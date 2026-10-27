from io import StringIO
from collections.abc import Callable

from langchain_core.messages import HumanMessage
from langgraph.graph.state import CompiledStateGraph
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.filters import Condition
from prompt_toolkit.history import FileHistory
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.utils import get_cwidth
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.layout import HSplit, Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Frame, Label, TextArea
from rich.console import Console
from rich.markdown import Markdown

from app.agents.supervisor_agent import SupervisorAgent


class ChatLexer(Lexer):
    """각 표시 행에 질문과 답변 라벨의 서식을 적용합니다."""

    def __init__(self) -> None:
        self.styles: list[str] = []

    def lex_document(self, document: Document) -> Callable[[int], StyleAndTextTuples]:
        """표시 행의 역할에 맞는 서식과 텍스트를 반환합니다."""

        def get_line(index: int) -> StyleAndTextTuples:
            style = self.styles[index] if index < len(self.styles) else ""
            return [(style, document.lines[index])]

        return get_line


class Chat:
    """하단 고정 입력창에서 질문을 받아 에이전트의 답변을 스트리밍합니다."""

    def __init__(self, supervisor: CompiledStateGraph) -> None:
        """에이전트, 대화 상태와 전체 화면 레이아웃을 설정합니다."""
        self.supervisor = supervisor
        self.config = {"configurable": {"thread_id": "session-1"}}
        self.busy = False
        self.messages: list[tuple[str, str]] = []
        self.lexer = ChatLexer()
        self.transcript = TextArea(
            text="안녕하세요, (주)길동상사 AI '길동이'입니다. 질문을 입력하세요.\n",
            read_only=True,
            scrollbar=True,
            lexer=self.lexer,
            wrap_lines=True,
        )
        self.input = TextArea(
            height=1,
            prompt="> ",
            multiline=False,
            wrap_lines=False,
            history=FileHistory(".my_history"),
            read_only=Condition(lambda: self.busy),
            accept_handler=self.submit,
        )
        bindings = KeyBindings()

        @bindings.add("c-c")
        @bindings.add("c-d")
        def exit_chat(event: KeyPressEvent) -> None:
            """진행 중인 답변을 중단하고 채팅 화면을 종료합니다."""
            event.app.exit()

        @bindings.add("escape")
        def focus_input(event: KeyPressEvent) -> None:
            """입력창으로 돌아갑니다."""
            event.app.layout.focus(self.input)

        @bindings.add("c-p")
        def focus_history(event: KeyPressEvent) -> None:
            """대화 영역으로 이동해 방향키로 이전 내용을 탐색합니다."""
            event.app.layout.focus(self.transcript)

        self.application: Application[None] = Application(
            layout=Layout(
                HSplit(
                    [
                        self.transcript,
                        Label(
                            lambda: " 답변 생성 중…" if self.busy else "",
                            style="class:hint",
                        ),
                        Frame(self.input),
                        Label(
                            " Enter 전송 · Ctrl+P 대화 탐색 · Esc 입력 · Ctrl+C 종료",
                            style="class:hint",
                        ),
                    ]
                ),
                focused_element=self.input,
            ),
            key_bindings=bindings,
            style=Style.from_dict(
                {
                    "frame.border": "#808080",
                    "frame.label": "#808080",
                    "hint": "#808080",
                    "question": "bg:#30343b #ffffff bold",
                    "assistant-label": "#5fd7d7 bold",
                }
            ),
            full_screen=True,
            mouse_support=True,
        )

    def redraw(self) -> None:
        """현재 터미널 너비에 맞춰 누적 대화와 Markdown 답변을 표시합니다."""
        width = max(10, self.application.output.get_size().columns - 2)
        lines: list[str] = []
        styles: list[str] = []
        for index, (role, content) in enumerate(self.messages):
            if lines:
                gap = 3 if role == "user" else 2
                lines.extend([""] * gap)
                styles.extend([""] * gap)
            if role == "user":
                for line in content.splitlines():
                    text = f"▌ > {line}"
                    lines.append(text + " " * max(0, width - get_cwidth(text)))
                    styles.append("class:question")
            else:
                label = "길동이"
                if self.busy and index == len(self.messages) - 1:
                    label += " · 답변 생성 중…"
                lines.extend([label, ""])
                styles.extend(["class:assistant-label", ""])
                output = StringIO()
                Console(file=output, width=width, color_system=None).print(
                    Markdown(content)
                )
                body = output.getvalue().rstrip().splitlines()
                lines.extend(body)
                styles.extend([""] * len(body))
        self.lexer.styles = styles
        text = "\n".join(lines) + "\n"
        cursor = (
            self.transcript.buffer.cursor_position
            if self.application.layout.has_focus(self.transcript)
            else len(text)
        )
        self.transcript.buffer.set_document(
            Document(text, cursor_position=min(cursor, len(text))), bypass_readonly=True
        )
        self.application.invalidate()

    def submit(self, buffer: Buffer) -> bool:
        """질문을 대화에 추가하고 비동기 답변 생성을 시작합니다."""
        message = buffer.text.strip()
        if message.lower() in {"exit", "quit"}:
            self.application.exit()
            return False
        if self.busy or not message:
            return False
        self.busy = True
        self.messages.extend([("user", message), ("assistant", "")])
        self.redraw()
        self.application.create_background_task(self.respond(message))
        return False

    async def respond(self, message: str) -> None:
        """상위 모델의 텍스트만 누적하여 Markdown 답변을 갱신합니다."""
        response = ""
        try:
            async for chunk, metadata in self.supervisor.astream(
                {"messages": [HumanMessage(message)]},
                config=self.config,
                stream_mode="messages",
            ):
                if (
                    metadata.get("langgraph_node") == "model"
                    and "supervisor_output" in metadata.get("tags", [])
                    and chunk.text
                ):
                    response += chunk.text
                    self.messages[-1] = ("assistant", response)
                    self.redraw()
            if not response:
                self.messages[-1] = ("assistant", "답변 내용을 확인할 수 없습니다.")
        except Exception:
            self.messages[-1] = (
                "assistant",
                response + "\n\n답변 생성에 실패했습니다. 다시 질문해 주세요.",
            )
        finally:
            self.busy = False
            self.redraw()

    def run(self) -> None:
        """채팅 화면을 실행하고 종료 시 남은 비동기 작업을 취소합니다."""
        self.application.run()


def main() -> None:
    """상위 에이전트를 생성하고 전체 화면 채팅을 실행합니다."""
    Chat(SupervisorAgent().get_agent()).run()


if __name__ == "__main__":
    main()

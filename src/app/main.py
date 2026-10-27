import base64
from types import NotImplementedType
from io import StringIO
from collections.abc import Callable
from langchain_core.messages import HumanMessage
from langgraph.graph.state import CompiledStateGraph
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.mouse_events import MouseEvent, MouseEventType
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
        self.scroll_lines = 3  # 휠 이벤트 한 번에 이동할 줄 수
        self.follow_output = True
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
            style="bg:#30343b #ffffff",
            multiline=False,
            wrap_lines=False,
            history=FileHistory(".my_history"),
            read_only=Condition(lambda: self.busy),
            accept_handler=self.submit,
        )
        # 입력창 위에서도 휠은 대화 영역만 스크롤합니다.
        for control in (self.transcript.control, self.input.control):
            original_handler = control.mouse_handler

            def mouse_handler(
                event: MouseEvent,
                handler: Callable[
                    [MouseEvent], None | NotImplementedType
                ] = original_handler,
                target: Buffer = control.buffer,
            ) -> None | NotImplementedType:
                if event.event_type in {
                    MouseEventType.SCROLL_UP,
                    MouseEventType.SCROLL_DOWN,
                }:
                    self.follow_output = False
                    for _ in range(self.scroll_lines):
                        self.transcript.window._mouse_handler(event)
                    return None
                if event.event_type == MouseEventType.MOUSE_DOWN:
                    self.follow_output = False
                # 기본 선택 핸들러를 처리하는 동안만 대상 버퍼를 활성화합니다.
                # 화면을 다시 그리기 전에 입력창으로 복귀해 커서 이동을 막습니다.
                self.application.layout.focus(target)
                try:
                    result = handler(event)
                finally:
                    self.application.layout.focus(self.input)
                if (
                    event.event_type == MouseEventType.MOUSE_UP
                    and target.selection_state
                ):
                    text = target.document.cut_selection()[1].text
                    if text:
                        self.application.clipboard.set_text(text)
                        encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
                        # OSC 52를 지원하는 터미널에 선택 내용을 클립보드로 전달합니다.
                        self.application.output.write_raw(f"\x1b]52;c;{encoded}\x07")
                        self.application.output.flush()
                return result

            control.mouse_handler = mouse_handler

        bindings = KeyBindings()

        @bindings.add("c-c")
        @bindings.add("c-d")
        def exit_chat(event: KeyPressEvent) -> None:
            """진행 중인 답변을 중단하고 채팅 화면을 종료합니다."""
            event.app.exit()

        @bindings.add("escape")
        def focus_input(event: KeyPressEvent) -> None:
            """대화 선택을 해제하고 입력창을 유지합니다."""
            self.transcript.buffer.exit_selection()
            self.follow_output = True
            event.app.layout.focus(self.input)
            self.redraw()

        self.application: Application[None] = Application(
            layout=Layout(
                HSplit(
                    [
                        self.transcript,
                        # Label(
                        #     lambda: " 답변 생성 중…" if self.busy else "",
                        #     style="class:hint",
                        # ),
                        Frame(self.input),
                        Label(
                            " Enter 전송 · 휠 스크롤 · ↑/↓ 입력 이력 · 드래그 복사 · Esc 선택 해제 · Ctrl+C 종료",
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
        if self.transcript.buffer.selection_state:
            return
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
                    text = f"▌ {line}"
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
            if not self.follow_output
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
        self.follow_output = True
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

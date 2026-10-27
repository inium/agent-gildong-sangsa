from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from rich.console import Console
from rich.markdown import Markdown
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from app.agents.supervisor_agent import SupervisorAgent


def answer(answer: str, references: list[tuple[str, str]] | None = None) -> None:
    """에이전트 답변 내용을 템플릿 내에 출력합니다."""

    console = Console()

    console.print()
    console.print("길동이> ")
    console.print(Markdown(answer))

    if references:
        console.print("\n검색된 참고 문서:")
        for source, page in references:
            console.print(f"- {source} · PDF 페이지: {page}", markup=False)

    console.print()


def main() -> None:
    """에이전트 메인 함수입니다."""

    supervisor = SupervisorAgent().get_agent()

    thread_id = "session-1"
    config = {"configurable": {"thread_id": thread_id}}

    session = PromptSession(history=FileHistory(".my_history"))

    print(
        "\n--------------------------------------------------\n"
        "안녕하세요, 저는 (주)길동상사 AI '길동이' 입니다. \n"
        "종료하려면 'exit' 또는 'quit'를 입력하세요.\n"
        "--------------------------------------------------\n"
    )

    while True:
        try:
            user_input = session.prompt("You> ").strip()
        except KeyboardInterrupt, EOFError:
            answer("종료합니다. 이용해 주셔서 감사합니다.")
            break

        if not user_input:
            continue

        command = user_input.lower()
        if command in {"exit", "quit"}:
            answer("종료합니다. 이용해 주셔서 감사합니다.")
            break

        result = supervisor.invoke(
            {"messages": [HumanMessage(user_input)]}, config=config
        )

        answer(
            result["messages"][-1].content,
            # references=collect_references(result["messages"]),
        )


if __name__ == "__main__":
    main()

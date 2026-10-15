import os
from pathlib import Path
from collections.abc import Sequence
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import WordCompleter
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.chat_models import init_chat_model
from agent.prompts import load_prompt
from agent.tools import all_tools


def collect_references(messages: Sequence[BaseMessage]) -> list[tuple[str, str]]:
    """현재 질문의 문서 출처와 1부터 시작하는 표시용 페이지를 수집합니다."""
    start = next(
        (
            index + 1
            for index in range(len(messages) - 1, -1, -1)
            if isinstance(messages[index], HumanMessage)
        ),
        0,
    )
    references = []
    for message in messages[start:]:
        if not isinstance(message, ToolMessage) or message.status == "error":
            continue
        if not isinstance(message.artifact, list):
            continue
        for document in message.artifact:
            if not isinstance(document, Document):
                continue
            source = Path(str(document.metadata.get("source") or "출처 정보 없음")).name
            page_index = document.metadata.get("page")
            page = (
                str(page_index + 1)
                if isinstance(page_index, int)
                and not isinstance(page_index, bool)
                and page_index >= 0
                else "페이지 정보 없음"
            )
            reference = (source, page)
            if reference not in references:
                references.append(reference)
    return references


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

    load_dotenv()  # Load environment variables from .env file
    model = init_chat_model(model=os.getenv("OPENAI_MODEL"), temperature=0)

    agent = create_agent(
        model=model,
        tools=all_tools(),
        system_prompt=load_prompt("system.md"),
        checkpointer=InMemorySaver(),
    )

    thread_id = "gildong-session-1"
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

        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]}, config=config
        )

        answer(
            result["messages"][-1].content,
            references=collect_references(result["messages"]),
        )


if __name__ == "__main__":
    main()

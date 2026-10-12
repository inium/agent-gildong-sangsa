import os
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import WordCompleter
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.chat_models import init_chat_model
from agent.tools import (
    CurrentTimeTool,
    HumanResourceTool,
    ShoppingMallCsTool,
)


def answer(answer: str) -> None:
    """에이전트 답변 내용을 템플릿 내에 출력합니다."""

    console = Console()

    console.print()
    console.print("길동이> ")
    console.print(Markdown(answer))
    console.print()


def main() -> None:
    """에이전트 메인 함수입니다."""

    load_dotenv()  # Load environment variables from .env file
    model = init_chat_model(model=os.getenv("OPENAI_MODEL"), temperature=0)

    SYSTEM_PROMPT = """
    당신의 이름은 '길동이' 이며, 지정된 도구로 확인할 수 있는 정보만 제공하는 에이전트입니다.

    규칙:
    - 사실 정보를 답하기 전에 관련 도구를 호출하세요.
    - 답변은 도구 실행 결과에 근거해야 합니다.
    - 요청을 처리할 도구가 없으면 추측하거나 사전 지식으로 답하지 마세요.
    - 도구가 오류를 반환하거나 필요한 정보를 제공하지 못하면 확인할 수 없다고 설명하세요.
    - 사용자가 도구의 지원 범위를 벗어난 요청을 하면 "현재 제공된 도구로는 해당 내용을 확인할 수 없습니다."라고 답하세요.
    - 도구 사용에 필요한 입력이 부족하면 사용자에게 추가 정보를 요청하세요.

    도구:
    - 시간 및 변환 도구는 get_current_time을 이용하세요.
    - 취업 규칙에 대한 검색은 gd_hr_rules_of_employment를 이용하세요.
    - 출장여비 규정에 대한 검색은 gd_hr_travel_expenses_of_employment를 이용하세요.
    - 복리후생 규정에 대한 검색은 gd_hr_welfare_of_employment를 이용하세요.
    - 쇼핑몰 CS에 대한 검색은 gd_mall_shopping_cs_manual를 이용하세요.
    """

    agent = create_agent(
        model=model,
        tools=[
            CurrentTimeTool().as_tool(),  # 현재 시간 및 변환 도구
            *HumanResourceTool().as_tools(),  # 취업규칙·복리후생·출장여비
            ShoppingMallCsTool().as_tool(),  # 쇼핑몰 CS 매뉴얼
        ],
        system_prompt=SYSTEM_PROMPT,
        # system_prompt = (
        #     "당신은 한국어로 친절하게 답변하는 도우미입니다. "
        #     "시간 확인이나 사내 문서 확인이 필요하면 제공된 도구를 사용하세요."
        # )
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

        answer(result["messages"][-1].content)


if __name__ == "__main__":
    main()

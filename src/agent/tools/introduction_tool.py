from collections.abc import Sequence

from langchain_core.tools import BaseTool, StructuredTool


class IntroductionTool:
    """길동이의 역할, 지원 기능과 사용 방법을 안내합니다."""

    def __init__(self, tools: Sequence[BaseTool]) -> None:
        """에이전트에 등록할 도구 목록을 보관합니다.

        Args:
            tools: 지원 기능 안내에 사용할 도구 목록입니다.
                실행하지 않고 각 도구의 이름과 설명만 읽습니다. 전달된 목록을
                참조하므로 목록의 추가·삭제는 이후 소개 호출에도 반영됩니다.
        """
        self._tools = tools

    def introduce(self) -> str:
        """등록된 도구의 이름과 설명에서 지원 기능 안내를 생성합니다."""
        capabilities = "\n".join(
            f"- {tool.name}: {' '.join(tool.description.split())}"
            for tool in self._tools
            if tool.name != "introduce_gildong"
        )
        return (
            "길동이는 가상의 회사 (주)길동상사의 콘솔 AI 도우미입니다.\n"
            "지원 기능:\n"
            f"{capabilities or '현재 등록된 기능 도구가 없습니다.'}\n"
            "사용 방법: 터미널에서 자연어로 질문하세요. "
            "답변은 도구 결과와 검색된 문서에 근거하며, "
            "근거가 부족하면 확인할 수 없다고 안내합니다.\n"
            "각 기능의 처리 범위와 제한 사항은 해당 도구 설명을 따릅니다.\n"
            "종료하려면 exit 또는 quit를 입력하세요."
        )

    def as_tool(self) -> StructuredTool:
        """입력 인자 없이 호출하는 길동이 소개 도구를 생성합니다."""
        return StructuredTool.from_function(
            func=self.introduce,
            name="introduce_gildong",
            description=(
                "길동이의 이름, 역할, 지원 기능, 사용 방법과 제한 사항을 안내합니다. "
                "'너는 누구야?', '길동이는 무엇을 할 수 있어?', '사용 방법을 알려줘' "
                "같은 자기소개·기능 안내 질문에 사용하세요. "
                "현재 시간이나 사내 규정의 실제 내용은 해당 분야 도구로 확인하세요."
            ),
        )

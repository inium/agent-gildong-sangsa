from langchain_core.prompts import PromptTemplate
from langchain_core.tools import StructuredTool, create_retriever_tool
from agent.config.vector_store import get_vector_store
from langchain_core.tools import tool


def gd_hr_rules_of_employment() -> StructuredTool:
    """길동상사 취업규칙을 검색하는 에이전트용 Retriever 도구를 생성합니다.

    rules_of_employment 컬렉션에 연결된 벡터 저장소에서 유사도 검색으로
    관련 문서 청크를 최대 4개 조회하도록 설정합니다. 검색된 각 청크는
    출처와 본문을 포함한 <document> 형식으로 에이전트에 전달합니다.
    문서에는 source 메타데이터가 있어야 합니다.

    Returns:
        StructuredTool: 검색어를 입력받아 취업규칙의 관련 문서를 반환하는 도구입니다.
            최종 답변 생성은 이 도구를 호출한 에이전트가 수행합니다.
    """

    # Vector Store
    vector_store = get_vector_store(collection="rules_of_employment")

    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4},  # 상위 4개 문서 검색
    )

    # 검색된 각 문서를 어떤 형식으로 보여줄지 지정
    # {page_content}: 문서 본문 / {source}: 문서의 metadata["source"] 값
    # 검색된 문서에 source 메타데이터가 없으면 현재 템플릿은 오류가 발생할 수 있음
    DOCUMENT_PROMPT = PromptTemplate.from_template(
        "<document>\n" "출처: {source}\n" "내용:\n{page_content}\n" "</document>"
    )

    # 에이전트에게 도구의 용도와 호출 조건을 설명
    DESCRIPTION = """
    길동상사의 취업규칙 문서에서 질문과 관련된 내용을 검색합니다.
    - 근로시간, 출퇴근, 휴일·휴가·연차, 복무, 인사 및 징계 등 취업규칙에 관한 질문에는 이 도구를 사용하세요.
    - 검색어에는 확인할 사항과 사용자가 제공한 조건을 구체적으로 포함하세요.
    - 관련 문서 청크를 최대 4개까지 출처와 함께 반환하며, 최종 답변이나 법률 해석을 생성하는 도구는 아닙니다.
    - 반환된 문서에 근거가 있을 때만 답하고 출처를 제시하세요.
    - 근거가 부족하면 해당 내용을 확인할 수 없다고 안내하세요.
    """

    return create_retriever_tool(
        retriever,
        name="gd_hr_rules_of_employment",
        description=DESCRIPTION,
        document_prompt=DOCUMENT_PROMPT,
        # document_separator="\n\n---\n\n",
    )

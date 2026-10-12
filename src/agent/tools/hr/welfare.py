from langchain_core.prompts import PromptTemplate
from langchain_core.tools import StructuredTool, create_retriever_tool
from agent.config.vector_store import get_vector_store


def gd_hr_welfare_of_employment() -> StructuredTool:
    """길동상사 복리후생 규정을 검색하는 에이전트용 Retriever 도구를 생성합니다.

    welfare_of_employment 컬렉션에 연결된 벡터 저장소에서 유사도 검색으로
    관련 문서 청크를 최대 4개 조회하도록 설정합니다. 검색된 각 청크는
    출처와 본문을 포함한 <document> 형식으로 에이전트에 전달합니다.
    문서에는 source 메타데이터가 있어야 합니다.

    Returns:
        StructuredTool: 검색어를 입력받아 복리후생 규정의 관련 문서를 반환하는 도구입니다.
            최종 답변 생성은 이 도구를 호출한 에이전트가 수행합니다.
    """

    # Vector Store
    vector_store = get_vector_store(collection="welfare_of_employment")

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
    길동상사의 복리후생 규정에서 질문과 관련된 내용을 검색합니다.
    - 직원 복지 혜택, 지원 대상, 지원 금액, 신청 및 지급 절차에 관한 질문에는 이 도구를 사용하세요.
    - 검색어에는 확인할 혜택과 사용자가 제공한 조건을 구체적으로 포함하세요.
    - 관련 문서 청크를 최대 4개까지 출처와 함께 반환합니다. 최종 답변 생성은 에이전트가 수행합니다.
    - 반환된 문서에 근거해 지원 대상, 자격 조건, 지원 금액·한도, 신청 방법, 필요 서류 및 예외를 구분하고 출처를 제시하세요.
    - 지원 여부 판단이나 금액 계산에 필요한 정보가 부족하면 추가로 질문하세요.
    - 문서에 없는 혜택이나 지원 금액을 추측하거나 지급을 약속하지 마세요. 근거가 부족하면 확인할 수 없다고 안내하세요.
    """

    return create_retriever_tool(
        retriever,
        name="gd_hr_welfare_of_employment",
        description=DESCRIPTION,
        document_prompt=DOCUMENT_PROMPT,
        # document_separator="\n\n---\n\n",
    )

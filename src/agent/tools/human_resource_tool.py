from langchain_core.prompts import PromptTemplate
from langchain_core.tools import StructuredTool, create_retriever_tool
from langchain_core.retrievers import BaseRetriever
from agent.store.source_retriever import SourceRetriever
from agent.store.pg_vector_store import PgVectorStore


class HumanResourceTool(PgVectorStore):
    """취업규칙, 복리후생, 출장여비의 검색 도구를 제공합니다."""

    def as_tools(self) -> list[StructuredTool]:
        """에이전트에 등록할 세 개의 인사 검색 도구를 반환합니다."""
        return [
            self.__rules_of_employment(),
            self.__welfare_of_employment(),
            self.__travel_expenses_of_employment(),
        ]

    def __create_tool(
        self, collection: str, name: str, description: str, k: int = 4
    ) -> StructuredTool:
        """지정한 인사 문서 컬렉션의 Retriever를 에이전트용 도구로 변환합니다.

        유사도 검색으로 관련 청크를 최대 k개 조회하고, 각 청크의 출처와
        본문을 <document> 형식으로 전달합니다. 검색 문서에는 source
        메타데이터가 필요하며, 최종 답변은 호출한 에이전트가 생성합니다.

        Args:
            collection (str): 검색할 PGVector 컬렉션 이름입니다.
            name (str): 에이전트에 노출할 고유한 도구 이름입니다.
            description (str): 도구의 검색 대상, 호출 조건과 결과 사용 규칙입니다.
                에이전트가 사용할 도구를 선택할 때 참고합니다.
            k (int): 반환할 최대 문서 청크 수입니다. 기본값은 4입니다.
                양의 정수를 지정하세요.

        Returns:
            StructuredTool: query를 입력받아 출처와 본문을 반환하는 검색 도구입니다.
        """

        retriever = self.__get_retriever(collection=collection, k=k)

        # 검색된 각 문서를 어떤 형식으로 보여줄지 지정
        # {page_content}: 문서 본문 / {source}: 문서의 metadata["source"] 값
        # 누락된 출처와 페이지 정보는 SourceRetriever에서 보정합니다.
        DOCUMENT_PROMPT = PromptTemplate.from_template(
            "<document>\n"
            "출처: {source}\n"
            "PDF 페이지: {page_number}\n"
            "내용:\n{page_content}\n"
            "</document>"
        )

        return create_retriever_tool(
            retriever=retriever,
            name=name,
            description=description,
            document_prompt=DOCUMENT_PROMPT,
            response_format="content_and_artifact",
        )

    def __rules_of_employment(self) -> StructuredTool:
        """길동상사의 취업규칙을 검색하는 에이전트용 도구를 생성합니다.

        rules_of_employment 컬렉션에서 근로시간, 출퇴근, 휴일·휴가·연차,
        복무, 인사 및 징계 관련 내용을 유사도 검색합니다. 관련 문서 청크를
        최대 4개까지 출처와 본문이 포함된 형식으로 반환하도록 설정합니다.
        검색 문서의 누락된 출처와 페이지는 확인 불가 안내로 표시합니다.

        Returns:
            StructuredTool: gd_hr_rules_of_employment 이름으로 등록되는
                검색 도구입니다. query를 입력받으며, 최종 답변 생성과
                검색 결과의 근거 확인은 호출한 에이전트가 수행합니다.
        """

        # 에이전트에게 도구의 용도와 호출 조건을 설명
        DESCRIPTION = """
        길동상사의 취업규칙 문서에서 질문과 관련된 내용을 검색합니다.

        - 근로시간, 출퇴근, 휴일·휴가·연차, 복무, 인사 및 징계 등 취업규칙에 관한 질문에는 이 도구를 사용하세요.
        - 검색어에는 확인할 사항과 사용자가 제공한 조건을 구체적으로 포함하세요.
        - 관련 문서 청크를 최대 4개까지 출처와 함께 반환하며, 최종 답변이나 법률 해석을 생성하는 도구는 아닙니다.
        - 반환된 문서에 근거가 있을 때만 답하고 출처를 제시하세요.
        - 근거가 부족하면 해당 내용을 확인할 수 없다고 안내하세요.
        """

        return self.__create_tool(
            collection="rules_of_employment",
            name="gd_hr_rules_of_employment",
            description=DESCRIPTION,
        )

    def __welfare_of_employment(self) -> StructuredTool:
        """길동상사의 복리후생 규정을 검색하는 에이전트용 도구를 생성합니다.

        welfare_of_employment 컬렉션에서 직원 복지 혜택, 지원 대상·금액,
        신청 및 지급 절차와 관련된 내용을 유사도 검색합니다. 관련 문서 청크를
        최대 4개까지 출처와 본문이 포함된 형식으로 반환하도록 설정합니다.
        검색 문서의 누락된 출처와 페이지는 확인 불가 안내로 표시합니다.

        Returns:
            StructuredTool: gd_hr_welfare_of_employment 이름으로 등록되는
                검색 도구입니다. query를 입력받으며, 지원 조건과 예외의
                확인 및 최종 답변 생성은 호출한 에이전트가 수행합니다.
        """

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

        return self.__create_tool(
            collection="welfare_of_employment",
            name="gd_hr_welfare_of_employment",
            description=DESCRIPTION,
        )

    def __travel_expenses_of_employment(self) -> StructuredTool:
        """길동상사의 출장여비 규정을 검색하는 에이전트용 도구를 생성합니다.

        travel_expenses_of_employment 컬렉션에서 교통비, 숙박비, 식비,
        일비의 지급 기준과 정산 절차를 유사도 검색합니다. 관련 문서 청크를
        최대 4개까지 출처와 본문이 포함된 형식으로 반환하도록 설정합니다.
        검색 문서의 누락된 출처와 페이지는 확인 불가 안내로 표시합니다.

        Returns:
            StructuredTool: gd_hr_travel_expenses_of_employment 이름으로
                등록되는 검색 도구입니다. query를 입력받으며, 지급 조건·한도·
                증빙 요건 확인과 최종 답변 생성은 호출한 에이전트가 수행합니다.
        """

        # 에이전트에게 도구의 용도와 호출 조건을 설명
        DESCRIPTION = """
        길동상사의 출장여비 규정에서 질문과 관련된 내용을 검색합니다.

        - 출장 시 교통비, 숙박비, 식비, 일비의 지급 기준과 비용 정산 절차에 관한 질문에는 이 도구를 사용하세요.
        - 검색어에는 확인할 비용 항목과 사용자가 제공한 출장 조건을 구체적으로 포함하세요.
        - 관련 문서 청크를 최대 4개까지 출처와 함께 반환합니다. 최종 답변 생성은 에이전트가 수행합니다.
        - 반환된 문서에 근거해 적용 대상, 지급 조건, 한도, 예외 및 증빙 요건을 구분하고 출처를 제시하세요.
        - 금액 계산에는 문서에 명시된 기준만 사용하고, 필요한 정보가 부족하면 추가로 질문하세요.
        - 검색 결과에 근거가 없는 지급 금액이나 정산 절차를 추측하지 말고 확인할 수 없다고 안내하세요.
        """

        return self.__create_tool(
            collection="travel_expenses_of_employment",
            name="gd_hr_travel_expenses_of_employment",
            description=DESCRIPTION,
        )

    def __get_retriever(self, collection: str, k: int = 4) -> BaseRetriever:
        """쇼핑몰 CS 매뉴얼의 관련 문서를 검색하는 Retriever를 생성합니다.

        shopping_cs_manual 컬렉션에 연결된 벡터 저장소를 사용하며,
        유사도 검색으로 검색어와 관련된 문서 청크를 최대 k개 조회합니다.

        Args:
            collection (str): 검색할 PGVector 컬렉션 이름입니다.
                예: "shopping_cs_manual". 현재 구현에서는 이 인자 대신
                self.collection 값을 사용합니다.
            k (int): 검색 결과로 반환할 최대 문서 청크 수입니다.
                기본값은 4이며, 양의 정수를 지정하세요.

        Returns:
            BaseRetriever: invoke(query)로 관련 문서 목록을 조회할 수
                있는 Retriever입니다. 답변 생성이나 결과 포맷팅은 수행하지 않습니다.
        """
        # Vector Store
        vector_store = self._get_vector_store(collection=collection)

        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k},  # 상위 k개 문서 검색
        )

        return SourceRetriever(retriever=retriever)

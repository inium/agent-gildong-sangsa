from langchain_core.prompts import PromptTemplate
from langchain_core.tools import StructuredTool, create_retriever_tool
from langchain_core.vectorstores import VectorStoreRetriever
from agent.store.pg_vector_store import PgVectorStore


class ShoppingMallCsTool(PgVectorStore):
    """쇼핑몰 CS 매뉴얼 검색 도구를 제공합니다."""

    # RAG collection
    collection: str = "shopping_cs_manual"

    # Agent Tool Name
    tool_name: str = "gd_mall_shopping_cs_manual"

    def as_tool(self) -> StructuredTool:
        """길동상사 쇼핑몰 CS 매뉴얼을 검색하는 에이전트용 Retriever 도구를 생성합니다.

        shopping_cs_manual 컬렉션에 연결된 벡터 저장소에서 유사도 검색으로
        관련 문서 청크를 최대 4개 조회하도록 설정합니다. 검색된 각 청크는
        출처와 본문을 포함한 <document> 형식으로 에이전트에 전달합니다.
        문서에는 source 메타데이터가 있어야 합니다.

        Returns:
            StructuredTool: 검색어를 입력받아 쇼핑몰 CS 매뉴얼의 관련 문서를 반환하는 도구입니다.
                최종 답변 생성은 이 도구를 호출한 에이전트가 수행합니다.
        """

        # 검색된 각 문서를 어떤 형식으로 보여줄지 지정
        # {page_content}: 문서 본문 / {source}: 문서의 metadata["source"] 값
        # 검색된 문서에 source 메타데이터가 없으면 현재 템플릿은 오류가 발생할 수 있음
        DOCUMENT_PROMPT = PromptTemplate.from_template(
            "<document>\n" "출처: {source}\n" "내용:\n{page_content}\n" "</document>"
        )

        # 에이전트에게 도구의 용도와 호출 조건을 설명
        DESCRIPTION = """
        길동상사의 쇼핑몰 CS 실무 매뉴얼에서 질문과 관련된 내용을 검색합니다.

        - 주문, 결제, 배송, 취소, 교환, 반품, 환불 및 고객 불만 응대 절차에 관한 질문에는 이 도구를 사용하세요.
        - 검색어에는 문의 유형과 사용자가 제공한 주문·배송 상태 등 필요한 조건을 구체적으로 포함하세요.
        - 관련 문서 청크를 최대 4개까지 출처와 함께 반환합니다. 최종 답변 생성은 에이전트가 수행합니다.
        - 반환된 문서에 근거해 처리 조건, 절차, 기한, 비용 부담 및 예외를 구분하고 출처를 제시하세요.
        - 내부 처리 절차와 고객에게 안내할 문구를 구분하세요. 처리에 필요한 정보가 부족하면 추가로 질문하세요.
        - 이 도구는 문서 검색만 수행하며 실제 주문 조회, 취소, 환불을 처리하지 않습니다. 처리가 완료되었다고 안내하지 마세요.
        - 문서에 없는 환불, 보상 또는 처리 기한을 약속하지 마세요. 근거가 부족하면 확인할 수 없다고 안내하세요.
        """

        return create_retriever_tool(
            retriever=self.__get_retriever(collection=self.collection, k=self.k),
            name=self.tool_name,
            description=DESCRIPTION,
            document_prompt=DOCUMENT_PROMPT,
        )

    def __get_retriever(self, collection: str, k: int = 4) -> VectorStoreRetriever:
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
            VectorStoreRetriever: invoke(query)로 관련 문서 목록을 조회할 수
                있는 Retriever입니다. 답변 생성이나 결과 포맷팅은 수행하지 않습니다.
        """
        # Vector Store
        vector_store = self._get_vector_store(collection=collection)

        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k},  # 상위 k개 문서 검색
        )

        return retriever

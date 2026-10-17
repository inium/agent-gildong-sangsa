from langchain_core.prompts import PromptTemplate
from langchain_core.tools import StructuredTool, create_retriever_tool
from langchain_core.vectorstores import VectorStoreRetriever
from agent.prompts import load_prompt
from agent.store.pg_vector_store import PgVectorStore


class CsTool(PgVectorStore):
    """쇼핑몰 CS 매뉴얼 검색 도구를 제공합니다."""

    def __init__(self) -> None:
        """검색도구 설정에 필요한 변수값을 설정합니다."""

        # Agent Tool Name
        self.tool_name = "gd_mall_cs"

        # 에이전트에게 도구의 용도, 호출 조건 설명
        self.tool_description = load_prompt("mall/cs_description.md")

        # RAG collection
        self.vector_collection = "mall_cs"

        # 검색 유형. similarity, mmr 중 1
        self.vector_search_type = "similarity"

        # 검색 파라미터
        self.vector_search_kwags = {"k": 4}

        super().__init__()

    def as_tool(self) -> StructuredTool:
        """길동상사 쇼핑몰 CS 매뉴얼을 검색하는 에이전트용 Retriever 도구를 생성합니다.

        Returns:
            StructuredTool: 검색어를 입력받아 쇼핑몰 CS 매뉴얼의 관련 문서를 반환하는 도구입니다.
                최종 답변 생성은 이 도구를 호출한 에이전트가 수행합니다.
        """

        return create_retriever_tool(
            retriever=self.__get_retriever(),
            name=self.tool_name,
            description=self.tool_description,
            document_prompt=self.__get_document_prompt(),
            response_format="content_and_artifact",
        )

    def __get_document_prompt(self) -> PromptTemplate:
        """검색 문서의 출처·페이지·본문을 표시할 PromptTemplate을 반환합니다.

        검색된 각 문서를 어떤 형식으로 보여줄지 지정합니다.
        검색 문서에는 source와 메타데이터가 필요하며,
        page는 0부터 시작하는 PDF 페이지 인덱스입니다.

        Returns:
            PromptTemplate: {source}, {page}, {page_content} 변수를 포함한 문서 템플릿입니다.
        """

        return PromptTemplate.from_template("""
            <document>
                출처: {source}
                PDF 페이지: {page}
                내용: {page_content}
            </document>
        """)

    def __get_retriever(self) -> VectorStoreRetriever:
        """검색 Retriever를 생성합니다.

        Returns:
            VectorStoreRetriever: invoke(query)로 관련 문서 목록을 조회할 수
                있는 Retriever입니다. 답변 생성이나 결과 포맷팅은 수행하지 않습니다.
        """

        vector_store = self._get_vector_store(collection=self.vector_collection)

        return vector_store.as_retriever(
            search_type=self.vector_search_type,
            search_kwargs=self.vector_search_kwags,
        )

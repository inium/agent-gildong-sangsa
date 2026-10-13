from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever


class SourceRetriever(BaseRetriever):
    """검색 결과의 누락된 출처와 PDF 페이지 정보를 보정합니다."""

    retriever: BaseRetriever

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[Document]:
        """하위 Retriever로 문서를 검색하고 누락된 출처·페이지 정보를 보정합니다.

        source가 없거나 비어 있으면 "출처 정보 없음"으로 표시합니다.
        page_number가 없으면 0부터 시작하는 page에 1을 더해 계산하며,
        유효한 page도 없으면 "페이지 정보 없음"으로 표시합니다.
        원본 문서를 변경하지 않고 메타데이터를 보정한 복사본을 반환합니다.

        Args:
            query (str): 하위 Retriever에 전달할 검색어입니다.
            run_manager (CallbackManagerForRetrieverRun): 검색 실행의 콜백
                관리자입니다. 하위 검색에 자식 콜백을 전달합니다.

        Returns:
            list[Document]: 출처와 PDF 페이지 정보가 보정된 검색 문서 목록입니다.
                검색 결과가 없으면 빈 목록을 반환합니다.
        """
        documents = self.retriever.invoke(
            query, config={"callbacks": run_manager.get_child()}
        )

        results = []
        for document in documents:
            metadata = dict(document.metadata)
            if not str(metadata.get("source") or "").strip():
                metadata["source"] = "출처 정보 없음"

            if not str(metadata.get("page_number") or "").strip():
                page = metadata.get("page")
                metadata["page_number"] = (
                    page + 1
                    if isinstance(page, int)
                    and not isinstance(page, bool)
                    and page >= 0
                    else "페이지 정보 없음"
                )

            results.append(document.model_copy(update={"metadata": metadata}))

        return results

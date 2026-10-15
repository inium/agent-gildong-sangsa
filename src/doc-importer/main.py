import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from sqlalchemy.engine import URL
from langchain_core.documents import Document
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_pymupdf4llm import PyMuPDF4LLMLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

"""길동상사의 PDF 문서를 임베딩해 PostgreSQL 벡터 저장소에 적재하는 스크립트입니다.

처리 과정:
1. .env와 환경 변수의 PG_* 설정으로 PostgreSQL 연결 URL을 생성합니다.
2. 취업규칙, 복리후생 규정, 출장여비 규정, 쇼핑몰 CS 매뉴얼의 파일 경로와
   저장할 컬렉션 이름을 지정합니다. 상대 경로는 이 파일의 디렉터리를 기준으로 합니다.
3. PyMuPDF4LLMLoader로 각 PDF의 내용을 읽고, tiktoken 인코딩을 기준으로
   최대 1000토큰, 겹침 200토큰의 청크로 분할합니다.
4. OpenAIEmbeddings로 청크 텍스트의 임베딩을 생성하고, PGVector를 통해
   문서와 메타데이터를 파일별 컬렉션에 저장합니다. 메타데이터는 JSONB를 사용합니다.
5. 파일별 처리 순번과 전체 완료 메시지를 출력합니다.

직접 실행하면 main()이 호출됩니다. 실행에는 PDF 파일, OpenAI API 인증 정보와
pgvector를 사용할 수 있는 PostgreSQL 데이터베이스가 필요합니다.
"""


def pg_connection_str() -> str:
    """.env와 환경 변수에서 PostgreSQL 접속 정보를 읽어 연결 URL을 반환합니다.

    사용하는 환경 변수는 PG_HOST, PG_PORT, PG_DATABASE, PG_USERNAME,
    PG_PASSWORD입니다. 이미 설정된 환경 변수는 .env 값보다 우선합니다.

    Returns:
        str: psycopg 드라이버를 사용하는 SQLAlchemy 형식의 PostgreSQL 연결
            URL입니다. 비밀번호가 포함되므로 로그에 출력하지 마세요.
    """
    load_dotenv()

    connection_url = URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("PG_USERNAME"),
        password=os.getenv("PG_PASSWORD"),
        host=os.getenv("PG_HOST"),
        port=os.getenv("PG_PORT"),
        database=os.getenv("PG_DATABASE"),
    )
    return connection_url.render_as_string(hide_password=False)


def pdf_text_splitter(
    path: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    encoding_name="cl100k_base",
) -> list[Document]:
    """PDF 파일을 로드한 후 문서를 청크(chunk)로 나눕니다.

    Args:
        path (str): 로드할 PDF 파일의 경로입니다.
        chunk_size (int): 청크의 최대 토큰 수입니다. 기본값은 1000입니다.
        chunk_overlap (int): 인접한 청크 사이에 겹치도록 유지할 토큰 수입니다.
            문맥을 이어 주기 위한 설정으로, 기본값은 200입니다.
            0 이상이며 chunk_size 이하여야 합니다.
        encoding_name (str): 청크 분할 시 토큰 수를 계산할 tiktoken 인코딩
            이름입니다. 기본값은 "cl100k_base"입니다. 사용하는 모델에 맞는
            인코딩을 지정하며, PDF 파일의 문자 인코딩과는 별개입니다.

    Returns:
        list[Document]: 청크로 분할한 문서 목록입니다. 각 문서는 청크 텍스트를
            담은 page_content와 원본 문서에서 전달된 metadata를 포함합니다.
    """
    loader = PyMuPDF4LLMLoader(path, mode="page")

    data = loader.load()
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        encoding_name=encoding_name,
    )

    documents = text_splitter.split_documents(data)

    for document in documents:
        source = document.metadata.get("source")
        if source is None or not str(source).strip():
            document.metadata["source"] = Path(path).name

    return documents


def add_document_to_vector_store(
    documents: list[Document],
    collection_name: str,
    connection: str,
    name: str,
    description: str,
) -> None:
    """문서를 OpenAI 임베딩으로 변환해 PostgreSQL 벡터 저장소에 추가합니다.

    Args:
        documents (list[Document]): 저장할 문서 목록입니다. 각 문서의
            page_content를 임베딩하고 metadata와 함께 지정한 컬렉션에 저장합니다.
        collection_name (str): 문서를 저장할 PGVector 컬렉션 이름입니다.
            예: "company_docs".
        connection (str): PostgreSQL 접속에 사용할 SQLAlchemy 연결 URL입니다.
            pg_connection_str()의 반환값을 전달할 수 있습니다.
            비밀번호가 포함될 수 있으므로 로그에 출력하지 마세요.
        name (str): 사용자에게 표시할 컬렉션 이름입니다.
        description (str): 컬렉션의 문서 범위와 용도에 대한 설명입니다.

    문서 저장 성공 후 컬렉션 메타데이터를 갱신합니다. 기존 created_at은
    유지하며, 값이 없으면 최초 기록 시각을 사용합니다. 문서 저장과
    메타데이터 갱신은 별도 트랜잭션입니다.

    Returns:
        None: 문서 저장을 수행하며 별도의 값을 반환하지 않습니다.
    """
    embeddings = OpenAIEmbeddings()
    for document in documents:
        document.metadata.update(
            {
                "embedding_model": embeddings.model,
            }
        )

    now = datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")

    vector_store = PGVector(
        embeddings=embeddings,
        connection=connection,
        collection_name=collection_name,
        collection_metadata={
            "name": name,
            "description": description,
            "created_at": now,
            "updated_at": now,
        },
        use_jsonb=True,
    )

    vector_store.add_documents(documents)


def main():
    connection_str = pg_connection_str()

    files = [
        {
            "path": "../../resources/취업규칙 - (주)길동상사.pdf",
            "collection_name": "hr_rules_of_employment",
            "name": "취업규칙",
            "description": "길동상사의 근로시간, 휴가, 복무 및 인사 규정",
        },
        {
            "path": "../../resources/복리후생 규정 - (주)길동상사.pdf",
            "collection_name": "hr_welfare_of_employment",
            "name": "복리후생 규정",
            "description": "직원 복지 혜택, 지원 조건 및 신청 절차",
        },
        {
            "path": "../../resources/출장여비 규정 - (주)길동상사.pdf",
            "collection_name": "hr_travel_of_employment",
            "name": "출장여비 규정",
            "description": "출장 비용 지급 기준 및 정산 절차",
        },
        {
            "path": "../../resources/쇼핑몰 CS 실무 매뉴얼 - (주)길동상사.pdf",
            "collection_name": "mall_cs",
            "name": "쇼핑몰 CS 매뉴얼",
            "description": "주문, 배송, 교환, 반품 및 고객응대 절차",
        },
    ]

    for index, file in enumerate(files, start=1):
        # 상대 경로는 실행 위치가 아닌 이 스크립트의 디렉터리를 기준으로 해석합니다.
        path = (Path(__file__).resolve().parent / file["path"]).resolve()
        documents = pdf_text_splitter(str(path))
        add_document_to_vector_store(
            documents,
            collection_name=file["collection_name"],
            connection=connection_str,
            name=file["name"],
            description=file["description"],
        )

        print(f"{index} of {len(files)} 완료")

    print("\n모든 문서가 import 완료되었습니다.")


if __name__ == "__main__":
    main()

import os
from dotenv import load_dotenv
from sqlalchemy.engine import URL
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector


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


def get_vector_store(
    collection: str,
    connection: str = pg_connection_str(),
    embeddings=OpenAIEmbeddings(),
) -> PGVector:
    """지정한 컬렉션에 연결된 PostgreSQL 벡터 저장소를 생성합니다.

    Args:
        collection (str): 문서를 저장하거나 검색할 PGVector 컬렉션 이름입니다.
        connection (str): SQLAlchemy 형식의 PostgreSQL 연결 URL입니다.
            기본값은 pg_connection_str()으로 생성한 URL입니다.
        embeddings: 문서와 검색어를 벡터로 변환할 임베딩 객체입니다.
            기본값은 OpenAIEmbeddings()입니다.

    Returns:
        PGVector: 문서 저장, 유사도 검색 및 Retriever 생성에 사용할
            벡터 저장소입니다. 메타데이터는 JSONB 형식으로 저장합니다.
    """
    vector_store = PGVector(
        embeddings=embeddings,
        connection=connection,
        collection_name=collection,
        use_jsonb=True,
    )

    return vector_store

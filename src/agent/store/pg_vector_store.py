import os

from dotenv import load_dotenv
from sqlalchemy.engine import URL
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector


class PgVectorStore:
    """PostgreSQL 연결 설정과 컬렉션별 벡터 저장소 생성을 제공합니다."""

    def __init__(self) -> None:
        """연결 URL과 임베딩 객체를 설정합니다.

        생략하면 환경 변수로 연결 URL을 생성하고 OpenAIEmbeddings를 사용합니다.
        """
        self.__connection = self.__pg_connection_str()
        self.__embeddings = OpenAIEmbeddings()

    @staticmethod
    def __pg_connection_str() -> str:
        """.env와 PG_* 환경 변수로 psycopg 연결 URL을 생성합니다.

        Returns:
            str: 비밀번호를 포함한 SQLAlchemy URL입니다. 로그에 출력하지 마세요.
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

    def _get_vector_store(self, collection: str) -> PGVector:
        """지정한 컬렉션에 연결된 벡터 저장소를 생성합니다.

        Args:
            collection (str): 문서를 저장하거나 검색할 컬렉션 이름입니다.

        Returns:
            PGVector: JSONB 메타데이터를 사용하는 벡터 저장소입니다.
        """
        return PGVector(
            embeddings=self.__embeddings,
            connection=self.__connection,
            collection_name=collection,
            use_jsonb=True,
        )

from pathlib import Path
from app.rag.loaders.pdf_text_splitter import PdfTextSplitter
from app.rag.vector_store.document_importer import DocumentImporter


def main():
    files = [
        {
            "path": "../../resources/취업규칙 - (주)길동상사.pdf",
            "table_name": "gd_hr_rules_of_employment",
        },
        {
            "path": "../../resources/복리후생 규정 - (주)길동상사.pdf",
            "table_name": "gd_hr_welfare_of_employment",
        },
        {
            "path": "../../resources/출장여비 규정 - (주)길동상사.pdf",
            "table_name": "gd_hr_travel_of_employment",
        },
        {
            "path": "../../resources/쇼핑몰 CS 실무 매뉴얼 - (주)길동상사.pdf",
            "table_name": "gd_mall_cs",
        },
    ]

    for index, file in enumerate(files, start=1):
        # 상대 경로는 실행 위치가 아닌 이 스크립트의 디렉터리를 기준으로 해석합니다.
        path = (Path(__file__).resolve().parent / file["path"]).resolve()
        documents = PdfTextSplitter.split(str(path))

        DocumentImporter.open(table_name=file["table_name"]).add_documents(documents)

        print(f"{index} of {len(files)} 완료")

    print("\n모든 문서가 import 완료되었습니다.")


if __name__ == "__main__":
    main()

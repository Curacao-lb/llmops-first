from pathlib import Path

import dotenv
from langchain_core.documents import Document

try:
    from study.not_spliter_document_transformer.doctran_compat import (
        DoctranTextTranslator,
    )
except ModuleNotFoundError:
    from doctran_compat import DoctranTextTranslator


dotenv.load_dotenv()


def main() -> None:
    source_path = Path(__file__).with_name("english.txt")
    page_content = source_path.read_text(encoding="utf-8").strip()

    documents = [
        Document(
            page_content=page_content,
            metadata={"source": str(source_path.name)},
        )
    ]

    translator = DoctranTextTranslator(
        language="chinese",
        openai_api_model="gpt-3.5-turbo-16k",
    )
    translated_documents = translator.transform_documents(documents)

    print("source:", translated_documents[0].metadata.get("source"))
    print()
    print("translated text:")
    print(translated_documents[0].page_content)


if __name__ == "__main__":
    main()

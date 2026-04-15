from __future__ import annotations

import copy
import json
import os
import uuid
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class ExtractProperty(BaseModel):
    name: str
    description: str
    type: Literal["string", "number", "boolean", "array", "object"]
    items: Optional[Union[List[Any], Dict[str, Any]]] = None
    enum: Optional[List[str]] = None
    required: bool = True


class ContentType(str, Enum):
    text = "text"
    html = "html"
    pdf = "pdf"
    mbox = "mbox"


class RecognizerEntity(str, Enum):
    CREDIT_CARD = "CREDIT_CARD"
    CRYPTO = "CRYPTO"
    DATE_TIME = "DATE_TIME"
    EMAIL_ADDRESS = "EMAIL_ADDRESS"
    IBAN_CODE = "IBAN_CODE"
    IP_ADDRESS = "IP_ADDRESS"
    NRP = "NRP"
    PHONE_NUMBER = "PHONE_NUMBER"
    URL = "URL"
    LOCATION = "LOCATION"
    PERSON = "PERSON"
    MEDICAL_LICENSE = "MEDICAL_LICENSE"
    US_BANK_NUMBER = "US_BANK_NUMBER"
    US_DRIVER_LICENSE = "US_DRIVER_LICENSE"
    US_ITIN = "US_ITIN"
    US_PASSPORT = "US_PASSPORT"
    US_SSN = "US_SSN"
    UK_NHS = "UK_NHS"
    ES_NIF = "ES_NIF"
    IT_FISCAL_CODE = "IT_FISCAL_CODE"
    IT_DRIVER_LICENSE = "IT_DRIVER_LICENSE"
    IT_VAT_CODE = "IT_VAT_CODE"
    IT_PASSPORT = "IT_PASSPORT"
    IT_IDENTITY_CARD = "IT_IDENTITY_CARD"
    SG_NRIC_FIN = "SG_NRIC_FIN"
    AU_ABN = "AU_ABN"
    AU_ACN = "AU_ACN"
    AU_TFN = "AU_TFN"
    AU_MEDICARE_NUMBER = "AU_MEDICARE_NUMBER"


class DoctranConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    openai_model: str
    openai_client: Any
    openai_token_limit: int


class Document(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    uri: str
    id: str
    content_type: ContentType
    raw_content: str
    transformed_content: str
    config: DoctranConfig
    extracted_properties: Dict[str, Any] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None

    def extract(self, *, properties: List[ExtractProperty]) -> "DocumentTransformationBuilder":
        builder = DocumentTransformationBuilder(self)
        return builder.extract(properties=properties)

    def summarize(self, token_limit: int = 100) -> "DocumentTransformationBuilder":
        builder = DocumentTransformationBuilder(self)
        return builder.summarize(token_limit=token_limit)

    def redact(
        self,
        *,
        entities: List[Union[RecognizerEntity, str]],
        spacy_model: str = "en_core_web_md",
        interactive: bool = False,
    ) -> "DocumentTransformationBuilder":
        builder = DocumentTransformationBuilder(self)
        return builder.redact(
            entities=entities,
            spacy_model=spacy_model,
            interactive=interactive,
        )

    def refine(self, *, topics: Optional[List[str]] = None) -> "DocumentTransformationBuilder":
        builder = DocumentTransformationBuilder(self)
        return builder.refine(topics=topics)

    def translate(self, language: str) -> "DocumentTransformationBuilder":
        builder = DocumentTransformationBuilder(self)
        return builder.translate(language=language)

    def interrogate(self) -> "DocumentTransformationBuilder":
        builder = DocumentTransformationBuilder(self)
        return builder.interrogate()


class DocumentTransformationBuilder:
    def __init__(self, document: Document) -> None:
        self.document = document
        self.transformations: List[tuple[str, Dict[str, Any]]] = []

    def extract(self, *, properties: List[ExtractProperty]) -> "DocumentTransformationBuilder":
        self.transformations.append(("extract", {"properties": properties}))
        return self

    def summarize(self, token_limit: int = 100) -> "DocumentTransformationBuilder":
        self.transformations.append(("summarize", {"token_limit": token_limit}))
        return self

    def redact(
        self,
        *,
        entities: List[Union[RecognizerEntity, str]],
        spacy_model: str = "en_core_web_md",
        interactive: bool = False,
    ) -> "DocumentTransformationBuilder":
        self.transformations.append(
            (
                "redact",
                {
                    "entities": entities,
                    "spacy_model": spacy_model,
                    "interactive": interactive,
                },
            )
        )
        return self

    def refine(self, *, topics: Optional[List[str]] = None) -> "DocumentTransformationBuilder":
        self.transformations.append(("refine", {"topics": topics or []}))
        return self

    def translate(self, language: str) -> "DocumentTransformationBuilder":
        self.transformations.append(("translate", {"language": language}))
        return self

    def interrogate(self) -> "DocumentTransformationBuilder":
        self.transformations.append(("interrogate", {}))
        return self

    def execute(self) -> Document:
        transformed_document = _clone_document(self.document)
        for name, kwargs in self.transformations:
            if name == "extract":
                transformed_document = _extract(transformed_document, **kwargs)
            elif name == "summarize":
                transformed_document = _summarize(transformed_document, **kwargs)
            elif name == "redact":
                transformed_document = _redact(transformed_document, **kwargs)
            elif name == "refine":
                transformed_document = _refine(transformed_document, **kwargs)
            elif name == "translate":
                transformed_document = _translate(transformed_document, **kwargs)
            elif name == "interrogate":
                transformed_document = _interrogate(transformed_document, **kwargs)
            else:
                raise ValueError(f"Unsupported transformation: {name}")
        self.transformations.clear()
        return transformed_document


class Doctran:
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        openai_model: str = "gpt-4o-mini",
        openai_token_limit: int = 8000,
        openai_base_url: Optional[str] = None,
    ) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError(
                "The current environment is missing the 'openai' package. "
                "Install the project requirements first."
            ) from exc

        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("No OpenAI API key provided.")

        base_url = openai_base_url or os.getenv("OPENAI_API_BASE")
        client = OpenAI(api_key=api_key, base_url=base_url)
        self.config = DoctranConfig(
            openai_model=openai_model,
            openai_client=client,
            openai_token_limit=openai_token_limit,
        )

    def close(self) -> None:
        client = getattr(self.config, "openai_client", None)
        if client is None:
            return
        try:
            client.close()
        except Exception:
            pass

    def __enter__(self) -> "Doctran":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def parse(
        self,
        *,
        content: str,
        content_type: Union[ContentType, str] = ContentType.text,
        uri: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Document:
        normalized_type = ContentType(content_type)
        if normalized_type is not ContentType.text:
            raise NotImplementedError(
                "This compatibility layer currently supports only text content."
            )

        return Document(
            uri=uri or str(uuid.uuid4()),
            id=str(uuid.uuid4()),
            content_type=normalized_type,
            raw_content=content,
            transformed_content=content,
            config=self.config,
            metadata=metadata,
        )


class DoctranQATransformer:
    """A drop-in compatibility wrapper for LangChain's DoctranQATransformer."""

    def __init__(
        self,
        openai_api_model: str = "gpt-4o-mini",
        openai_api_key: Optional[str] = None,
        openai_token_limit: int = 8000,
        openai_base_url: Optional[str] = None,
    ) -> None:
        self.doctran = Doctran(
            openai_api_key=openai_api_key,
            openai_model=openai_api_model,
            openai_token_limit=openai_token_limit,
            openai_base_url=openai_base_url,
        )

    def transform_documents(self, documents: List[Any], **_: Any) -> List[Any]:
        transformed_documents: List[Any] = []
        try:
            for document in documents:
                parsed = self.doctran.parse(
                    content=document.page_content,
                    metadata=dict(getattr(document, "metadata", {}) or {}),
                )
                qa_document = parsed.interrogate().execute()
                questions_and_answers = qa_document.extracted_properties.get(
                    "questions_and_answers",
                    [],
                )

                transformed = copy.deepcopy(document)
                merged_metadata = dict(getattr(transformed, "metadata", {}) or {})
                merged_metadata["questions_and_answers"] = questions_and_answers
                transformed.metadata = merged_metadata
                transformed_documents.append(transformed)
            return transformed_documents
        finally:
            self.doctran.close()


class DoctranTextTranslator:
    """A drop-in compatibility wrapper for LangChain's DoctranTextTranslator."""

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        language: str = "english",
        openai_api_model: str = "gpt-4o-mini",
        openai_token_limit: int = 8000,
        openai_base_url: Optional[str] = None,
    ) -> None:
        self.language = language
        self.doctran = Doctran(
            openai_api_key=openai_api_key,
            openai_model=openai_api_model,
            openai_token_limit=openai_token_limit,
            openai_base_url=openai_base_url,
        )

    def transform_documents(self, documents: List[Any], **_: Any) -> List[Any]:
        transformed_documents: List[Any] = []
        try:
            for document in documents:
                parsed = self.doctran.parse(
                    content=document.page_content,
                    metadata=dict(getattr(document, "metadata", {}) or {}),
                )
                translated_document = parsed.translate(language=self.language).execute()

                transformed = copy.deepcopy(document)
                transformed.page_content = translated_document.transformed_content
                transformed.metadata = copy.deepcopy(translated_document.metadata or {})
                transformed_documents.append(transformed)
            return transformed_documents
        finally:
            self.doctran.close()


def _extract(document: Document, *, properties: List[ExtractProperty]) -> Document:
    schema_properties: Dict[str, Any] = {}
    required: List[str] = []
    for prop in properties:
        schema_properties[prop.name] = {
            "type": prop.type,
            "description": prop.description,
            **({"items": prop.items} if prop.items is not None else {}),
            **({"enum": prop.enum} if prop.enum is not None else {}),
        }
        if prop.required:
            required.append(prop.name)

    payload = _run_openai_tool_call(
        document,
        function_name="extract_information",
        function_description="Extract structured data from a raw text document.",
        parameters={
            "type": "object",
            "properties": schema_properties,
            "required": required,
        },
    )
    document.extracted_properties.update(payload)
    return document


def _clone_document(document: Document) -> Document:
    # Keep the OpenAI client by reference and only clone the user data fields.
    # Deep-copying the client triggers pickling errors because httpx contains locks.
    return Document(
        uri=document.uri,
        id=document.id,
        content_type=document.content_type,
        raw_content=document.raw_content,
        transformed_content=document.transformed_content,
        config=document.config,
        extracted_properties=copy.deepcopy(document.extracted_properties),
        metadata=copy.deepcopy(document.metadata),
    )


def _summarize(document: Document, *, token_limit: int = 100) -> Document:
    payload = _run_openai_tool_call(
        document,
        function_name="summarize",
        function_description=f"Summarize a document in under {token_limit} tokens.",
        parameters={
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "The summary of the document.",
                }
            },
            "required": ["summary"],
        },
    )
    document.transformed_content = payload["summary"]
    return document


def _refine(document: Document, *, topics: Optional[List[str]] = None) -> Document:
    description = "Remove all irrelevant information from a document."
    if topics:
        description = (
            "Remove all information from a document that is not relevant to the "
            f"following topics: {'; '.join(topics)}"
        )

    payload = _run_openai_tool_call(
        document,
        function_name="refine",
        function_description=description,
        parameters={
            "type": "object",
            "properties": {
                "refined_document": {
                    "type": "string",
                    "description": "The document with irrelevant information removed.",
                }
            },
            "required": ["refined_document"],
        },
    )
    document.transformed_content = payload["refined_document"]
    return document


def _translate(document: Document, *, language: str) -> Document:
    payload = _run_openai_tool_call(
        document,
        function_name="translate",
        function_description=f"Translate a document into {language}.",
        parameters={
            "type": "object",
            "properties": {
                "translated_document": {
                    "type": "string",
                    "description": f"The document translated into {language}.",
                }
            },
            "required": ["translated_document"],
        },
    )
    document.transformed_content = payload["translated_document"]
    return document


def _interrogate(document: Document) -> Document:
    payload = _run_openai_tool_call(
        document,
        function_name="interrogate",
        function_description="Convert a text document into a series of questions and answers.",
        parameters={
            "type": "object",
            "properties": {
                "questions_and_answers": {
                    "type": "array",
                    "description": "The list of questions and answers.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "The question.",
                            },
                            "answer": {
                                "type": "string",
                                "description": "The answer.",
                            },
                        },
                        "required": ["question", "answer"],
                    },
                }
            },
            "required": ["questions_and_answers"],
        },
    )
    document.extracted_properties.update(payload)
    return document


def _redact(
    document: Document,
    *,
    entities: List[Union[RecognizerEntity, str]],
    spacy_model: str = "en_core_web_md",
    interactive: bool = False,
) -> Document:
    try:
        import spacy
        from presidio_analyzer import AnalyzerEngine
        from presidio_analyzer.nlp_engine import NlpEngineProvider
        from presidio_anonymizer import AnonymizerEngine
        from presidio_anonymizer.entities import OperatorConfig
    except ImportError as exc:
        raise ImportError(
            "Redact requires optional packages. Install the pins from "
            "'requirements-doctran-compat.txt' first."
        ) from exc

    normalized_entities = [_normalize_entity(entity) for entity in entities]

    try:
        spacy.load(spacy_model)
    except OSError:
        from spacy.cli.download import download

        if interactive:
            answer = input(
                f"{spacy_model} is required for redact. Download it now? (Y/n) "
            ).strip()
            if answer.lower() in {"n", "no"}:
                raise RuntimeError(f"Cannot run redact without the '{spacy_model}' model.")

        download(spacy_model)

    nlp_engine_provider = NlpEngineProvider(
        nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": spacy_model}],
        }
    )
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine_provider.create_engine())
    anonymizer = AnonymizerEngine()

    results = analyzer.analyze(
        text=document.transformed_content,
        entities=normalized_entities or None,
        language="en",
    )
    anonymized = anonymizer.anonymize(
        text=document.transformed_content,
        analyzer_results=results,
        operators={"DEFAULT": OperatorConfig("replace")},
    )
    document.transformed_content = anonymized.text
    return document


def _normalize_entity(entity: Union[RecognizerEntity, str]) -> str:
    if isinstance(entity, RecognizerEntity):
        return entity.value
    if entity in RecognizerEntity.__members__:
        return RecognizerEntity[entity].value

    valid_entities = ", ".join(RecognizerEntity.__members__.keys())
    raise ValueError(f"Invalid entity type '{entity}'. Valid values: {valid_entities}")


def _run_openai_tool_call(
    document: Document,
    *,
    function_name: str,
    function_description: str,
    parameters: Dict[str, Any],
) -> Dict[str, Any]:
    _ensure_token_limit(
        content=document.transformed_content,
        model=document.config.openai_model,
        token_limit=document.config.openai_token_limit,
    )

    response = document.config.openai_client.chat.completions.create(
        model=document.config.openai_model,
        messages=[{"role": "user", "content": document.transformed_content}],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": function_name,
                    "description": function_description,
                    "parameters": parameters,
                },
            }
        ],
        tool_choice={"type": "function", "function": {"name": function_name}},
        temperature=0,
    )

    message = response.choices[0].message
    tool_calls = getattr(message, "tool_calls", None) or []
    if not tool_calls:
        text_content = _extract_message_text(message)
        if text_content:
            parsed = _try_parse_json_text(text_content)
            if parsed is not None:
                return parsed

        return _run_openai_json_fallback(
            document,
            function_name=function_name,
            function_description=function_description,
            parameters=parameters,
        )

    raw_arguments = tool_calls[0].function.arguments
    try:
        return json.loads(raw_arguments)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "OpenAI returned malformed JSON. Consider using a stronger model or "
            "a larger token limit."
        ) from exc


def _run_openai_json_fallback(
    document: Document,
    *,
    function_name: str,
    function_description: str,
    parameters: Dict[str, Any],
) -> Dict[str, Any]:
    schema_json = json.dumps(parameters, ensure_ascii=False)
    response = document.config.openai_client.chat.completions.create(
        model=document.config.openai_model,
        messages=[
            {
                "role": "system",
                "content": (
                    f"You are executing the task '{function_name}'. "
                    f"{function_description} "
                    "Return only one valid JSON object and no markdown."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Process the following document and return a JSON object that "
                    f"matches this schema exactly: {schema_json}\n\n"
                    f"Document:\n{document.transformed_content}"
                ),
            },
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    message = response.choices[0].message
    text_content = _extract_message_text(message)
    parsed = _try_parse_json_text(text_content)
    if parsed is None:
        raise RuntimeError(
            "OpenAI did not return tool call arguments, and the JSON fallback "
            "response was not valid JSON."
        )
    return parsed


def _extract_message_text(message: Any) -> str:
    content = getattr(message, "content", None)
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if text:
                    parts.append(text)
            else:
                text = getattr(item, "text", None)
                if text:
                    parts.append(text)
        return "".join(parts)
    return str(content)


def _try_parse_json_text(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None

    stripped = text.strip()
    try:
        parsed = json.loads(stripped)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    candidate = stripped[start : end + 1]
    try:
        parsed = json.loads(candidate)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def _ensure_token_limit(*, content: str, model: str, token_limit: int) -> None:
    try:
        import tiktoken
    except ImportError:
        return

    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    content_token_size = len(encoding.encode(content))
    if content_token_size > token_limit:
        raise ValueError(
            f"The document is {content_token_size} tokens long, which exceeds the "
            f"token limit of {token_limit}."
        )

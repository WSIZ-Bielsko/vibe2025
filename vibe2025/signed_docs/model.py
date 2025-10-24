from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class Paragraph(BaseModel):
    fixed_text: str
    placeholder: str
    text: str


class Document(BaseModel):
    id: UUID
    parent_document_id: UUID | None = None
    author_id: int
    addressee_id: int
    created_at: datetime
    content: list[Paragraph]


class Signature(BaseModel):
    document_id: UUID
    json_version: str
    signator_id: int
    public_key: str
    signature: str
    signed_at: datetime

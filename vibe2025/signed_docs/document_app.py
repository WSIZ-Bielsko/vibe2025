from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from vibe2025.signed_docs.model import Document, Signature
from vibe2025.signed_docs.service import SignedDocumentsService


# Request/Response models
class AddKeyRequest(BaseModel):
    signer_id: int
    public_key_pem: str


class AddKeyResponse(BaseModel):
    success: bool
    message: str


class RemoveKeyResponse(BaseModel):
    success: bool
    message: str


class VerifyRequest(BaseModel):
    document: Document
    signature: Signature


class VerifyResponse(BaseModel):
    valid: bool
    message: str


class TrustedSignersResponse(BaseModel):
    signer_ids: list[int]


class GetKeyResponse(BaseModel):
    signer_id: int
    public_key_pem: str | None
    found: bool


# FastAPI app
app = FastAPI(title="Signed Documents Service API", version="1.0.0")

# Service instance (in production, use dependency injection)
service = SignedDocumentsService()


@app.post("/keys/add", response_model=AddKeyResponse, status_code=status.HTTP_201_CREATED)
async def add_trusted_key(request: AddKeyRequest):
    """Add a trusted public key for a signer"""
    try:
        # Normalize newlines - handle both literal \n strings and actual newlines
        public_key_pem = request.public_key_pem.replace('\\n', '\n')

        service.add_trusted_key(request.signer_id, public_key_pem)
        return AddKeyResponse(
            success=True,
            message=f"Successfully added trusted key for signer {request.signer_id}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@app.delete("/keys/{signer_id}", response_model=RemoveKeyResponse)
async def remove_trusted_key(signer_id: int):
    """Remove a trusted public key"""
    removed = service.remove_trusted_key(signer_id)
    if removed:
        return RemoveKeyResponse(
            success=True,
            message=f"Successfully removed key for signer {signer_id}"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Signer {signer_id} not found"
        )


@app.get("/keys/{signer_id}", response_model=GetKeyResponse)
async def get_trusted_key(signer_id: int):
    """Get trusted public key for a signer"""
    key = service.get_trusted_key(signer_id)
    return GetKeyResponse(
        signer_id=signer_id,
        public_key_pem=key,
        found=key is not None
    )


@app.get("/keys", response_model=TrustedSignersResponse)
async def list_trusted_signers():
    """List all trusted signer IDs"""
    return TrustedSignersResponse(signer_ids=service.list_trusted_signers())


@app.post("/verify", response_model=VerifyResponse)
async def verify_document_signature(request: VerifyRequest):
    """Verify a document signature"""
    try:
        is_valid = service.verify_document_signature(request.document, request.signature)

        if is_valid:
            return VerifyResponse(
                valid=True,
                message="Signature is valid"
            )
        else:
            return VerifyResponse(
                valid=False,
                message="Signature is invalid or signer is not trusted"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification error: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "trusted_signers_count": len(service.list_trusted_signers())}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

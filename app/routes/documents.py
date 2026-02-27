import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from app.db.base import get_db
from app.models.user import User
from app.models.document import Document
from app.auth.dependencies import get_current_user
from app.services.s3_service import (
    upload_file_to_s3,
    generate_presigned_url,
    delete_file_from_s3,
    list_files_in_s3,
)
from app.schemas.schemas import DocumentRead, PresignedURLResponse

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document to S3 and save metadata in the database",
)
async def upload_document(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Build a unique S3 key: <user_id>/<uuid>-<filename>
    s3_key = f"{current_user.id}/{uuid.uuid4()}-{file.filename}"

    try:
        upload_file_to_s3(file.file, s3_key, file.content_type or "application/octet-stream")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"S3 upload failed: {exc}",
        )

    doc = Document(
        document_name=file.filename,
        document_type=file.content_type or "application/octet-stream",
        document_size=file.size or 0,
        description=description,
        s3_key=s3_key,
        user_id=current_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get(
    "/",
    response_model=list[DocumentRead],
    summary="List all documents for the current user",
)
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Document).filter(Document.user_id == current_user.id).all()


@router.get(
    "/{document_id}/download",
    response_model=PresignedURLResponse,
    summary="Get a presigned URL to download a document from S3",
)
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id,
    ).first()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    try:
        url = generate_presigned_url(doc.s3_key)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not generate presigned URL: {exc}",
        )

    return {"presigned_url": url, "expires_in_seconds": 3600}


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document from S3 and remove its metadata from the database",
)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id,
    ).first()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    try:
        delete_file_from_s3(doc.s3_key)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"S3 delete failed: {exc}",
        )

    db.delete(doc)
    db.commit()

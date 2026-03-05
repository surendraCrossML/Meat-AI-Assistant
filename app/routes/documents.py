import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from app.db.base import get_db
from app.models.document import Document
from app.services.s3_service import (
    upload_file_to_s3,
    generate_presigned_url,
    delete_file_from_s3,
    list_files_in_s3,
    read_file_from_s3,
)
from app.services.gemini_service import (
    extract_keywords_from_query,
    generate_response_from_documents,
)
from app.schemas.schemas import (
    DocumentRead,
    PresignedURLResponse,
    DocumentSearchRequest,
    DocumentQueryRequest,
    DocumentQueryResponse,
    KeywordExtractionResponse,
)

router = APIRouter(prefix="/documents", tags=["Documents"])

# Fixed S3 folder — all documents go here regardless of who uploads them
S3_FOLDER = "beef-documents"


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
):
    # Build a unique S3 key inside the fixed beef-documents folder
    s3_key = f"{S3_FOLDER}/{uuid.uuid4()}-{file.filename}"

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
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get(
    "/",
    response_model=list[DocumentRead],
    summary="List all documents",
)
def list_documents(
    db: Session = Depends(get_db),
):
    return db.query(Document).all()


@router.get(
    "/{document_id}/download",
    response_model=PresignedURLResponse,
    summary="Get a presigned URL to download a document from S3",
)
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(Document.id == document_id).first()

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
):
    doc = db.query(Document).filter(Document.id == document_id).first()

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


@router.post(
    "/query",
    response_model=DocumentQueryResponse,
    summary="Query documents using natural language with AI keyword extraction",
)
def query_documents_with_ai(
    request: DocumentQueryRequest,
    db: Session = Depends(get_db),
):
    """
    Query documents using natural language.

    This endpoint:
    1. Takes a user query in natural language
    2. Uses Gemini AI to extract relevant keywords (recipes, beef-related terms)
    3. Searches the database for matching documents
    4. Returns matching documents with extraction details

    Request body:
    - **query**: Your question or search intent (e.g., "What are the best beef recipes for a healthy diet?")

    Response includes:
    - Extracted keywords and summaries
    - List of matching documents
    - Summary of the search
    """
    try:
        # Extract keywords using Gemini AI
        keywords_data = extract_keywords_from_query(request.query)

        # Prepare keyword extraction response
        extracted_keywords = KeywordExtractionResponse(**keywords_data)

        # Combine all keywords for comprehensive search
        all_keywords = extracted_keywords.keywords

        # Search documents using extracted keywords
        matching_documents = []

        for keyword in all_keywords:
            search_term = f"%{keyword}%"
            docs = db.query(Document).filter(
                (Document.document_name.ilike(search_term)) |
                (Document.description.ilike(search_term))
            ).all()

            # Add unique documents to the matching list
            for doc in docs:
                if not any(d.id == doc.id for d in matching_documents):
                    matching_documents.append(doc)

        # Create summary
        summary = f"Found {len(matching_documents)} document(s) matching your search for: {extracted_keywords.query_summary}"

        # Fetch actual file content from S3 for each matched document
        docs_for_llm = []
        for doc in matching_documents:
            try:
                file_content = read_file_from_s3(doc.s3_key)
            except Exception:
                # Fall back to description if S3 read fails
                file_content = doc.description or ""
            docs_for_llm.append({
                "document_name": doc.document_name,
                "content": file_content,
            })
        # Ask Gemini to produce a response based on the documents
        try:
            agent_response = generate_response_from_documents(request.query, docs_for_llm)
        except Exception:
            agent_response = "Unable to generate response from documents."

        return DocumentQueryResponse(
            user_query=request.query,
            extracted_keywords=extracted_keywords,
            matching_documents=matching_documents,
            summary=summary,
            agent_response=agent_response,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"AI service error: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}",
        )
"""Router FastAPI pour le module documents (upload, analyse, CRUD)."""

import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.user import User
from app.modules.documents.schemas import (
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadResponse,
    QuotaStatus,
    ReanalyzeResponse,
)
from app.modules.documents.service import (
    QuotaExceededError,
    check_user_storage_quota,
    delete_document,
    get_document,
    list_documents,
    upload_document,
)

router = APIRouter()

MAX_FILES_PER_UPLOAD = 5


# ─── Helpers ──────────────────────────────────────────────────────────


def _check_document_ownership(document, user: User) -> None:
    """Vérifier que l'utilisateur est propriétaire du document."""
    if document.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé",
        )


def _document_to_response(document) -> DocumentResponse:
    """Convertir un Document ORM en DocumentResponse."""
    return DocumentResponse(
        id=document.id,
        original_filename=document.original_filename,
        mime_type=document.mime_type,
        file_size=document.file_size,
        status=document.status,
        document_type=document.document_type,
        has_analysis=document.analysis is not None
        if hasattr(document, "analysis") and document.analysis is not None
        else False,
        created_at=document.created_at,
    )


# ─── POST /upload ────────────────────────────────────────────────────


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_documents(
    files: list[UploadFile] = File(...),
    conversation_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    """Uploader un ou plusieurs fichiers (max 5)."""
    if len(files) > MAX_FILES_PER_UPLOAD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {MAX_FILES_PER_UPLOAD} fichiers par upload",
        )

    # Lire tous les contenus en mémoire AVANT toute écriture disque.
    # Évite les orphelins disque quand un fichier tardif d'un batch
    # dépasse le quota — cf. review D2.
    files_data: list[tuple[UploadFile, bytes]] = []
    for file in files:
        content = await file.read()
        files_data.append((file, content))

    # Pré-check quota aggregate du batch AVANT tout _save_file_to_disk.
    from app.core.config import settings

    total_new_bytes = sum(len(content) for _, content in files_data)
    total_new_docs = len(files_data)

    bytes_used, docs_count = await check_user_storage_quota(db, current_user.id)
    bytes_limit = settings.quota_bytes_per_user_mb * 1024 * 1024
    docs_limit = settings.quota_docs_per_user

    # Ordre : docs AVANT bytes, cf. AC3 du spec (message « documents »
    # prioritaire quand les deux quotas sont dépassés simultanément).
    if docs_count + total_new_docs > docs_limit:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"Quota atteint : {docs_count}/{docs_limit} documents. "
                "Supprimez d'anciens documents pour libérer de l'espace."
            ),
        )
    if bytes_used + total_new_bytes > bytes_limit:
        used_mb = bytes_used // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"Quota atteint : "
                f"{used_mb}/{settings.quota_bytes_per_user_mb} MB. "
                "Supprimez d'anciens documents pour libérer de l'espace."
            ),
        )

    uploaded_docs: list[DocumentResponse] = []

    for file, content in files_data:
        try:
            doc = await upload_document(
                db=db,
                user_id=current_user.id,
                filename=file.filename or "document",
                content=content,
                content_type=file.content_type or "application/octet-stream",
                file_size=len(content),
                conversation_id=conversation_id,
            )
            uploaded_docs.append(
                DocumentResponse(
                    id=doc.id,
                    original_filename=doc.original_filename,
                    mime_type=doc.mime_type,
                    file_size=doc.file_size,
                    status=doc.status,
                    document_type=doc.document_type,
                    has_analysis=False,
                    created_at=doc.created_at,
                )
            )
        except QuotaExceededError as e:
            # Défense en profondeur : le pré-check amont rejette déjà,
            # mais un appel concurrent pourrait pousser un utilisateur
            # juste au-dessus de la limite entre le pré-check et l'insert.
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=str(e),
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    return DocumentUploadResponse(documents=uploaded_docs)


# ─── GET / ───────────────────────────────────────────────────────────


@router.get("/", response_model=DocumentListResponse)
async def list_user_documents(
    document_type: str | None = Query(None),
    document_status: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    """Lister les documents de l'utilisateur avec filtres et pagination."""
    documents, total = await list_documents(
        db=db,
        user_id=current_user.id,
        document_type=document_type,
        status=document_status,
        page=page,
        limit=limit,
    )

    return DocumentListResponse(
        documents=[
            DocumentResponse(
                id=doc.id,
                original_filename=doc.original_filename,
                mime_type=doc.mime_type,
                file_size=doc.file_size,
                status=doc.status,
                document_type=doc.document_type,
                has_analysis=False,
                created_at=doc.created_at,
            )
            for doc in documents
        ],
        total=total,
        page=page,
        limit=limit,
    )


# ─── GET /quota ──────────────────────────────────────────────────────
# L'ordre de déclaration n'est plus critique depuis que les routes
# suivantes utilisent le path converter `{document_id:uuid}` — « quota »
# n'est pas un UUID valide, donc aucune collision possible.


@router.get("/quota", response_model=QuotaStatus)
@limiter.limit("60/minute")
async def get_quota_status(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QuotaStatus:
    """Récupérer le statut de quota de l'utilisateur (dette spec 004 §3.2).

    Rate-limité à 60 req/min/utilisateur (review D3) pour protéger la BDD
    contre le polling abusif de l'agrégat SUM+COUNT. Le paramètre `response`
    est requis par SlowAPI pour pouvoir injecter les en-têtes X-RateLimit-*
    (headers_enabled=True dans rate_limit.py).
    """
    from app.core.config import settings

    bytes_used, docs_count = await check_user_storage_quota(db, current_user.id)
    bytes_limit = settings.quota_bytes_per_user_mb * 1024 * 1024
    docs_limit = settings.quota_docs_per_user
    bytes_pct = (
        min(100, round(bytes_used / bytes_limit * 100)) if bytes_limit else 0
    )
    docs_pct = (
        min(100, round(docs_count / docs_limit * 100)) if docs_limit else 0
    )
    return QuotaStatus(
        bytes_used=bytes_used,
        bytes_limit=bytes_limit,
        docs_count=docs_count,
        docs_limit=docs_limit,
        usage_percent=max(bytes_pct, docs_pct),
    )


# ─── GET /{id} ───────────────────────────────────────────────────────


@router.get("/{document_id:uuid}", response_model=DocumentDetailResponse)
async def get_document_detail(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentDetailResponse:
    """Récupérer le détail d'un document avec son analyse."""
    document = await get_document(db, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document non trouvé",
        )

    _check_document_ownership(document, current_user)

    from app.modules.documents.schemas import DocumentAnalysisResponse

    analysis_response = None
    if document.analysis is not None:
        analysis_response = DocumentAnalysisResponse.model_validate(document.analysis)

    return DocumentDetailResponse(
        id=document.id,
        original_filename=document.original_filename,
        mime_type=document.mime_type,
        file_size=document.file_size,
        status=document.status,
        document_type=document.document_type,
        created_at=document.created_at,
        analysis=analysis_response,
    )


# ─── DELETE /{id} ────────────────────────────────────────────────────


@router.delete("/{document_id:uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_endpoint(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Supprimer un document (fichier physique + BDD)."""
    document = await get_document(db, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document non trouvé",
        )

    _check_document_ownership(document, current_user)
    await delete_document(db, document)


# ─── POST /{id}/reanalyze ───────────────────────────────────────────


@router.post("/{document_id:uuid}/reanalyze", response_model=ReanalyzeResponse)
async def reanalyze_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReanalyzeResponse:
    """Relancer l'analyse d'un document."""
    document = await get_document(db, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document non trouvé",
        )

    _check_document_ownership(document, current_user)

    from app.models.document import DocumentStatus

    document.status = DocumentStatus.processing
    await db.flush()

    return ReanalyzeResponse(
        id=document.id,
        status=document.status,
        message="Analyse relancée avec succès",
    )


# ─── GET /{id}/preview ─────────────────────────────────────────────


@router.get("/{document_id:uuid}/preview")
async def preview_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Servir le fichier pour prévisualisation (images et PDFs)."""
    document = await get_document(db, document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document non trouvé",
        )

    _check_document_ownership(document, current_user)

    from app.modules.documents.service import UPLOADS_DIR

    file_path = Path(UPLOADS_DIR.parent / document.storage_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fichier introuvable sur le serveur",
        )

    return FileResponse(
        path=str(file_path),
        media_type=document.mime_type,
        filename=document.original_filename,
    )

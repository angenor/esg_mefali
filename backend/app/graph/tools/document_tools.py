"""Tools LangChain pour le noeud analyse de documents.

Trois tools exposes au LLM :
- analyze_uploaded_document : lancer l'analyse d'un document
- get_document_analysis : consulter les resultats d'analyse
- list_user_documents : lister les documents de l'utilisateur
"""

import uuid

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.graph.tools.common import get_db_and_user, with_retry


@tool
async def analyze_uploaded_document(
    document_id: str,
    config: RunnableConfig,
) -> str:
    """Analyser un document uploade par l'utilisateur.

    Utilise cet outil quand un document est uploade et doit etre analyse.
    N'analyse JAMAIS un document sur la base du nom de fichier seul —
    appelle toujours ce tool pour obtenir l'analyse reelle.

    Args:
        document_id: Identifiant UUID du document a analyser.
    """
    from app.modules.documents.service import analyze_document, get_document

    db, _user_id = get_db_and_user(config)

    document = await get_document(db=db, document_id=uuid.UUID(document_id))
    if document is None:
        return f"Document introuvable (id={document_id})."

    analysis = await analyze_document(db=db, document=document)

    findings = analysis.key_findings if hasattr(analysis, "key_findings") and analysis.key_findings else []
    findings_text = "\n".join(f"  - {f}" for f in findings[:5]) if findings else "  Aucun point cle identifie."

    return (
        f"Analyse du document '{document.filename}' terminee.\n"
        f"- Type : {analysis.document_type}\n"
        f"- Resume : {analysis.summary[:300] if analysis.summary else 'N/A'}\n"
        f"- Points cles :\n{findings_text}\n"
        f"- Confiance : {getattr(analysis, 'confidence_score', 'N/A')}"
    )


@tool
async def get_document_analysis(
    document_id: str,
    config: RunnableConfig,
) -> str:
    """Consulter les resultats d'analyse d'un document deja analyse.

    Utilise cet outil quand l'utilisateur demande les resultats d'analyse,
    le resume ou les points cles d'un document specifique.

    Args:
        document_id: Identifiant UUID du document.
    """
    from app.modules.documents.service import get_document

    db, _user_id = get_db_and_user(config)

    document = await get_document(db=db, document_id=uuid.UUID(document_id))
    if document is None:
        return f"Document introuvable (id={document_id})."

    analysis = document.analysis if hasattr(document, "analysis") else None
    if analysis is None:
        return (
            f"Le document '{document.filename}' n'a pas encore ete analyse. "
            f"Utilisez le tool analyze_uploaded_document pour lancer l'analyse."
        )

    findings = analysis.key_findings if hasattr(analysis, "key_findings") and analysis.key_findings else []
    findings_text = "\n".join(f"  - {f}" for f in findings[:5]) if findings else "  Aucun point cle identifie."

    return (
        f"Resultats d'analyse de '{document.filename}' :\n"
        f"- Type : {analysis.document_type}\n"
        f"- Resume : {analysis.summary[:300] if analysis.summary else 'N/A'}\n"
        f"- Points cles :\n{findings_text}\n"
        f"- Confiance : {getattr(analysis, 'confidence_score', 'N/A')}"
    )


@tool
async def list_user_documents(
    config: RunnableConfig,
    document_type: str | None = None,
) -> str:
    """Lister les documents uploades par l'utilisateur.

    Utilise cet outil quand l'utilisateur demande a voir ses documents,
    cherche un document specifique, ou veut connaitre les documents disponibles.

    Args:
        document_type: Filtrer par type de document (optionnel).
    """
    from app.modules.documents.service import list_documents

    db, user_id = get_db_and_user(config)

    documents, total = await list_documents(
        db=db,
        user_id=user_id,
        document_type=document_type,
    )

    if not documents:
        return "Aucun document trouve pour cet utilisateur."

    lines: list[str] = [f"{total} document(s) trouve(s) :"]
    for doc in documents[:10]:
        status = doc.status if hasattr(doc, "status") else "N/A"
        lines.append(
            f"  - {doc.filename} (type: {doc.document_type or 'N/A'}, "
            f"statut: {status}, id: {doc.id})"
        )

    if total > 10:
        lines.append(f"  ... et {total - 10} autres documents.")

    return "\n".join(lines)


DOCUMENT_TOOLS = [
    with_retry(analyze_uploaded_document, max_retries=2, node_name="document"),
    with_retry(get_document_analysis, max_retries=2, node_name="document"),
    with_retry(list_user_documents, max_retries=2, node_name="document"),
]

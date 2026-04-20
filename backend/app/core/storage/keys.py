"""Helpers purs de construction de clés storage opaques.

Les clés produites sont **portables** entre `LocalStorageProvider` et
`S3StorageProvider` : le même string est stocké dans `Document.storage_path`
et `Report.file_path`, indépendamment du backend actif.

Préfixes (Task 5 storage.md §4 + piège #13) :
  - ``documents/{user_id}/{document_id}/{filename}``
  - ``reports/{report_id}/{filename}``

Permet des IAM policies S3 granulaires par préfixe en Phase Growth.
"""

from __future__ import annotations

import uuid


def storage_key_for_document(
    user_id: uuid.UUID,
    document_id: uuid.UUID,
    filename: str,
) -> str:
    """Retourne la clé opaque canonique pour un document utilisateur.

    La sanitation du filename est la responsabilité de l'appelant
    (`documents.service._sanitize_filename`) ; ce helper ne dédouble pas
    cette responsabilité (principe Single Source of Truth).
    """
    return f"documents/{user_id}/{document_id}/{filename}"


def storage_key_for_report(
    report_id: uuid.UUID,
    filename: str,
) -> str:
    """Retourne la clé opaque canonique pour un rapport ESG."""
    return f"reports/{report_id}/{filename}"

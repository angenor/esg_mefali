# API Contracts: Rapports ESG PDF

**Feature**: 006-esg-pdf-reports
**Base path**: `/api/reports`

## POST /api/reports/esg/{assessment_id}/generate

Lance la génération d'un rapport PDF pour une évaluation ESG.

**Path Parameters** :
- `assessment_id` (UUID) : Identifiant de l'évaluation ESG

**Response 201** :
```json
{
  "id": "uuid",
  "assessment_id": "uuid",
  "report_type": "esg_compliance",
  "status": "generating",
  "created_at": "2026-03-31T10:00:00Z"
}
```

**Response 400** : Évaluation non complétée
```json
{
  "detail": "L'évaluation ESG doit être au statut 'completed' pour générer un rapport."
}
```

**Response 404** : Évaluation non trouvée
**Response 409** : Génération déjà en cours pour cette évaluation

---

## GET /api/reports/{report_id}/download

Télécharge le fichier PDF d'un rapport.

**Path Parameters** :
- `report_id` (UUID) : Identifiant du rapport

**Response 200** :
- Content-Type: `application/pdf`
- Content-Disposition: `attachment; filename="rapport-esg-{entreprise}-{date}.pdf"`
- Body: fichier PDF binaire

**Response 404** : Rapport non trouvé ou fichier manquant
**Response 403** : Accès refusé (rapport d'un autre utilisateur)

---

## GET /api/reports/

Liste les rapports de l'utilisateur connecté.

**Query Parameters** :
- `page` (int, default: 1) : Numéro de page
- `limit` (int, default: 20, max: 100) : Nombre par page
- `assessment_id` (UUID, optional) : Filtrer par évaluation

**Response 200** :
```json
{
  "items": [
    {
      "id": "uuid",
      "assessment_id": "uuid",
      "report_type": "esg_compliance",
      "status": "completed",
      "file_size": 245000,
      "generated_at": "2026-03-31T10:00:30Z",
      "created_at": "2026-03-31T10:00:00Z"
    }
  ],
  "total": 5,
  "page": 1,
  "limit": 20
}
```

---

## GET /api/reports/{report_id}/status

Vérifie le statut de génération d'un rapport (polling frontend).

**Path Parameters** :
- `report_id` (UUID) : Identifiant du rapport

**Response 200** :
```json
{
  "id": "uuid",
  "status": "completed",
  "generated_at": "2026-03-31T10:00:30Z"
}
```

**Valeurs possibles de status** : `generating`, `completed`, `failed`

---

## Notes d'intégration

- Tous les endpoints nécessitent authentification (user_id extrait du token)
- Les rapports sont filtrés par `user_id` — un utilisateur ne voit que ses propres rapports
- Le endpoint `POST /generate` est synchrone : il retourne immédiatement avec `status: generating`, puis le frontend poll `/status` jusqu'à `completed`
- Le nom du fichier téléchargé suit le format : `rapport-esg-{nom_entreprise}-{YYYY-MM-DD}.pdf`

# API Contracts: Dashboard & Plan d'action

**Feature**: 011-dashboard-action-plan
**Date**: 2026-04-01
**Base URL**: `/api`

---

## Dashboard

### GET /dashboard/summary

Vue synthétique agrégée de tous les modules.

**Auth**: Bearer token requis

**Response 200**:
```json
{
  "esg": {
    "score": 67,
    "grade": "B",
    "trend": "up",
    "last_assessment_date": "2026-03-15",
    "pillar_scores": { "environment": 72, "social": 58, "governance": 71 }
  },
  "carbon": {
    "total_tco2e": 45.2,
    "year": 2025,
    "variation_percent": -12.5,
    "top_category": "energy",
    "categories": { "energy": 22.1, "transport": 15.3, "waste": 7.8 }
  },
  "credit": {
    "score": 72,
    "grade": "B+",
    "last_calculated": "2026-03-20"
  },
  "financing": {
    "recommended_funds_count": 5,
    "active_applications_count": 3,
    "application_statuses": {
      "preparation": 2,
      "submitted": 1,
      "pending": 0
    },
    "next_intermediary_action": {
      "title": "Rendez-vous SIB (guichet SUNREF)",
      "due_date": "2026-04-15",
      "intermediary_name": "SIB"
    },
    "has_intermediary_paths": true
  },
  "next_actions": [
    {
      "id": "uuid",
      "title": "Prendre rendez-vous avec la SIB",
      "category": "intermediary_contact",
      "due_date": "2026-04-15",
      "status": "todo",
      "intermediary_name": "SIB",
      "intermediary_address": "Plateau, Abidjan"
    }
  ],
  "recent_activity": [
    {
      "type": "action_status_change",
      "title": "Action complétée",
      "description": "Préparer les bilans comptables",
      "timestamp": "2026-03-30T14:30:00Z",
      "related_entity_type": "action_item",
      "related_entity_id": "uuid"
    }
  ],
  "badges": [
    {
      "badge_type": "first_carbon",
      "unlocked_at": "2026-03-10T09:00:00Z"
    }
  ]
}
```

**Response 200 (nouvel utilisateur, pas de données)**:
```json
{
  "esg": null,
  "carbon": null,
  "credit": null,
  "financing": {
    "recommended_funds_count": 0,
    "active_applications_count": 0,
    "application_statuses": {},
    "next_intermediary_action": null,
    "has_intermediary_paths": false
  },
  "next_actions": [],
  "recent_activity": [],
  "badges": []
}
```

---

## Plan d'action

### POST /action-plan/generate

Génère un plan d'action personnalisé via Claude.

**Auth**: Bearer token requis

**Request Body**:
```json
{
  "timeframe": 12
}
```

| Champ | Type | Requis | Valeurs |
|-------|------|--------|---------|
| timeframe | integer | oui | 6, 12, 24 |

**Response 201**:
```json
{
  "id": "uuid",
  "title": "Plan d'action ESG & Financement — 12 mois",
  "timeframe": 12,
  "status": "active",
  "total_actions": 15,
  "completed_actions": 0,
  "items": [
    {
      "id": "uuid",
      "title": "Prendre rendez-vous avec la SIB (guichet SUNREF)",
      "description": "Adresse : Plateau, Abidjan. Tél : +225 XX XX XX.",
      "category": "intermediary_contact",
      "priority": "high",
      "status": "todo",
      "due_date": "2026-04-15",
      "estimated_cost_xof": 0,
      "estimated_benefit": "Accès au financement SUNREF via la SIB",
      "completion_percentage": 0,
      "related_fund_id": "uuid",
      "related_intermediary_id": "uuid",
      "intermediary_name": "SIB",
      "intermediary_address": "Plateau, Abidjan",
      "intermediary_phone": "+225 XX XX XX",
      "intermediary_email": "contact@sib.ci"
    }
  ],
  "created_at": "2026-04-01T10:00:00Z"
}
```

**Response 428** (profil incomplet):
```json
{
  "detail": {
    "code": "INCOMPLETE_PROFILE",
    "message": "Veuillez compléter votre profil entreprise avant de générer un plan d'action."
  }
}
```

---

### GET /action-plan/

Récupère le plan d'action actif de l'utilisateur.

**Auth**: Bearer token requis

**Response 200**: Même structure que POST /action-plan/generate (sans items)

**Response 404**: Aucun plan actif
```json
{
  "detail": "Aucun plan d'action actif. Générez un plan via le chat ou la page plan d'action."
}
```

---

### GET /action-plan/{plan_id}/items

Actions du plan, filtrable par catégorie.

**Auth**: Bearer token requis

**Query params**:

| Param | Type | Défaut | Description |
|-------|------|--------|-------------|
| category | string | null | Filtre par catégorie (enum) |
| status | string | null | Filtre par statut |
| page | integer | 1 | Page |
| limit | integer | 50 | Items par page |

**Response 200**:
```json
{
  "items": [ /* ActionItem[] */ ],
  "total": 15,
  "page": 1,
  "limit": 50,
  "progress": {
    "global_percentage": 33,
    "by_category": {
      "environment": { "total": 3, "completed": 1, "percentage": 33 },
      "social": { "total": 2, "completed": 1, "percentage": 50 },
      "governance": { "total": 2, "completed": 0, "percentage": 0 },
      "financing": { "total": 3, "completed": 1, "percentage": 33 },
      "carbon": { "total": 2, "completed": 0, "percentage": 0 },
      "intermediary_contact": { "total": 3, "completed": 2, "percentage": 67 }
    }
  }
}
```

---

### PATCH /action-plan/items/{item_id}

Met à jour une action.

**Auth**: Bearer token requis

**Request Body** (tous optionnels):
```json
{
  "status": "in_progress",
  "completion_percentage": 50,
  "due_date": "2026-05-01"
}
```

**Response 200**: ActionItem mis à jour

**Response 400**: Transition de statut invalide
```json
{
  "detail": "Transition invalide : completed → todo"
}
```

---

## Rappels

### POST /reminders/

Crée un rappel.

**Auth**: Bearer token requis

**Request Body**:
```json
{
  "action_item_id": "uuid",
  "type": "intermediary_followup",
  "message": "Relancer la SIB pour le dossier SUNREF",
  "scheduled_at": "2026-04-20T09:00:00Z"
}
```

**Response 201**: Reminder créé

---

### GET /reminders/upcoming

Prochains rappels non envoyés.

**Auth**: Bearer token requis

**Query params**:

| Param | Type | Défaut | Description |
|-------|------|--------|-------------|
| limit | integer | 10 | Nombre max |

**Response 200**:
```json
{
  "items": [
    {
      "id": "uuid",
      "type": "intermediary_followup",
      "message": "Relancer la SIB pour le dossier SUNREF",
      "scheduled_at": "2026-04-20T09:00:00Z",
      "sent": false,
      "action_item": {
        "id": "uuid",
        "title": "Prendre rendez-vous avec la SIB",
        "category": "intermediary_contact"
      }
    }
  ],
  "total": 3
}
```

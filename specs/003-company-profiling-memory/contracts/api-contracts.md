# API Contracts: 003-company-profiling-memory

**Date**: 2026-03-30

## REST Endpoints

### GET /api/company/profile

Retourne le profil entreprise de l'utilisateur connecte.

**Auth**: Bearer token (JWT)

**Response 200**:
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "company_name": "EcoPlast SARL",
  "sector": "recyclage",
  "sub_sector": "recyclage de plastique",
  "employee_count": 15,
  "annual_revenue_xof": 50000000,
  "city": "Abidjan",
  "country": "Cote d'Ivoire",
  "year_founded": 2018,
  "has_waste_management": true,
  "has_energy_policy": null,
  "has_gender_policy": null,
  "has_training_program": true,
  "has_financial_transparency": null,
  "governance_structure": null,
  "environmental_practices": "Tri selectif et recyclage PET",
  "social_practices": null,
  "notes": "L'entreprise travaille avec des cooperatives locales de collecte.",
  "created_at": "2026-03-30T10:00:00Z",
  "updated_at": "2026-03-30T14:30:00Z"
}
```

**Response 404**: Profil non trouve (pas encore cree)
```json
{
  "detail": "Profil entreprise non trouve."
}
```

---

### PATCH /api/company/profile

Mise a jour partielle du profil entreprise. Seuls les champs envoyes sont mis a jour.

**Auth**: Bearer token (JWT)

**Request Body** (tous les champs optionnels):
```json
{
  "company_name": "EcoPlast SARL",
  "sector": "recyclage",
  "employee_count": 20
}
```

**Response 200**: Le profil mis a jour (meme format que GET)

**Response 422**: Erreur de validation
```json
{
  "detail": [
    {
      "loc": ["body", "sector"],
      "msg": "Valeur invalide. Valeurs acceptees : agriculture, energie, recyclage, transport, construction, textile, agroalimentaire, services, commerce, artisanat, autre",
      "type": "value_error"
    }
  ]
}
```

---

### GET /api/company/profile/completion

Retourne le pourcentage de completion et les champs manquants par categorie.

**Auth**: Bearer token (JWT)

**Response 200**:
```json
{
  "identity_completion": 75.0,
  "esg_completion": 25.0,
  "overall_completion": 50.0,
  "identity_fields": {
    "filled": ["company_name", "sector", "sub_sector", "employee_count", "city", "country"],
    "missing": ["annual_revenue_xof", "year_founded"]
  },
  "esg_fields": {
    "filled": ["has_waste_management", "has_training_program"],
    "missing": ["has_energy_policy", "has_gender_policy", "has_financial_transparency", "governance_structure", "environmental_practices", "social_practices"]
  }
}
```

**Response 404**: Profil non trouve

---

## SSE Events (Chat Streaming)

### Event existant : token

```
event: token
data: {"content": "Voici mes recommandations..."}
```

### Nouvel event : profile_update

Emis quand le `profiling_node` extrait et applique des informations au profil.

```
event: profile_update
data: {"field": "sector", "value": "recyclage", "label": "Secteur"}
```

```
event: profile_update
data: {"field": "city", "value": "Abidjan", "label": "Ville"}
```

### Nouvel event : profile_completion

Emis apres les `profile_update` pour signaler la nouvelle completion.

```
event: profile_completion
data: {"identity_completion": 75.0, "esg_completion": 12.5, "overall_completion": 43.75}
```

## Schema Pydantic : ProfileExtraction

Retour de la chaine d'extraction structuree. Tous les champs sont optionnels — seuls les champs detectes avec confiance sont remplis.

```python
class ProfileExtraction(BaseModel):
    company_name: str | None = None
    sector: SectorEnum | None = None
    sub_sector: str | None = None
    employee_count: int | None = None
    annual_revenue_xof: int | None = None
    city: str | None = None
    country: str | None = None
    year_founded: int | None = None
    has_waste_management: bool | None = None
    has_energy_policy: bool | None = None
    has_gender_policy: bool | None = None
    has_training_program: bool | None = None
    has_financial_transparency: bool | None = None
    governance_structure: str | None = None
    environmental_practices: str | None = None
    social_practices: str | None = None
    notes: str | None = None
```

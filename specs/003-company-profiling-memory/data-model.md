# Data Model: 003-company-profiling-memory

**Date**: 2026-03-30

## Entites

### CompanyProfile

Table : `company_profiles`

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, default uuid4 | Identifiant unique |
| user_id | UUID | FK→users, UNIQUE, NOT NULL, CASCADE | Relation un-a-un avec User |
| company_name | VARCHAR(255) | nullable | Nom de l'entreprise |
| sector | ENUM | nullable, 11 valeurs | Secteur d'activite |
| sub_sector | TEXT | nullable | Sous-secteur libre |
| employee_count | INTEGER | nullable, >= 0 | Nombre d'employes |
| annual_revenue_xof | BIGINT | nullable, >= 0 | Chiffre d'affaires annuel en FCFA |
| city | VARCHAR(100) | nullable | Ville |
| country | VARCHAR(100) | default "Cote d'Ivoire" | Pays |
| year_founded | INTEGER | nullable, >= 1900 | Annee de creation |
| has_waste_management | BOOLEAN | nullable | Gestion des dechets en place |
| has_energy_policy | BOOLEAN | nullable | Politique energetique |
| has_gender_policy | BOOLEAN | nullable | Politique genre |
| has_training_program | BOOLEAN | nullable | Programme de formation |
| has_financial_transparency | BOOLEAN | nullable | Transparence financiere |
| governance_structure | TEXT | nullable | Description de la gouvernance |
| environmental_practices | TEXT | nullable | Pratiques environnementales |
| social_practices | TEXT | nullable | Pratiques sociales |
| notes | TEXT | nullable | Notes qualitatives libres |
| created_at | TIMESTAMP | NOT NULL, default now() | Date de creation |
| updated_at | TIMESTAMP | NOT NULL, default now(), auto-update | Date de derniere modification |

**Index** : UNIQUE sur `user_id`

### SectorEnum

Valeurs de l'enum `sector_type` :

```
agriculture, energie, recyclage, transport, construction,
textile, agroalimentaire, services, commerce, artisanat, autre
```

### Conversation (modification)

Ajout du champ `summary` a la table `conversations` existante :

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| summary | TEXT | nullable | Resume genere par le LLM a la cloture du thread |

## Relations

```
User (1) ──── (0..1) CompanyProfile
  │
  └── (1) ──── (*) Conversation
                   └── summary (nouveau champ)
```

- Un utilisateur a au maximum un profil entreprise
- Un profil est cree automatiquement a la premiere interaction (si inexistant)
- Les conversations existantes ne sont pas modifiees, seul le champ `summary` est ajoute

## ConversationState (LangGraph)

Enrichissement du TypedDict existant :

```
ConversationState:
  messages: list[BaseMessage]       # Existant (avec add_messages reducer)
  user_profile: dict | None         # Nouveau : profil entreprise serialise
  context_memory: list[str]         # Nouveau : 3 derniers resumes
  profile_updates: list[dict] | None  # Nouveau : extractions de la passe courante
```

- `user_profile` : charge depuis la BDD au debut de chaque invocation du graphe, injecte dans le prompt
- `context_memory` : les 3 derniers `summary` des conversations de l'utilisateur
- `profile_updates` : champs extraits par le profiling_node dans la passe courante (pour notifications SSE)

## Regles de validation

- `employee_count` : entier >= 0
- `annual_revenue_xof` : entier >= 0 (en FCFA, pas de decimales)
- `year_founded` : entre 1900 et l'annee courante
- `sector` : doit etre une valeur de l'enum `sector_type`
- `country` : defaut "Cote d'Ivoire" si non specifie

## Calcul de completion

### Identite & Localisation (seuil 70%)

8 champs : `company_name`, `sector`, `sub_sector`, `employee_count`, `annual_revenue_xof`, `year_founded`, `city`, `country`

- `country` a un defaut → toujours compte comme rempli
- Chaque champ rempli = 12.5%
- Seuil profilage guide : 70% ≈ 6 champs sur 8 remplis

### ESG (suivi separe)

8 champs : `has_waste_management`, `has_energy_policy`, `has_gender_policy`, `has_training_program`, `has_financial_transparency`, `governance_structure`, `environmental_practices`, `social_practices`

- Booleens : rempli si non-null (True OU False = rempli)
- Textuels : rempli si non-null et non-vide
- Chaque champ rempli = 12.5%

### Completion globale

La completion globale affichee = moyenne des deux :
`(identity_pct + esg_pct) / 2`

Le badge sidebar affiche ce pourcentage global. La page profil et les blocs progress affichent les deux categories separement.

## Transitions d'etat

### Profil
- **Vide** → premiere interaction → profil cree avec `country = "Cote d'Ivoire"`
- **Partiel** → messages avec infos extractibles → champs mis a jour incrementalement
- **Complet (100%)** → celebration visuelle (gauge) → pas de changement de comportement fonctionnel

### Conversation
- **Active** → pas de resume
- **Nouvelle conversation creee** → resume du thread precedent genere par le LLM
- **Resume stocke** → disponible dans `context_memory` des futures conversations

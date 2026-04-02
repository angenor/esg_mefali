# Data Model: 013-fix-multiturn-routing-timeline

**Date**: 2026-04-01

## Entites modifiees

### ConversationState (TypedDict existant)

**Fichier**: `backend/app/graph/state.py`

**Champs ajoutes**:

| Champ | Type | Default | Description |
|-------|------|---------|-------------|
| `active_module` | `str \| None` | `None` | Module specialiste actuellement actif. Valeurs : `null`, `esg_scoring`, `carbon`, `financing`, `application`, `credit`, `profiling`, `document`, `action_plan` |
| `active_module_data` | `dict \| None` | `None` | Donnees contextuelles du module actif : assessment_id, progression, derniere question |

**Champs existants impactes** (comportement modifie, pas de changement de type) :

| Champ | Impact |
|-------|--------|
| `_route_esg` | Defini par le routeur en priorite via `active_module` si module actif |
| `_route_carbon` | Idem |
| `_route_financing` | Idem |
| `_route_application` | Idem |
| `_route_credit` | Idem |
| `_route_action_plan` | Idem |

### active_module_data (structure interne)

Structure du dictionnaire selon le module actif :

**Pour esg_scoring** :
```
{
  "assessment_id": int,
  "current_criterion": str | None,
  "criteria_remaining": list[str],
  "criteria_evaluated": list[str]
}
```

**Pour carbon** :
```
{
  "assessment_id": int,
  "entries_collected": list[str],
  "current_category": str | None
}
```

**Pour financing** :
```
{
  "search_done": bool,
  "selected_fund_id": int | None,
  "interest_expressed": bool
}
```

**Pour application, credit, profiling, document** :
```
{
  "session_id": int | None
}
```

### TimelineBlockData (interface TypeScript existante)

**Fichier**: `frontend/app/types/richblocks.ts`

**Pas de modification de l'interface**. La normalisation se fait dans le composant avant le typage.

## Transitions d'etat

### Cycle de vie du module actif

```
null ──[routeur detecte intention]--> "esg_scoring" (ou autre module)
                                          │
                                          ├──[reponse utilisateur]--> reste "esg_scoring"
                                          │
                                          ├──[finalisation]--> null
                                          │
                                          ├──[changement de sujet vers autre module]--> "financing" (direct)
                                          │
                                          └──[changement de sujet general]--> null
```

### Regles de transition

1. `null → module` : Le routeur detecte une intention via classification normale (comportement actuel)
2. `module → module (meme)` : Le message est route vers le meme module (multi-tour)
3. `module → null` : Finalisation de session OU changement de sujet vers chat general
4. `module → autre module` : Transition directe sans passer par null (ex: carbone → financement)

## Aucune migration de base de donnees requise

Les champs `active_module` et `active_module_data` sont dans le state LangGraph (TypedDict en memoire), pas dans la base de donnees. Le checkpointer (MemorySaver) les persiste automatiquement.

# Data Model: Correction des 34 tests en échec

**Date**: 2026-04-02 | **Branch**: 017-fix-failing-tests

## Aucun changement de schéma BDD

Cette feature corrige uniquement des tests existants. Aucune migration, aucun nouveau modèle, aucune modification de schéma.

## Entités impliquées (lecture seule)

### ConversationState (TypedDict — 27 champs)

| Champ | Type | Défaut test |
|-------|------|-------------|
| messages | list (add_messages) | `[]` |
| user_id | str \| None | `"test-user-id"` |
| user_profile | dict \| None | `None` |
| context_memory | list[str] | `[]` |
| profile_updates | list[dict] \| None | `None` |
| profiling_instructions | str \| None | `None` |
| document_upload | dict \| None | `None` |
| document_analysis_summary | str \| None | `None` |
| has_document | bool | `False` |
| esg_assessment | dict \| None | `None` |
| _route_esg | bool | `False` |
| carbon_data | dict \| None | `None` |
| _route_carbon | bool | `False` |
| financing_data | dict \| None | `None` |
| _route_financing | bool | `False` |
| application_data | dict \| None | `None` |
| _route_application | bool | `False` |
| credit_data | dict \| None | `None` |
| _route_credit | bool | `False` |
| action_plan_data | dict \| None | `None` |
| _route_action_plan | bool | `False` |
| tool_call_count | int | `0` |
| active_module | str \| None | `None` |
| active_module_data | dict \| None | `None` |

### User (SQLAlchemy model)

Utilisé dans le fixture auth override. Champs minimum requis pour les tests:
- `id`: UUID
- `email`: str
- `is_active`: bool (True)

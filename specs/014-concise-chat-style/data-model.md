# Data Model: 014-concise-chat-style

**Date**: 2026-04-02

## Entites

Aucune nouvelle entite en base de donnees. Cette feature modifie uniquement le contenu des prompts systeme (texte statique).

## Constantes

### STYLE_INSTRUCTION

- **Type**: `str` (constante Python)
- **Emplacement**: `backend/app/prompts/system.py`
- **Contenu**: Bloc de texte contenant les regles de style concis, les interdictions et les exemples BON/MAUVAIS
- **Relations**: Importe par les 6 modules de prompts specialises (`esg_scoring.py`, `carbon.py`, `financing.py`, `credit.py`, `application.py`, `action_plan.py`)

## Points d'injection

| Prompt | Fichier | Fonction | Condition |
|--------|---------|----------|-----------|
| Chat general | `prompts/system.py` | `build_system_prompt()` | `user_profile` renseigne (>=2 champs) |
| ESG scoring | `prompts/esg_scoring.py` | `build_esg_prompt()` | Toujours (module post-profilage) |
| Carbone | `prompts/carbon.py` | `build_carbon_prompt()` | Toujours |
| Financement | `prompts/financing.py` | `build_financing_prompt()` | Toujours |
| Credit | `prompts/credit.py` | `build_credit_prompt()` | Toujours |
| Application | `prompts/application.py` | `build_application_prompt()` | Toujours |
| Plan d'action | `prompts/action_plan.py` | `build_action_plan_prompt()` | Toujours |

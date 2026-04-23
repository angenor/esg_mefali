---
title: 'DEF-BUG-011-1 — LANGUAGE_INSTRUCTION manquante dans les 6 builders spécialistes'
type: 'bugfix'
created: '2026-04-23'
status: 'done'
route: 'one-shot'
---

## Intent

**Problem:** BUG-011 a ajouté `LANGUAGE_INSTRUCTION` dans `build_system_prompt()` (system.py) mais les 6 builders spécialistes (esg_scoring, carbon, financing, application, credit, action_plan) construisaient leurs prompts indépendamment sans l'inclure, permettant à MiniMax de répondre en chinois sur ces modules.

**Approach:** Importer `LANGUAGE_INSTRUCTION` dans chaque builder et le prepend au string retourné avec le séparateur `"\n\n"`, identique au pattern de `build_system_prompt()`.

## Suggested Review Order

1. [system.py:3-8](../../../backend/app/prompts/system.py) — constante `LANGUAGE_INSTRUCTION` (référence)
2. [esg_scoring.py:94,111](../../../backend/app/prompts/esg_scoring.py) — import + return patché
3. [carbon.py:130,147](../../../backend/app/prompts/carbon.py) — import + return patché
4. [financing.py:95,112](../../../backend/app/prompts/financing.py) — import + return patché
5. [application.py:107,119](../../../backend/app/prompts/application.py) — import + return patché (sans guided_tour)
6. [credit.py:124,141](../../../backend/app/prompts/credit.py) — import + return patché
7. [action_plan.py:121,142](../../../backend/app/prompts/action_plan.py) — import + return patché
8. [test_language_instruction_all_builders.py](../../../backend/tests/test_prompts/test_language_instruction_all_builders.py) — 8 tests (startswith + count==1 + parametrized)
9. [golden/*.txt](../../../backend/tests/test_prompts/golden/) — 6 golden snapshots régénérés

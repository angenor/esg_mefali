---
title: 'BUG-011 — Fix langue française MiniMax post-tool calling'
type: 'bugfix'
created: '2026-04-23'
status: 'done'
route: 'one-shot'
---

## Intent

**Problem:** MiniMax (via OpenRouter) génère du chinois traditionnel dans ses réponses après l'exécution d'un tool LangGraph — l'instruction langue dans `BASE_PROMPT` est insuffisante pour forcer le français en post-ToolMessage.

**Approach:** Ajouter `LANGUAGE_INSTRUCTION` en tête absolue de `build_system_prompt()` et un reminder court dans `tool_instructions` de `chat_node`.

## Suggested Review Order

1. [LANGUAGE_INSTRUCTION constant](../../backend/app/prompts/system.py) — nouvelle constante prepend dans `build_system_prompt()`
2. [chat_node tool_instructions](../../backend/app/graph/nodes.py) — reminder langue ajouté en fin de la variable
3. [Regression test](../../backend/tests/test_system_prompt.py) — assert `"LANGUE OBLIGATOIRE"` dans le prompt
4. [Golden snapshot](../../backend/tests/test_prompts/golden/system.txt) — régénéré avec nouvelle tête
5. [Deferred work](deferred-work.md) — DEF-BUG-011-1 : builders spécialistes non patchés (hors scope)

# Research: Fix Tool Persistence & Routing Bugs

## Analyse des causes racines

### Bug 1 — ESG save_esg_criterion_score jamais appelé (Test 3.2)

**Decision**: Renforcer les tool_instructions dans `esg_scoring_node` et le prompt `esg_scoring.py`

**Rationale**: Deux incohérences identifiées :
1. Les `tool_instructions` injectées dans le node (nodes.py:602-615) listent `save_esg_criterion_score` mais PAS `batch_save_esg_criteria`. Le prompt statique (esg_scoring.py:61-65) mentionne batch_save dans une section "SAUVEGARDE PAR LOT" mais cette section est noyée après les instructions visuelles. Le LLM ne voit pas clairement qu'il doit appeler ce tool.
2. Le workflow (nodes.py:609-614) dit "Pour chaque critère évalué, appelle save_esg_criterion_score" mais c'est formulé comme un conseil, pas comme une obligation. Le test montre que le LLM met à jour le profil company au lieu d'appeler save_esg_criterion_score — il confond profilage ESG (champs has_waste_management du profil) et évaluation ESG (critères E1-E10 de l'assessment).

**Fix concret**:
- Ajouter `batch_save_esg_criteria` dans la liste des tools du node
- Ajouter une section "REGLE ABSOLUE" au début du tool_instructions : "Quand l'utilisateur répond à des questions ESG, tu DOIS appeler batch_save_esg_criteria ou save_esg_criterion_score. Ne JAMAIS répondre sans sauvegarder."
- Remonter la section "SAUVEGARDE PAR LOT" avant les instructions visuelles dans le prompt statique

**Alternatives rejetées**:
- Modifier le routing pour forcer le retour dans esg_scoring_node → Inutile, le routing fonctionne (test 3.1 passe), c'est le LLM qui ne call pas le tool une fois dans le bon node

---

### Bug 2 — save_emission_entry jamais appelé (Test 4.2)

**Decision**: Ajouter "REGLE ABSOLUE" dans les tool_instructions du carbon_node

**Rationale**: Les instructions actuelles (nodes.py:758-768) sont consultatives : "Quand l'utilisateur donne une consommation, appelle save_emission_entry". Le LLM calcule mentalement les émissions et les affiche dans le chat sans persister. Même pattern que le bug ESG.

**Fix concret**:
- Ajouter une section "REGLE ABSOLUE" dans carbon_node : "Quand l'utilisateur donne une consommation, tu DOIS appeler save_emission_entry AVANT de répondre. Ne JAMAIS calculer des émissions sans les sauvegarder."
- Ajouter dans le prompt carbone statique une instruction plus visible

**Alternatives rejetées**:
- Post-processing automatique pour détecter les calculs non persistés → Trop complexe, le fix prompt est suffisant

---

### Bug 3 — search_compatible_funds non appelé (Test 5.1)

**Decision**: Renforcer l'enforcement ET réduire les informations statiques sur les fonds dans le prompt

**Rationale**: Le prompt financing.py contient une section "BASE DE DONNEES DES FONDS" avec les noms des 12 fonds et 14 intermédiaires. Cela donne assez d'information au LLM pour répondre de mémoire. Les instructions "utilise TOUJOURS le tool" (nodes.py:869-876) sont présentes mais le LLM les ignore car il a déjà les données dans le prompt.

**Fix concret**:
- Retirer la liste détaillée des fonds du prompt statique (garder seulement "Tu as accès à une base de fonds verts via le tool search_compatible_funds")
- Renforcer l'instruction : "REGLE ABSOLUE : Ne cite JAMAIS un nom de fonds sans avoir d'abord appelé search_compatible_funds. Toute réponse sur les fonds DOIT être précédée d'un appel tool."

**Alternatives rejetées**:
- Garder les détails dans le prompt et espérer que le LLM appelle quand même le tool → C'est ce qui est en place et ça ne marche pas

---

### Bug 4 — Bloc gauge bloqué sur "Génération du graphique..." (Test 1.5)

**Decision**: Ajouter un fallback temporisé pour les blocs incomplets post-streaming

**Rationale**: Le `BlockPlaceholder` s'affiche quand `segment.isComplete === false`. Cela arrive quand le closing ``` n'est pas trouvé. Deux cas possibles :
1. Pendant le streaming SSE, le bloc est en cours de construction → Normal, le placeholder disparaît une fois le bloc complet
2. Après le streaming terminé, si le JSON est malformé ou le LLM n'a pas fermé le bloc → Le placeholder reste indéfiniment

L'investigation montre que `MessageParser.vue` utilise `!segment.isComplete` comme seule condition pour afficher le placeholder, sans considérer `props.isStreaming`. Quand le streaming est terminé et que le bloc est toujours incomplet, il faudrait tenter de le rendre quand même (fallback) au lieu de garder le placeholder.

**Fix concret**:
- Dans `MessageParser.vue`, ajouter une condition : si `!segment.isComplete && !isStreaming`, tenter de rendre le bloc avec le contenu disponible au lieu d'afficher le placeholder
- Ajouter un `BlockError` comme fallback si le contenu est invalide

**Alternatives rejetées**:
- Timer/timeout sur le placeholder → Mauvaise UX, le délai est arbitraire
- Forcer le LLM à toujours fermer les blocs → Pas fiable, les LLM peuvent tronquer

---

### Bug 5 — L'IA propose d'ajouter un site inexistant (Test 12.1)

**Decision**: Ajouter une instruction de correction dans le prompt système (system.py)

**Rationale**: Le prompt actuel dit "Ne repose JAMAIS une question dont la réponse est dans ce profil" (system.py:214-215) mais ne dit pas quoi faire quand l'utilisateur référence des données inexistantes. Le LLM, en mode "assistant serviable", propose naturellement d'ajouter le site au lieu de corriger l'utilisateur.

**Fix concret**:
- Ajouter dans `build_system_prompt()` une instruction : "Si l'utilisateur mentionne une entité (site, filiale, localisation) qui n'existe PAS dans son profil, corrige-le clairement : 'Votre profil ne contient pas de site à [X]. Vos données sont basées à [ville du profil].' Ne propose PAS d'ajouter l'entité sauf si l'utilisateur le demande explicitement."

**Alternatives rejetées**:
- Validation côté router pour détecter les références inexistantes → Over-engineering pour un fix prompt simple

---

## Synthèse des patterns identifiés

Le bug systémique a une cause commune : **les instructions tool calling dans les nodes sont formulées comme des conseils, pas comme des obligations**. Le pattern qui fonctionne (vu dans la branche 015 pour application/credit) est :
1. Section "REGLE ABSOLUE" en début des tool_instructions
2. Formulation impérative : "tu DOIS appeler", "JAMAIS répondre sans"
3. Réduction des informations statiques dans le prompt pour forcer la consultation tool

Ce pattern doit être appliqué uniformément aux 3 modules concernés (ESG, carbone, financement).

# Audit Rétrospectif — Spec 016 : Correction Persistence Tool Calling + Rendu Visuel

**Date d'audit** : 2026-04-16
**Auditeur** : Angenor (Project Lead) + assistant Amelia
**Spec** : [specs/016-fix-tool-persistence-bugs/](../../../specs/016-fix-tool-persistence-bugs/)
**Méthode** : rétrospective post-hoc sur spec-correctif
**Statut rétro** : ✅ Audité — 5 bugs chirurgicalement résolus, mais symptôme d'une fragilité systémique

---

## 1. Portée de la spec

**Spec-correctif** qui arrive **1 semaine après spec 015** pour fixer 5 bugs supplémentaires révélés par le plan de tests d'intégration :
- **US1 P1** : évaluation ESG — LLM mettait à jour le profil au lieu de sauvegarder les critères
- **US2 P1** : bilan carbone — `save_emission_entry` jamais appelé
- **US3 P2** : financement — `search_compatible_funds` ignoré, LLM répondait de mémoire (GCF, BOAD, FENU hallucinés au lieu de la BDD réelle SUNREF, FNDE, etc.)
- **US4 P3** : rendu gauge bloqué sur "Génération du graphique..."
- **US5 P3** : hallucination site inexistant (Yamoussoukro)

| Dimension | Livré |
|-----------|-------|
| Tâches | 25 / 25 `[X]` (100 %) |
| Discordance tasks↔code | 0 (fixes vérifiés) |
| User Stories | 5 (US1-US2 P1, US3 P2, US4-US5 P3) |
| Tests ajoutés | 13 backend + 3 frontend |
| Résultat backend (T022) | **867 passed, 33 failed (pré-existants)** |
| CLAUDE.md mention | non (spec 016 pas dans Recent Changes visibles) |

---

## 2. Ce qui a bien fonctionné

### 2.1 Diagnostic chirurgical par bug

- 5 bugs bien **distincts** (pas d'amalgame)
- Cause racine identifiée pour chacun :
  - US1/US2/US3 : prompts insuffisamment directifs (pattern identique spec 015)
  - US4 : logique conditionnelle incorrecte dans MessageParser (condition streaming vs complete)
  - US5 : instruction manquante dans `_format_profile_section`
- Fixes vérifiés en code :
  - `nodes.py:645, 939` : "REGLE ABSOLUE" dans tool_instructions ESG + carbon + financing ✅
  - `MessageParser.vue:34` : `!segment.isComplete && isStreaming` (le &&isStreaming manquait) ✅
  - `system.py:280-281` : *"Votre profil ne contient pas de site à [X]. Vos données sont basées à [ville]."* ✅

### 2.2 Parallélisation maximale

- 5 user stories **entièrement indépendantes** (fichiers différents ou sections différentes de nodes.py)
- 6 tests parallélisables (T003, T004, T008, T011, T016, T019)
- Pattern d'exécution optimale : `US1 → US2 → US3` séquentiel (même fichier) puis `US4 + US5` parallèles

### 2.3 Pattern "REGLE ABSOLUE" étendu

- Spec 015 avait introduit le pattern pour 3 prompts (application, credit, esg_scoring)
- Spec 016 l'étend aux **tool_instructions** des nœuds (carbon_node, financing_node) dans `nodes.py`
- Pattern cohérent : ROLE actif + OUTILS DISPONIBLES + REGLE ABSOLUE avec "INTERDIT"

### 2.4 Fix US3 structurel : supprimer la BDD hallucinable

- Avant : le prompt financing contenait la liste détaillée des 12 fonds → LLM la régurgitait de mémoire sans appeler le tool
- Après : prompt allégé, référence au tool `search_compatible_funds` uniquement
- **Leçon appliquée** : si le prompt contient de la donnée que le tool devrait retourner, le LLM zappe le tool. Supprimer la donnée du prompt **force** l'appel tool.

### 2.5 Non-régression validée

- T022 : 867 tests passés, 33 échoués (pré-existants)
- T024 : zéro régression introduite
- Spec ne touche pas les 33 échecs pré-existants (scope respecté)

### 2.6 US5 instruction simple et efficace

- 2 lignes dans `_format_profile_section` (system.py:280-281)
- Transforme une hallucination problématique en correction polie
- Exemple de fix minimal qui résout un UX problem

---

## 3. Ce qui a posé problème

### 3.1 🔴 SIGNAL SYSTÉMIQUE — 4 specs-correctif en 2 semaines (013, 015, 016, 017)

- **Timeline** :
  - Spec 012 (tool-calling) livrée
  - Spec 013 corrige routing multi-tour
  - Spec 015 corrige tool calling application/credit + timeout ESG
  - Spec 016 corrige tool calling ESG/carbon/financing **à nouveau**
  - Spec 017 (à auditer) corrige des tests qui échouent
- **Diagnostic** : le système LLM + prompts + tools est **fragile**. Chaque correction révèle un autre bug du même pattern.
- **Cause racine** : **absence de tests d'intégration E2E** qui testent le comportement LLM observé (pas juste le contenu des prompts)
  - Spec 015 a ajouté tests mais tests **unitaires** (string match)
  - Spec 016 même pattern
  - Aucun test de charge "un utilisateur complète vraiment une évaluation ESG et les critères sont en BDD"
- **Leçon** : un pattern qui accumule les correctifs mérite un **fix structurel** — pas plus de "REGLE ABSOLUE" empilées

### 3.2 🔴 33 tests pré-existants en échec = dette visible mais non adressée

- T022 mentionne explicitement : *"867 passed, 33 failed (pré-existants)"*
- Ces 33 échecs sont **connus** depuis avant spec 016
- Spec 016 déclare explicitement ne pas les traiter
- **Spec 017 a été créée pour ça** (`fix-failing-tests`)
- **Mais** : livrer une spec-correctif en laissant 33 tests en échec = signal de vélocité > qualité
- **Leçon** : une spec-correctif qui ignore des tests en échec pré-existants documente la fragilité globale du système

### 3.3 🟠 "REGLE ABSOLUE" copié-collé 5-6 fois désormais

- Spec 015 : injection dans 3 prompts (application, credit, esg_scoring)
- Spec 016 : injection dans **tool_instructions** des nœuds (carbon, financing) dans `nodes.py:645, 939`
- Pattern dupliqué **5-6 fois** entre prompts et tool_instructions
- **Sans factorisation** → chaque nouveau fix = duplication additionnelle
- **Consolidation avec spec 014 §3.2 et spec 015 §3.2** : framework d'injection d'instructions manquant

### 3.4 🟠 Cause racine US1 mal diagnostiquée dans la spec

- Spec dit : *"Actuellement, l'assistant met à jour le profil company au lieu de sauvegarder les critères d'évaluation"*
- C'est **surprenant** : comment le LLM confond-il `update_company_profile` et `save_esg_criterion_score` ?
- **Hypothèse non documentée** : le `PROFILING_TOOLS` est bindé sur `chat_node`, pas sur `esg_scoring_node` — donc si le routing multi-tour (spec 013) échoue ponctuellement, le LLM retombe dans chat_node qui a `update_company_profile`
- **Cause racine profonde** : couplage routing spec 013 ↔ tool binding
- **Fix spec 016** : prompt plus directif — mais si le routing redescend dans chat_node, le prompt ESG n'est pas appliqué
- **Leçon** : un fix de symptôme sans diagnostic root cause risque de laisser le bug sous-jacent

### 3.5 🟠 US4 gauge : fix MessageParser, pas GaugeBlock

- FR-006 : *"Le composant gauge du frontend DOIT rendre un visuel interactif sans rester bloqué sur 'Génération du graphique...'"*
- **Fix appliqué** : `MessageParser.vue:34` modifie la condition d'affichage du placeholder
- Logique avant : "bloc incomplet → placeholder"
- Logique après : "bloc incomplet ET streaming en cours → placeholder"
- **Mais** : le GaugeBlock lui-même peut avoir des bugs de rendu (JSON malformé, valeur invalide) non traités
- **Impact** : le placeholder disparaît mais le gauge peut afficher vide si le JSON est corrompu
- **Leçon** : un fix conditionnel d'affichage ne remplace pas un fix de robustesse du composant

### 3.6 🟡 Test T019 "prompt contient instruction de correction"

- T019 : *"vérifier que le prompt système contient l'instruction de correction"*
- Test **unité** : vérifie la string `"corrige-le clairement"` dans `_format_profile_section`
- **Mais** : rien ne teste que le LLM **applique** cette correction
- Test golden "envoyer 'bilan de Yamoussoukro' et vérifier que le LLM dit 'pas de données pour Yamoussoukro'" manque
- **Cohérent avec la dette P3 #43** (tests d'intégration comportement LLM)

### 3.7 🟡 Pas de suivi des 5 bugs dans un tableau de bord

- Chaque bug est fixé individuellement, mais aucun **dashboard** ne suit "combien de bugs ESG/carbon/financing/gauge reviennent ?"
- Sans métrique, impossible d'anticiper la prochaine spec-correctif
- **Leçon** : après 2 specs-correctif sur le même pattern (015 + 016), introduire un dashboard bugs par module

### 3.8 🟡 Clarifications absentes

- Spec 016 n'a **pas de section "Clarifications"** (contrairement aux specs 003, 005, 012, 014)
- **Aucune question de clarification** n'a été posée avant l'implémentation
- **Risque** : les hypothèses implicites (ex: "REGLE ABSOLUE suffit à forcer le tool") passent sans challenge
- **Leçon** : les spec-correctif bénéficieraient aussi d'une session de clarification (hypothèses root cause, impact des fix)

---

## 4. Leçons transversales

1. **Pattern répété de bugs = fix structurel nécessaire** — pas "plus de REGLE ABSOLUE".
2. **Tests en échec pré-existants = dette visible** — documenter explicitement et planifier leur résolution.
3. **Framework d'injection d'instructions** (dette transverse avec specs 014, 015, 016).
4. **Root cause analysis obligatoire** dans les specs-correctif (hypothèse + preuve).
5. **Fix conditionnel d'affichage ≠ robustesse composant** — ne pas se contenter du symptôme.
6. **Tests golden** pour les comportements LLM — string match insuffisant.
7. **Dashboard bugs par module** après 2+ specs-correctif.
8. **Clarifications obligatoires même pour spec-correctif** (challenger les hypothèses root cause).

---

## 5. Actions résiduelles retenues

| # | Action | Priorité | Source |
|---|--------|----------|--------|
| 1 | **Investigation root cause US1** : pourquoi le LLM confond `update_company_profile` et `save_esg_criterion_score` ? (couplage routing spec 013 ↔ tool binding spec 012) | P2 | §3.4 |
| 2 | Robustesse `GaugeBlock` : fallback sur JSON malformé / valeur invalide | P3 | §3.5 |
| 3 | Dashboard bugs par module (métrique bugs ESG/carbon/financing/gauge) | P3 | §3.7 |
| 4 | Tests golden pour les comportements LLM (spec 016 US1/US2/US3/US5) | P3 | §3.6 (consolidation avec P3 #43 spec 015) |

**Actions déjà en place** :
- ✅ "REGLE ABSOLUE" dans tool_instructions (carbon, financing, esg)
- ✅ MessageParser fix conditional streaming/complete
- ✅ Instruction correction dans `_format_profile_section`
- ✅ 13 nouveaux tests + 3 frontend, zéro régression introduite

**Consolidation avec autres audits** :
- §3.1 signal systémique + §3.3 pattern REGLE ABSOLUE dupliqué → consolider avec spec 014 §3.2 (framework injection) + spec 015 §3.2
- §3.2 tests pré-existants en échec → adressé par spec 017 (à auditer)

---

## 6. Verdict

**Spec 016 est un correctif P1/P2/P3 bien exécuté** — 5 bugs distincts résolus, 13 tests ajoutés, zero régression. Les fixes vérifiés en code fonctionnent.

**MAIS** : c'est la **2ème spec-correctif en 2 semaines** sur le même pattern (tool calling + prompts insuffisamment directifs). C'est un **signal systémique** : le système LLM + tools + prompts est fragile et chaque correction révèle de nouveaux bugs du même type. Le pattern "REGLE ABSOLUE" est désormais dupliqué 5-6 fois.

**33 tests pré-existants en échec** (T022) sont une dette visible non adressée par spec 016 — spec 017 est créée pour ça.

**Recommandation** :
1. Acter que le pattern actuel "prompt directif + REGLE ABSOLUE" a atteint ses limites
2. Investigation root cause **US1** (couplage routing/tool binding) prioritaire
3. Mettre en place **tests d'intégration E2E** pour les comportements LLM (dette P3 récurrente) — sinon la spec 018 ou future reviendra avec les mêmes bugs
4. Framework d'injection d'instructions (dette P3 #38, #42) pour éviter la 6ème duplication

La spec en elle-même est **saine**. C'est le pattern accumulé de spec-correctifs qui pose question.

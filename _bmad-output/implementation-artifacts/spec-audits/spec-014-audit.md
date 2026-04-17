# Audit Rétrospectif — Spec 014 : Style de Communication Concis

**Date d'audit** : 2026-04-16
**Auditeur** : Angenor (Project Lead) + assistant Amelia
**Spec** : [specs/014-concise-chat-style/](../../../specs/014-concise-chat-style/)
**Méthode** : rétrospective post-hoc + vérification patterns BMAD ultérieurs
**Statut rétro** : ✅ Audité — pattern devenu référence pour 2 features BMAD, mais couplage fragile

---

## 1. Portée de la spec

**Spec-style** (pas de logique métier, pas de BDD). Ajoute un bloc d'instructions `STYLE_INSTRUCTION` au prompt système pour imposer des réponses concises (max 2-3 phrases après un bloc visuel, pas de politesse, pas de récapitulatif). Injection dans 6 prompts spécialisés + chat général conditionnel.

| Dimension | Livré |
|-----------|-------|
| Tâches | 22 / 22 `[x]` (100 %) |
| Discordance tasks↔code | 0 — toutes les injections vérifiées par grep |
| User Stories | 3 (US1-US2 P1, US3 P2) |
| Clarifications | 1 (exception onboarding pour les premières interactions) |
| Nouveaux fichiers | 1 (`test_style_instruction.py`) |
| Fichiers modifiés | 7 (`system.py` + 6 prompts spécialisés) |
| CLAUDE.md mentionne | "STYLE_INSTRUCTION injectée dans les 6 modules spécialisés + conditionnelle dans le chat général (post-onboarding)" |

---

## 2. Ce qui a bien fonctionné

### 2.1 Implémentation chirurgicale et verifiable

- **Grep code actuel** confirme les 6 imports et concaténations :
  - `esg_scoring.py:94-103` ✅
  - `carbon.py:131-140` ✅
  - `financing.py:96-105` ✅
  - `credit.py:125-134` ✅
  - `application.py:104-113` ✅
  - `action_plan.py:122-135` ✅
- `system.py:80` définit `STYLE_INSTRUCTION` (constante module-level)
- `system.py:214` injection conditionnelle dans `build_system_prompt` pour chat général
- **Pattern DRY exemplaire** : une constante, sept imports, zéro duplication

### 2.2 Exception onboarding bien cadrée (FR-010)

- Helper `_has_minimum_profile(profile: dict) -> bool` (system.py:163)
- Règle claire : >= 2 champs du profil → onboarding terminé → style concis activé
- Évite le style sec pour un utilisateur qui découvre la plateforme
- Clarification Q1 documentée avant implémentation (bon pattern speckit)

### 2.3 Spec-style comme pattern réutilisable

- **Feature BMAD 018 (interactive-widgets)** a copié le pattern → `WIDGET_INSTRUCTION`
- **Feature BMAD 019 (guided-tour) story 6.2** a copié le pattern → `GUIDED_TOUR_INSTRUCTION`
- CLAUDE.md Recent Changes confirme : *"Pattern identique à WIDGET_INSTRUCTION (feature 018) et STYLE_INSTRUCTION (feature 014)"*
- **Spec 014 a posé le standard** pour les instructions transverses injectées dans tous les nœuds

### 2.4 TDD respecté sur un micro-scope

- 8 tests (T004-T007 US1, T014-T016 US2, T018 US3)
- Test d'exhaustivité : `test_style_instruction_in_all_specialized_prompts` (T006)
- Test de contenu : `test_style_instruction_contains_rules` (T018)
- Couverture complète pour une feature de 22 tâches

### 2.5 Exemples BON/MAUVAIS dans le prompt (FR-008)

- Le prompt inclut des contrastes concrets pour guider le LLM
- Pattern qui améliore significativement la fidélité à l'instruction

---

## 3. Ce qui a posé problème

### 3.1 🟠 Couplage fragile `STYLE_INSTRUCTION` ↔ `GUIDED_TOUR_INSTRUCTION`

- **Dette documentée dans `_bmad-output/implementation-artifacts/deferred-work.md`** :
  > *"Couplage STYLE_INSTRUCTION / GUIDED_TOUR_INSTRUCTION : même branche conditionnelle `_has_minimum_profile` dans `build_system_prompt`. Un futur changement de seuil du style concis déplacera silencieusement le guidage."*
- `system.py:213-214` :
  ```python
  if user_profile and _has_minimum_profile(user_profile):
      sections.append(STYLE_INSTRUCTION)
      # GUIDED_TOUR_INSTRUCTION ajouté ici par spec 019 story 6.2
  ```
- Feature 019 a **réutilisé la même branche** au lieu de créer son propre helper
- **Impact** : modifier le seuil de `_has_minimum_profile` (ex: 2 → 3 champs) affecte **silencieusement** le guidage alors que l'intention était style only
- **Leçon** : les patterns réutilisables gagnent à avoir un **helper dédié par concern** (ex: `_should_inject_style()`, `_should_inject_guided_tour()`) plutôt qu'une branche conditionnelle partagée

### 3.2 🟡 Spec n'a pas anticipé la généralisation du pattern

- Spec 014 définit `STYLE_INSTRUCTION` comme une constante unique
- Features 018 + 019 ont reproduit le pattern par copier-coller (avec variations)
- **Pas de framework d'injection d'instructions** — chaque nouveau pattern duplique la logique
- **Leçon** : dès qu'une spec pose un pattern qui est *évidemment* réutilisable (injection d'instruction dans N prompts), abstraire dès le départ :
  ```python
  INSTRUCTION_REGISTRY = {
      "style": STYLE_INSTRUCTION,
      "widget": WIDGET_INSTRUCTION,
      "guided_tour": GUIDED_TOUR_INSTRUCTION,
  }
  def build_prompt(base, instructions: list[str], user_profile: dict) -> str:
      ...
  ```

### 3.3 🟡 Mesurabilité des SC faible

- **SC-005** : *"Le temps de lecture moyen d'une réponse de l'assistant diminue"* — pas de mesure instrumentée
- **SC-003** : *"Les confirmations tiennent en 1 phrase"* — pas de validation automatique (pas de test qui compte les phrases)
- **SC-004** : *"Aucune réponse ne commence par une formule de politesse décorative"* — pas de test
- Les SC sont mesurables *en théorie* mais aucune instrumentation en prod
- **Leçon** : pour les specs-style, les SC doivent avoir des tests de conformité (regex sur les sorties, longueur moyenne, etc.) — sinon le style dérive silencieusement au fil des évolutions du prompt

### 3.4 🟡 Pas de métrique de dérive du style

- Si le LLM tourne avec un nouveau modèle (ex: upgrade Claude 3.5 → 4), le respect du style peut baisser
- Pas de test de régression "le résumé ne commence pas par 'Je suis ravi'"
- Les specs 015/016/017 ont modifié les prompts sans s'assurer que STYLE_INSTRUCTION est toujours consommé correctement
- **Leçon** : les comportements de style méritent un test périodique avec un jeu de fixtures (conversations golden)

### 3.5 🟡 `_has_minimum_profile` : seuil magique = 2

- Le nombre "2 champs" est dans le code sans justification documentée
- Pourquoi pas 3 ? Pourquoi pas "secteur obligatoire" ?
- La logique est simple mais le chiffre magique n'est pas dans un config/constant
- **Leçon** : les seuils métier doivent être nommés (`MINIMUM_PROFILE_FIELDS_FOR_STYLE = 2`) avec commentaire de justification

### 3.6 🟡 STYLE_INSTRUCTION hard-codé côté backend

- Impossible d'A/B tester un style alternatif sans déploiement
- Pas de mécanisme "user X a un style concis, user Y a un style verbose"
- Pas de personnalisation par user (ex: préférence "style expert" vs "style débutant")
- **Leçon** : pour un produit SaaS qui doit s'adapter aux publics, les instructions de style devraient être configurables par user/workspace

---

## 4. Leçons transversales

1. **Helper dédié par concern** — éviter le couplage par branche conditionnelle partagée.
2. **Anticiper la réutilisabilité** — un pattern évident mérite une abstraction dès la première spec.
3. **Tests de conformité pour specs-style** — sans mesure, le style dérive au fil des upgrades LLM/prompts.
4. **Fixtures golden** pour tests de régression comportementale.
5. **Seuils magiques = constantes nommées** avec justification.
6. **Instructions de style configurables** (A/B testing, préférences user).

---

## 5. Actions résiduelles retenues

| # | Action | Priorité | Source |
|---|--------|----------|--------|
| 1 | **Extraire helper dédié `_should_inject_guided_tour()`** (découpler de `_has_minimum_profile`) | P3 | §3.1 (déjà dans deferred-work) |
| 2 | Framework d'injection d'instructions (registry + builder unifié) | P3 | §3.2 |
| 3 | Tests de conformité au style sur fixtures golden (SC-003, SC-004, SC-005) | P3 | §3.3 |
| 4 | Constante nommée `MINIMUM_PROFILE_FIELDS_FOR_STYLE = 2` | P3 | §3.5 |
| 5 | Instructions de style configurables par user (prefs `style: concise\|verbose`) | P3 | §3.6 |

**Actions déjà en place** :
- ✅ `STYLE_INSTRUCTION` définie et injectée dans 6 prompts + chat conditionnel
- ✅ Exception onboarding (`_has_minimum_profile`)
- ✅ 8 tests de conformité basique
- ✅ Pattern adopté par features 018 et 019

**Consolidation avec autres audits** :
- §3.1 couplage `_has_minimum_profile` → couvert par la dette deferred-work (à ajouter en P3)

---

## 6. Verdict

**Spec 014 est une micro-spec parfaitement exécutée** — 22 tâches, 7 fichiers modifiés, 8 tests, pattern DRY exemplaire. Elle a posé le **standard d'injection d'instructions transverses** pour le projet : features BMAD 018 (widgets) et 019 (guided tour) ont reproduit le pattern.

**Note importante** (mentionnée par Angenor) : le style concis a été **étendu via BMAD** — `WIDGET_INSTRUCTION` (feature 018) et `GUIDED_TOUR_INSTRUCTION` (feature 019) sont des patterns dérivés. Spec 014 reste **active et opérationnelle** dans les 6 prompts spécialisés + chat conditionnel.

La dette principale est **§3.1 le couplage fragile** entre les 3 instructions via `_has_minimum_profile` — dette **déjà documentée dans deferred-work.md** pour spec 019. Un changement de seuil du style affecte silencieusement le guidage. Un helper par concern résout proprement.

Les autres dettes sont **opérationnelles** (mesurabilité des SC, configurabilité) — toutes P3.

**Recommandation** : spec 014 reste une **référence pour les micro-specs de style/prompt engineering**. Pattern à reproduire pour toute instruction transverse. La leçon : dès la 2ème instruction, abstraire le pattern en registry + builder unifié (dette §3.2 à ouvrir si une 4ème instruction est prévue).

# Audit Rétrospectif — Spec 017 : Correction des 34 Tests en Échec

**Date d'audit** : 2026-04-16
**Auditeur** : Angenor (Project Lead) + assistant Amelia
**Spec** : [specs/017-fix-failing-tests/](../../../specs/017-fix-failing-tests/)
**Méthode** : rétrospective post-hoc sur spec-nettoyage
**Statut rétro** : ✅ Audité — spec-nettoyage exemplaire, diagnostic en 5 causes racines

---

## 1. Portée de la spec

**Spec-nettoyage** qui adresse **les 34 tests pré-existants en échec** documentés dans `failing-tests-audit.md`. Pas de nouvelle fonctionnalité — uniquement des corrections de tests. Répond directement à la dette visible dans spec 016 T022 (*"867 passed, 33 failed (pré-existants)"*).

| Dimension | Livré |
|-----------|-------|
| Tâches | 14 / 14 `[x]` (100 %) |
| Discordance tasks↔code | 0 (fixtures vérifiés dans `conftest.py:83, 101`) |
| User Stories | 5 (US1-US2 P1, US3-US4 P2, US5 P3) |
| Tests corrigés | 34 → 0 (SC-001) |
| Résultat final | **907/907 pass, zero régression** (T013) |
| Code production modifié | **0** (uniquement fichiers de test) |

---

## 2. Ce qui a bien fonctionné

### 2.1 Diagnostic en 5 causes racines distinctes

- Les 34 tests en échec **regroupés par root cause**, pas par module :
  - **15 tests** (44 %) : auth 401 → `@patch` au lieu de `dependency_overrides`
  - **7 tests** (21 %) : state conversationnel incomplet → KeyError
  - **3 tests** : Form vs JSON body
  - **1 test** : mock type (MagicMock au lieu d'AIMessage)
  - **6 tests** : dépendance WeasyPrint (bibliothèques système C)
- **Excellent diagnostic** — éviter de traiter 34 cas séparément
- **Leçon méthodologique** : regrouper les bugs par cause racine > par module pour optimiser le nombre de fixes

### 2.2 Fixtures partagés réutilisables

- `backend/tests/conftest.py:83` : `override_auth` via `app.dependency_overrides[get_current_user]`
  - Yield + cleanup automatique
  - Pattern FastAPI natif (bien meilleur que `@patch`)
- `backend/tests/conftest.py:101` : `make_conversation_state(**overrides)` avec 27 clés par défaut
  - Accepte des overrides par kwargs
  - Résout le problème "nouveau champ ajouté au state → tests cassés"
- **Bénéfice** : 22/34 tests corrigés par 2 fixtures → gain de temps futur sur chaque nouveau test

### 2.3 Parallélisation maximale

- T003/T004/T005 (auth 15 tests) : parallélisables (3 fichiers différents)
- T006/T007 (state 7 tests) : parallélisables
- US3/US4/US5 **indépendants** (pas de dépendance sur les fixtures)
- T010/T011 (WeasyPrint) : parallélisables
- Exécution optimale : 5 agents simultanés après Phase 1

### 2.4 Pattern `@pytest.mark.usefixtures`

- Usage idiomatique pour appliquer `override_auth` sans pollution du signature des tests
- Évite la duplication `def test_X(override_auth, ...)` × 15
- Pattern DRY + pythonic

### 2.5 Mock `patch.dict(sys.modules)` pour WeasyPrint

- Technique avancée mais cohérente avec la portabilité CI/CD
- Évite de requérir Cairo/Pango/GDK-Pixbuf sur les runners CI
- **Leçon** : mocker les dépendances système dès le départ (pas seulement les services applicatifs)

### 2.6 SC-002 validé : 907/907 tests pass

- Objectif **atteint** (zero échec, zero régression)
- Suite de tests stable pour la première fois depuis spec 013
- Base saine pour toutes les features futures

### 2.7 Aucun code de production modifié

- Les fixes sont **100 % dans les tests** → risque nul de régression fonctionnelle
- Les 867 tests précédemment passants continuent à passer
- Pattern de **spec-nettoyage propre** : séparer clairement "corrections tests" vs "corrections code"

---

## 3. Ce qui a posé problème

### 3.1 🔴 SIGNAL SYSTÉMIQUE — 4ᵉ spec-correctif en 2 semaines

- **Timeline rappel** : 012 (tool-calling) → 013 (fix routing) → 015 (fix timeout ESG) → 016 (fix persistence) → 017 (fix tests)
- **5 specs de 2 semaines à corriger des bugs** issus des fondations (spec 012)
- Spec 017 est le **symptôme** d'une absence de test d'intégration robuste **depuis spec 012**
- Les 34 tests en échec étaient **accumulés depuis plusieurs semaines** — certains datent probablement des specs 009-011
- **Impact** : chaque PR passait avec "907 passed, 34 failed (known)" — tolérance à la dette normalisée
- **Leçon** : interdire le merge avec des tests en échec connus — mettre en place CI qui refuse `main` si failures > 0

### 3.2 🟠 Pas de nouveaux tests anti-régression

- Les 5 causes racines corrigées n'ont pas de **test qui vérifie qu'elles ne reviennent pas**
- Ex: si un futur développeur ajoute un nouveau endpoint financing et oublie `override_auth`, pas d'alerte
- Pas de linter custom "tous les tests API doivent utiliser override_auth"
- **Leçon** : après un nettoyage massif, ajouter des **tests méta** ou des linters pour détecter les régressions du pattern

### 3.3 🟠 34 tests accumulés = symptôme de manque de discipline

- La dette de tests s'est accumulée sur plusieurs semaines avant que spec 017 soit créée
- Cela suggère que les PR mergent sans valider la suite de tests localement
- Ou que la CI accepte des tests en échec (soft-fail ?)
- **Leçon** : politique "zero failing tests on main" doit être CI-enforced, pas juste culturelle

### 3.4 🟡 Catégorie "WeasyPrint" révèle dette d'environnement

- Si certains tests requièrent des lib système C, l'environnement de test n'est pas reproductible
- Le mock est un fix pragmatique mais masque un problème : les dépendances Python du backend ne sont pas isolées
- **Alternative** : conteneur Docker de tests avec toutes les deps système (plus lourd mais reproductible)
- **Leçon** : dépendance à des lib système = documenter explicitement (requirements-system.txt ?) ou Dockeriser les tests

### 3.5 🟡 `make_conversation_state` avec 27 clés = fragilité

- Le helper duplique la **structure** du `ConversationState` TypedDict
- Si `ConversationState` ajoute une 28ème clé, `make_conversation_state` doit être mis à jour manuellement
- Pas de **sync automatique** entre le state réel et le helper
- **Alternative** : utiliser `ConversationState.__annotations__` pour générer les defaults dynamiquement
- **Leçon** : les helpers de test qui dupliquent une structure production gagnent à être générés depuis la source de vérité

### 3.6 🟡 Pas de métrique sur le temps des tests

- Les 907 tests passent mais combien de temps prennent-ils ?
- Est-ce que les fixtures partagés ajoutent de la latence ?
- Pas de budget temps pour la suite complète (ex: "doit passer en < 5 min en CI")
- **Leçon** : les fixtures réutilisables doivent être profilés (coût d'initialisation)

### 3.7 🟡 Test 3.4 `test_application_node_returns_messages` : 1 seul test concerné

- US4 traite **un seul test** avec un mock mal construit
- Soupçon : d'autres tests similaires pourraient avoir le même problème latent
- Pas d'audit proactif "tous les tests qui mockent LLM utilisent-ils AIMessage + AsyncMock ?"
- **Leçon** : quand une cause racine est identifiée, chercher activement d'autres occurrences (grep pattern)

---

## 4. Leçons transversales

1. **Regrouper les bugs par cause racine** > par module — minimise le nombre de fixes.
2. **Fixtures partagés via `conftest.py`** > `@patch` local pour FastAPI.
3. **`dependency_overrides` > `@patch`** pour l'auth (idiomatique FastAPI).
4. **Interdire CI merge avec tests en échec connus** — pas de "known failures".
5. **Tests méta / linters** après un nettoyage massif pour détecter les régressions de pattern.
6. **Helpers qui dupliquent une structure production** → générer dynamiquement (`__annotations__`).
7. **Mock dépendances système dès le départ** (WeasyPrint, Tesseract, etc.) pour portabilité CI.
8. **Budget temps** pour la suite de tests + profiling.
9. **Grep actif** quand une cause racine est identifiée (chercher autres occurrences).

---

## 5. Actions résiduelles retenues

| # | Action | Priorité | Source |
|---|--------|----------|--------|
| 1 | **Politique CI "zero failing tests on main"** (refuser merge si failures > 0) | P2 | §3.1, §3.3 |
| 2 | Linter custom "tous les tests API utilisent `override_auth`" | P3 | §3.2 |
| 3 | `make_conversation_state` dérivé de `ConversationState.__annotations__` | P3 | §3.5 |
| 4 | Dockeriser les tests (conteneur avec deps système : Cairo/Pango/Tesseract) | P3 | §3.4 |
| 5 | Budget temps + profiling suite de tests | P3 | §3.6 |
| 6 | Audit proactif "autres mocks LLM avec MagicMock au lieu d'AIMessage" | P3 | §3.7 |

**Actions déjà en place** :
- ✅ `override_auth` fixture (conftest.py:83)
- ✅ `make_conversation_state` helper (conftest.py:101)
- ✅ 5 causes racines documentées dans `failing-tests-audit.md`
- ✅ 907/907 tests pass, zero régression
- ✅ Aucun code de production modifié

**Consolidation avec autres audits** :
- §3.1 signal systémique → dette cross-spec "fragilité du système LLM+tools" déjà documentée dans spec 016 §3.1
- §3.2 linter custom → consolider avec la famille "tests d'intégration E2E comportement LLM" (P3 #43, #53)

---

## 6. Verdict

**Spec 017 est une spec-nettoyage exemplaire** — diagnostic en 5 causes racines distinctes, 2 fixtures partagés qui corrigent 22/34 tests, fixes ciblés pour les 12 restants, **zero code de production modifié**, **907/907 tests pass**, zero régression.

Elle **rétablit la santé de la suite de tests** après 4 semaines d'accumulation de dette (specs 012-016). C'est la **base saine** sur laquelle spec 018 (widgets interactifs) peut construire sans hériter de bugs latents.

**Signal important** : la nécessité même de spec 017 est un symptôme — la dette de tests ne s'accumule pas par accident, elle accumule parce que la CI accepte des échecs. **Action P2 prioritaire** : politique CI "zero failing tests on main".

**Recommandation** : spec 017 doit servir de **référence pour toute spec-nettoyage** future. Pattern à reproduire : diagnostic root cause → fixtures partagés → fixes par batch → validation globale → zero régression.

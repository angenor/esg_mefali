# Audit Rétrospectif — Spec 009 : Générateur de Dossiers de Candidature

**Date d'audit** : 2026-04-16
**Auditeur** : Angenor (Project Lead) + assistant Amelia
**Spec** : [specs/009-fund-application-generator/](../../../specs/009-fund-application-generator/)
**Méthode** : rétrospective post-hoc + audit-tasks-discordance
**Statut rétro** : ⚠️ Dettes lourdes (FR-005 RAG non implémenté malgré spec explicite)

---

## 1. Portée de la spec

Génération automatique de dossiers de candidature adaptés au destinataire : fonds direct (institutionnel), banque partenaire (bancaire), agence d'implémentation (développement), développeur projets carbone (technique). Export PDF/Word. Fiche de préparation intermédiaire. Simulateur financier. Statuts enrichis.

| Dimension | Livré |
|-----------|-------|
| Tâches | 57 / 62 `[x]` (91,9 %) — **Phase 12 Polish non marquée** (T058-T062 `[ ]`) |
| Discordance tasks↔code | 0 (tous les fichiers cités existent) |
| User Stories | 9 (US1-US2 P1, US3-US4/US6-US7 P2, US5/US8-US9 P3) |
| target_types | 4 (fund_direct, intermediary_bank, intermediary_agency, intermediary_developer) |
| Tools LangChain | 6 (`APPLICATION_TOOLS`) |
| Tests backend | 7 fichiers (test_service, test_router, test_export, test_simulation, test_prep_sheet, test_templates, test_node) |
| Nouveau modèle | `FundApplication` avec JSONB denses (sections, checklist, intermediary_prep, simulation) |

---

## 2. Ce qui a bien fonctionné

### 2.1 Architecture multi-templates cohérente

- 4 target_types avec 4 templates différents (`templates.py`)
- `determine_target_type` (service.py:35) avec mapping `IntermediaryType` → `TargetType` — pattern propre
- `accredited_entity` et `national_agency` fallback sur `intermediary_agency` — gestion gracieuse des cas non standards

### 2.2 Couverture de tests solide (contraste avec spec 008)

- **7 fichiers de test** : test_service, test_router, test_export, test_simulation, test_prep_sheet, test_templates, test_node
- Chaque composant clé a son test dédié (service, router, export PDF/Word, simulation, prep sheet, templates, LangGraph node)
- **Bien meilleur que spec 008** (où 5 tests critiques manquaient)

### 2.3 Validation des transitions de statut

- `VALID_TRANSITIONS` (service.py:139) : matrice de transitions autorisées ✅
- Cycle de vie enrichi : draft → preparing_documents → in_progress → review → ready_for_intermediary → submitted_to_intermediary → submitted_to_fund → under_review → accepted | rejected
- FR-010 correctement implémenté

### 2.4 6 tools LangChain exposés

- `APPLICATION_TOOLS` : create_fund_application, generate_application_section, update_application_section, get_application_checklist, simulate_financing, export_application
- LLM peut orchestrer toute la gestion de dossier depuis le chat
- Pattern cohérent avec spec 005/007/008

### 2.5 Stack d'export réutilisée

- WeasyPrint (PDF) + python-docx (Word) + Jinja2 (template HTML)
- Réutilisation intelligente du pattern spec 006 (rapports ESG)
- 2 templates : `application_export.html` + `prep_sheet.html`

### 2.6 Différenciation fund_direct vs intermediary_bank

- SC-002 testable : vocabulaire et structure différents (bancaire vs institutionnel)
- Checklist différenciée (documents financiers vs documents d'impact)
- Pattern différenciant de la plateforme

---

## 3. Ce qui a posé problème

### 3.1 🔴 DETTE MAJEURE — FR-005 RAG documentaire **non implémenté**

- **FR-005** : *"generer ou regenerer individuellement chaque section d'un dossier, en exploitant les documents uploades et le profil entreprise **via RAG (pgvector)**"*
- **Vérification code** :
  - `grep "search_similar_chunks|search_financing_chunks|DocumentChunk" backend/app/modules/applications/service.py` → **aucun résultat**
  - `grep "search_*" backend/app/modules/applications/prep_sheet.py` → **aucun résultat**
  - Aucun import de RAG dans le module applications
- **Impact** :
  - La génération LLM des sections n'exploite PAS les documents uploadés
  - Si l'utilisateur a uploadé ses statuts juridiques, ils ne sont PAS injectés dans la section "Présentation entreprise"
  - Si l'utilisateur a uploadé ses bilans, ils ne sont PAS injectés dans la section "Plan financier"
  - **La promesse "personnalisation maximale via documents" n'est pas tenue**
- **Cause racine** : T015 (generate_section) a probablement été livré sans la partie RAG, ou le RAG a été retiré pendant l'implémentation
- **Leçon** : un FR qui mentionne explicitement "via RAG (pgvector)" doit avoir une tâche de test dédiée qui vérifie que les chunks apparaissent dans le contexte LLM

### 3.2 🔴 Phase 12 Polish non livrée (T058-T062 `[ ]`)

Contrairement à toutes les autres specs auditées, la Phase 12 de spec 009 n'a **pas été marquée done** :

- **T058** `[ ]` Dark mode complet — vérification code : `grep "dark:" index.vue [id].vue` → 26 + 82 occurrences présentes ✅, probablement OK mais non formellement validé
- **T059** `[ ]` États vides et erreurs — probablement partiel
- **T060** `[ ]` Couverture 80 % — non vérifiée formellement
- **T061** `[ ]` Quickstart validation — non exécuté
- **T062** `[ ]` CLAUDE.md mise à jour — vérifiable en git log

**Impact** : cette spec est en position ambiguë — fonctionnellement livrée mais qualité non auditée. Contraste avec les specs 001-008 qui ont toutes leur Phase Polish ✅.

**Leçon** : une spec avec sa Phase Polish marquée `[ ]` devrait avoir un statut `in_progress` dans tasks.md, pas "livrée". Incohérence de workflow.

### 3.3 🟠 Historique de versions des sections non implémenté

- Key Entities mentionne : *"ApplicationSection ... Possede une cle, un titre, un contenu genere, un statut (non_generee, generee, validee), **et un historique de versions**"*
- **Vérification code** : `grep "version|history|previous_content"` dans service.py → **aucun résultat**
- **Impact** :
  - Si l'utilisateur régénère une section, le contenu précédent est **écrasé définitivement**
  - Si la régénération produit pire, l'utilisateur ne peut pas revenir en arrière
  - UX dégradée pour les utilisateurs qui itèrent
- **Leçon** : les Key Entities de la spec sont contractuelles — un champ listé mais non implémenté = promesse cassée

### 3.4 🟠 Templates hard-codés dans `templates.py`

- 4 templates + 1 générique dans un fichier Python
- Assumption spec : *"Les templates de dossier sont definis dans le code (pas dans la base de donnees) ; un template generique est utilise pour les fonds sans configuration specifique"*
- **Impact** :
  - Ajouter un 5ᵉ type de destinataire (ex: "fonds souverain national") = PR code
  - Modifier le ton/structure d'un template = déploiement backend
  - Même pattern que spec 006 (référentiels UEMOA/BCEAO hard-codés)
- **Leçon** : dette transverse — tous les "référentiels stables" du produit gagneraient à migrer en BDD (SECTOR_BENCHMARKS + UEMOA/BCEAO + templates applications)

### 3.5 🟠 Simulateur : hypothèses hard-codées

- Assumption spec : *"simulateur de financement utilise des estimations basees sur les parametres du fonds (montant min/max, duree) et **des hypotheses standard (taux, frais)**"*
- Les taux bancaires, les frais intermédiaire, les durées de traitement sont hard-codés dans `simulation.py`
- **Impact** :
  - Un taux bancaire change en zone UEMOA → pas de mise à jour possible sans redéploiement
  - Pas de différenciation par intermédiaire (SIB vs SGBCI ont-elles les mêmes frais ? Hypothèse non documentée)
- **Leçon** : les paramètres financiers externes doivent être versionnés (BDD + `effective_from`/`effective_to`) pour traçabilité

### 3.6 🟡 `application_node` exclu du `GUIDED_TOUR_TOOLS` — non documenté

- `graph.py:140` : `create_tool_loop(graph, "application", application_node, tools=APPLICATION_TOOLS + INTERACTIVE_TOOLS)` — **pas** de `GUIDED_TOUR_TOOLS`
- Commentaire graph.py:133 : *"GUIDED_TOUR_TOOLS injecte dans les 6 noeuds eligibles au guidage (feature 019)"* — application_node volontairement exclu
- Pourquoi ? Spec 019 l'a-t-elle décidé parce que le parcours guidé n'a pas de sens pendant la rédaction d'un dossier ?
- **Pas de documentation dans spec 009 ni dans spec 019 sur cette exclusion**
- **Leçon** : les décisions architecturales croisées (spec A affecte spec B) doivent être tracées dans les deux documents

### 3.7 🟡 Pas de preview PDF dans l'interface avant export

- L'utilisateur clique "Exporter" → download direct
- Pas de preview intermédiaire pour voir le rendu avant de l'envoyer à un fonds/banque
- Un PDF mal formaté (section vide, texte hallucinant) n'est détecté qu'après download
- **Leçon** : pour un document à valeur institutionnelle, preview avant download (même simple iframe PDF) ajoute de la confiance

---

## 4. Leçons transversales

1. **FR qui mentionne RAG/pgvector = tâche de test RAG dédiée** — sinon il saute silencieusement, comme ici.
2. **Phase Polish `[ ]` = spec non livrée** — workflow speckit devrait refuser de marquer la spec "done" sans tous les Phase `[x]`.
3. **Key Entities contractuelles** — un champ listé mais non implémenté = dette documentée.
4. **Référentiels "stables" gagneraient à vivre en BDD** — dette transverse avec specs 005/006/007/008.
5. **Décisions cross-spec = tracer dans les deux** — exclusion de GUIDED_TOUR_TOOLS pour application_node.
6. **Paramètres financiers externes = versionnés** (BDD + effective_from/to).

---

## 5. Actions résiduelles retenues

| # | Action | Priorité | Source |
|---|--------|----------|--------|
| 1 | **Implémenter FR-005 RAG réellement** : injecter `search_similar_chunks(user_id)` dans `generate_section` + tests de contenu RAG | **P1** | §3.1 |
| 2 | Finaliser Phase 12 Polish de spec 009 (dark mode formellement validé, états vides, couverture, quickstart) | P2 | §3.2 |
| 3 | Historique de versions pour `ApplicationSection` (champ `versions: JSONB` + endpoint "rollback") | P2 | §3.3 |
| 4 | Documenter l'exclusion de GUIDED_TOUR_TOOLS pour application_node dans spec 019 + spec 009 | P3 | §3.6 |
| 5 | Preview PDF inline avant export | P3 | §3.7 |
| 6 | Paramètres financiers simulation en BDD + versioning | P3 | §3.5 |

**Actions déjà en place** :
- ✅ `VALID_TRANSITIONS` pour les statuts
- ✅ 7 fichiers de test (couverture solide)
- ✅ 4 templates différenciés par target_type
- ✅ Pattern WeasyPrint/Jinja2 réutilisé

**Consolidation avec autres audits** :
- §3.4 "templates hard-codés" → fusionner avec dette transverse "référentiels en BDD" (sources : 005, 006, 007, 008, 009)

---

## 6. Verdict

**Spec 009 fonctionnellement en place à 92 % (57/62 tâches), mais avec 2 dettes majeures :**

1. **🔴 FR-005 RAG documentaire non implémenté** — la promesse "dossier personnalisé via les documents uploadés" n'est pas tenue. C'est précisément ce qui différencierait un dossier de qualité d'un dossier générique.
2. **🔴 Phase 12 Polish non livrée** (T058-T062 `[ ]`) — incohérence de workflow, spec non formellement finalisée.

La couverture de tests est **remarquable** (7 fichiers, bien meilleur que spec 008). La machine à états est propre. Les templates différenciés fonctionnent.

**Recommandation** : avant de bâtir spec 011 (dashboard) qui agrègera les dossiers, **implémenter FR-005 RAG** (P1) + finaliser Phase 12 (P2). Sans RAG, les sections générées restent génériques, ce qui mine la value proposition de personnalisation.

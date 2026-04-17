# Audit Rétrospectif — Spec 006 : Génération de Rapports ESG en PDF

**Date d'audit** : 2026-04-16
**Auditeur** : Angenor (Project Lead) + assistant Amelia
**Spec** : [specs/006-esg-pdf-reports/](../../../specs/006-esg-pdf-reports/)
**Méthode** : rétrospective post-hoc
**Statut rétro** : ✅ Complet

---

## 1. Portée de la spec

Génération de rapports PDF ESG professionnels de 5-10 pages (9 sections) avec graphiques SVG + résumé exécutif IA + conformité UEMOA/BCEAO. Liste, prévisualisation, notification chat.

| Dimension | Livré |
|-----------|-------|
| Tâches | 35 / 35 `[X]` (100 %) — **mais cf. §3.1** |
| User Stories | 4 (US1-US2 P1, US3 P2, US4 P3) |
| Phases | 7 |
| Nouveau modèle | `Report` + enums `ReportType`, `ReportStatus` |
| Nouveau module | `backend/app/modules/reports/` (service, router, charts, templates) |
| Stack PDF | WeasyPrint (HTML → PDF) + matplotlib (SVG) + Jinja2 |
| Sections PDF | 9 (couverture, résumé, scores, forts, axes, benchmark, conformité, plan, méthodo) |

---

## 2. Ce qui a bien fonctionné

### 2.1 Structure modulaire claire

- `backend/app/modules/reports/` : service + router + charts + templates + schemas
- Templates HTML + CSS séparés (`esg_report.html`, `esg_report.css`)
- Prompt IA isolé dans `prompts/esg_report.py`
- Clean separation of concerns

### 2.2 Validations d'état correctes

- **FR-018** : `if assessment.status != ESGStatusEnum.completed` (service.py:207) ✅
- **FR-020** : vérification d'un report `generating` existant avant nouvelle génération (service.py:219) ✅
- Enums `ReportStatusEnum` : generating/completed/failed — cycle de vie propre

### 2.3 Stack PDF pragmatique

- WeasyPrint : HTML → PDF, permet du CSS print sophistiqué
- Matplotlib SVG : graphiques vectoriels nets à l'impression
- Jinja2 : template layer découplé, facile à modifier
- Choix éprouvés, pas de magie — maintenance facile

### 2.4 TDD respecté

- 3 fichiers de test écrits avant implémentation (T013-T015)
- Tests de `charts.py`, `service.py`, `router.py`
- Couverture visée 80% (T035)

### 2.5 Page `/reports` + `ReportButton.vue`

- Page liste présente dans `frontend/app/pages/reports/`
- `ReportButton.vue` dans `components/esg/` pour déclencher la génération depuis la page ESG
- US1 + US2 livrées ✅

---

## 3. Ce qui a posé problème

### 3.1 🔴 DISCORDANCE MAJEURE — US4 (notification chat) marquée `[X]` mais non implémentée

- T030 : *"Ajouter un noeud ou intégration dans le graph LangGraph pour déclencher la génération de rapport et poster le message de notification"*
- T031 : *"Rendre le lien de téléchargement cliquable dans le composant chat frontend"*
- **Tous deux marqués `[X]` dans `tasks.md`**
- **Vérification code** :
  - `grep -i "report" backend/app/graph/graph.py` → **aucun résultat**
  - Aucun fichier `report_tools.py` dans `backend/app/graph/tools/`
  - Aucune référence à `generate_report`, `esg_report`, `rapport pdf` dans `nodes.py`
  - Aucun event SSE `report_ready` dans `chat.py`
- **FR-019 ("Le chatbot DOIT informer l'utilisateur quand le rapport est prêt") → NON IMPLÉMENTÉ**
- **Cause racine** : vérification de livraison défaillante sur les tâches speckit — check des `[X]` sans vérification du code réel
- **Impact** : l'utilisateur doit rafraîchir `/reports` pour savoir si son PDF est prêt. Pas de flux conversationnel comme promis.
- **Leçon** : quand une spec évolue, le repo tasks.md devient la source de vérité apparente mais pas nécessairement la réalité. **Croiser tasks.md ↔ code avant de marquer `[X]`**.

Note : ce même anti-pattern avait été observé pour T038 de spec 002 (`chat.spec.ts` absent).

### 3.2 🟠 Génération PDF synchrone → blocage worker HTTP

- Assumption spec : *"La génération est synchrone (pas de queue de tâches asynchrone pour cette version)"*
- SC-002 cible : "< 30 secondes"
- **Impact à l'échelle** : chaque génération bloque un worker uvicorn pendant 30 s
  - 10 utilisateurs qui génèrent en simultané → 10 workers bloqués → pannes cascade
  - Le calcul LLM du résumé exécutif (~5-10 s) + SVG matplotlib + WeasyPrint (~5-10 s) cumule facilement 30 s
- Pas de queue Celery/RQ/background task (marqué explicitement hors scope)
- **Leçon** : accepter "synchrone hors scope" dans une V1 est OK, mais documenter comme dette critique avec trigger de migration (ex: "> 5 générations simultanées observées en prod")

### 3.3 🟠 Module reports non accessible au LLM (pas de REPORT_TOOLS)

- Les 8 autres modules métier (profil, ESG, carbon, financing, credit, application, documents, action_plan) exposent des `*_TOOLS` LangChain
- **Reports n'a rien** → le LLM ne peut pas dire *"je génère votre rapport"* et déclencher l'action
- Seul point d'entrée : clic bouton `ReportButton.vue` sur la page `/esg/results`
- **Cause racine** : spec 006 antérieure à spec 012 (tool-calling) — oubli de migration
- **Leçon** : toute nouvelle capacité backend doit avoir un tool LangChain dès que spec 012 est en place (date de migration : 2026-XX-XX)

### 3.4 🟡 Pas de signature/watermark des PDFs

- SC-005 parle de "téléchargeables et s'ouvrent dans lecteurs courants" mais pas d'authenticité
- Un rapport ESG remis à un investisseur peut être **altéré** avant présentation (scores gonflés, date modifiée)
- Pas de signature cryptographique, pas de watermark "généré le XX par ESG Mefali", pas de QR code de vérification
- **Leçon** : pour un document à valeur institutionnelle (FR-004 : "présenter à des investisseurs"), l'authenticité est une exigence implicite

### 3.5 🟡 Pas de quota sur les rapports stockés

- Chaque génération crée un nouveau fichier dans `uploads/reports/`
- Pas de purge automatique, pas de limite par user
- Un utilisateur peut générer 100 rapports pour la même évaluation → 100 × 2-5 MB stockés
- Même dette que spec 004 sur les documents (cf. action #4 de l'index consolidé)
- **Leçon** : applique-la globalement — tout stockage user-generated nécessite quota + purge

### 3.6 🟡 Conformité UEMOA/BCEAO hard-codée dans le template

- T027 : *"tableau détaillé des taxonomies UEMOA et réglementation BCEAO"* ajouté au template HTML
- Si la BCEAO met à jour sa taxonomie, il faut redéployer le backend
- Pas de version du référentiel dans `Report` (traçabilité de quelle version a été utilisée)
- **Leçon** : les référentiels réglementaires doivent être versionnés en BDD + affichés dans le rapport

### 3.7 🟡 Résumé exécutif IA non validé

- T026 : *"Affiner le prompt pour garantir pertinence et qualité (150-300 mots, cohérent avec scores, français professionnel)"*
- Pas de mécanisme de vérification automatique :
  - Le résumé fait-il bien 150-300 mots ? (non vérifié)
  - Est-il en français ? (non vérifié)
  - Les scores cités correspondent-ils aux scores réels ? (non vérifié — hallucination possible)
- SC-004 ("résumé jugé pertinent") non mesurable
- **Leçon** : les outputs LLM persistés (vs éphémères du chat) doivent avoir des guards : longueur, langue détectée, cohérence numérique avec les données source

---

## 4. Leçons transversales

1. **Vérifier les `[X]` tasks contre le code** — discordance observée spec 002 (T038) + spec 006 (T030/T031). Anti-pattern speckit.
2. **"Synchrone hors scope" doit avoir un trigger de migration** — pas juste une note d'assumption.
3. **Toute nouvelle capacité post-spec 012 = tool LangChain** — sinon le LLM ne peut pas l'orchestrer.
4. **Documents institutionnels → authenticité** (signature, watermark, QR de vérification).
5. **Référentiels réglementaires = BDD versionnée** — pas hard-codée dans les templates.
6. **Outputs LLM persistés → guards de validation** — longueur, langue, cohérence numérique.

---

## 5. Actions résiduelles retenues

| # | Action | Priorité | Source |
|---|--------|----------|--------|
| 1 | **Implémenter FR-019 réellement** : `REPORT_TOOLS` (`generate_esg_report`, `list_reports`) + event SSE `report_ready` | P1 | §3.1, §3.3 |
| 2 | **Queue asynchrone pour la génération PDF** (Celery/RQ/FastAPI BackgroundTask au minimum) | P1 | §3.2 |
| 3 | Signature/watermark PDF (PyPDF2 + metadata + QR code de vérification) | P2 | §3.4 |
| 4 | Quota + purge automatique des rapports (ex: 10 rapports max par évaluation, purge > 90j) | P2 | §3.5 |
| 5 | Guards sur le résumé exécutif IA (longueur, langue, cohérence scores) | ~~P2~~ → **P1** (reclassé 2026-04-16) | §3.7 |
| 6 | Versionner les référentiels UEMOA/BCEAO en BDD + champ `regulation_version` sur `Report` | P3 | §3.6 |

**Actions déjà en place** :
- ✅ Validation statut `completed` avant génération
- ✅ Prévention des doublons de génération simultanée
- ✅ Stack WeasyPrint + matplotlib + Jinja2 propre

---

## 6. Verdict

**Spec 006 livrée à 80 % — les US1/US2/US3 sont en place et fonctionnelles, mais US4 (notification chat, FR-019) est marquée `[X]` sans avoir été implémentée.**

Cette discordance est **le 2ème cas confirmé** dans l'audit (après T038 de spec 002). Ça valide l'inquiétude d'Angenor sur speckit : les `[X]` sont auto-déclaratifs, sans vérification par croisement code/spec. L'outil n'a pas de gate implémentation → validation.

Les autres dettes sont opérationnelles (queue async, quota, signature) plutôt que architecturales. **§3.1 + §3.2 sont P1** : le premier parce que la spec n'est pas vraiment terminée, le second parce que la génération synchrone ne tiendra pas à l'échelle.

---

## 7. Mise à jour 2026-04-16 — reclassement Guards résumé exécutif IA P2 → **P1**

**Justification** : le résumé exécutif IA (§3.7) est **persisté dans un document officiel remis aux bailleurs** (PDF ESG), pas un message éphémère du chat. L'absence de guards transforme une hallucination LLM en risque métier concret.

**Scénario d'échec** :
1. Le LLM génère un résumé avec un chiffre halluciné (ex : « votre score ESG est de 85/100 » alors qu'il est de 65)
2. Le PDF est produit, signé de facto par Mefali (logo, en-tête, référence)
3. Le user le transmet au bailleur (GCF, BOAD, etc.)
4. Le bailleur croise les chiffres avec les sections détaillées du même PDF
5. Constat d'incohérence → dossier rejeté → perte de crédibilité

**Classes de risques** :
- **Compliance** : le bailleur peut dénoncer le document comme fallacieux
- **Crédibilité plateforme** : « Mefali produit des chiffres faux »
- **Juridique** : dans un contexte de financement (engagement contractuel), un document erroné engage la responsabilité de la plateforme

**Guards requis** (minimum viable) :
- Longueur (150-400 mots) — rejet si hors bornes
- Langue détectée (fr_FR) — rejet si drift anglais ou autre
- Cohérence numérique : tous les chiffres du résumé doivent apparaître dans les sections détaillées (score global, sous-scores piliers, principales recommandations)
- Vocabulaire interdit : détection de formulations à risque (« garanti », « certifié », « validé par ») que le LLM ne doit pas poser de lui-même

Même classe de risque que le rate limiting (FR-013) : invisible tant que ça n'arrive pas, catastrophique quand ça arrive. P1 justifié.

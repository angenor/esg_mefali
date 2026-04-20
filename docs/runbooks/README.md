# Runbooks opérationnels (G-3)

**Owner** : Angenor (Project Lead, ops de facto MVP)
**Dernière mise à jour** : 2026-04-20
**Checkpoint Phase 0** : 5 runbooks obligatoires avant fin Phase 0 (finding G-3 readiness check 2026-04-18)
**Révision** : à chaque incident majeur + post-mortem trimestriel

---

## Index

| # | Runbook | Sévérité max | Fréquence estimée | Statut |
|---|---------|--------------|-------------------|--------|
| 1 | [Incident response général](#1-incident-response-général) | P1 | Rare (espéré) | 🟡 squelette |
| 2 | [Outage LLM provider switch](#2-outage-llm-provider-switch) | P2 | 1-4×/an | 🟡 squelette |
| 3 | [Data residency migration](#3-data-residency-migration) | P1 | Exceptionnel | 🟡 squelette |
| 4 | [Copie anonymisée PROD → STAGING mensuelle](#4-copie-anonymisée-prod--staging-mensuelle) | P3 | Mensuelle | 🟡 squelette |
| 5 | [Migration référentiel bloquée — divergence > 20 %](#5-migration-référentiel-bloquée--divergence--20) | P1 | Rare | 🟡 squelette |
| 6 | [Rollback migration Alembic (NFR32 trimestriel)](#6-rollback-migration-alembic-nfr32-trimestriel) | P1 | Trimestriel | 🟡 squelette |

**Légende statut** : 🟡 squelette (structure + TODO) · 🟢 prêt (détails opérationnels complets) · ✅ validé (testé lors d'un drill ou incident réel)

**Convention** : tous ces runbooks commencent avec structure standard (Purpose / Triggers / Prerequisites / Decision tree / Steps / Rollback / Post-incident / References) et doivent être complétés avant clôture Phase 0.

---

## 1. Incident response général

### Purpose

Runbook meta appliqué à tout incident P1/P2 (user-facing degradation, data loss, security breach, outage partiel ou total). Garantit qu'aucun incident ne reste sans réponse structurée.

### Triggers (quand déclencher)

Un ou plusieurs des signaux suivants :
- **Alerting Sentry/PagerDuty** : erreur critique taux > seuil NFR68
- **User reports** : > 3 signalements simultanés même symptôme
- **Monitoring Story 17.5** : dashboard admin montre anomalie sur metric clé (latence p95, error rate, cost LLM dépassement)
- **Manual detection** : Angenor ou collaborateur constate comportement anormal

### Prerequisites

- Accès AWS console (IAM role ops)
- Accès Sentry dashboard
- Accès Mailgun (pour notification users si dégradation communiquée)
- `backend/scripts/diagnose.sh` (à créer lors de Phase 0)
- Compte Slack/Discord/WhatsApp pour coordination (si > 1 intervenant)

### Decision tree

1. **Severity triage** (≤ 5 min)
   - P1 = data loss / sécurité / outage > 50 % users → action immédiate
   - P2 = dégradation partielle / latence x3 / feature majeure KO → action sous 30 min
   - P3 = bug cosmétique / edge case → ticket suivi, pas urgence

2. **Type triage**
   - LLM outage → runbook 2 (outage LLM provider switch)
   - BDD lock / migration cassée → section step-by-step ci-dessous
   - Frontend down → vérifier Cloudflare/Nuxt build, rollback dernière release
   - Guard LLM fail massif → vérifier Story 9.6 guards + télémétrie `llm_guard_failure`

### Step-by-step procedure

- [ ] **1. Acknowledge** l'alerte dans Sentry (stop l'escalade auto)
- [ ] **2. Rassembler les infos** : error message, user_id impactés, tool_name depuis `tool_call_logs`, timestamp, environnement (PROD/STAGING)
- [ ] **3. Décider** : hot-fix immédiat OU rollback dernier déploiement OU attendre investigation approfondie
- [ ] **4. Communiquer** aux users si user-facing > 5 min (email transactionnel Mailgun avec message dédié)
- [ ] **5. Exécuter** le fix (hot-fix ou rollback)
- [ ] **6. Valider** via smoke tests + user confirmation si possible
- [ ] **7. Documenter** dans `_bmad-output/implementation-artifacts/incident-log-YYYY-MM-DD.md` (à créer)

### Rollback procedure

**Rollback déploiement backend** : (à détailler Phase 0 — AWS ECS Fargate service update revert à la précédente task definition).

**Rollback migration Alembic** : `alembic downgrade -1` (stop app d'abord, backup RDS snapshot via console AWS, exécuter, restart). **⚠️ Attention aux migrations non-réversibles** (DROP COLUMN) — voir checklist NFR75.

### Post-incident actions

- [ ] Post-mortem dans les 48h (template à créer)
- [ ] Action items dans `deferred-work.md` si pattern systémique
- [ ] Mise à jour de ce runbook si procédure a évolué
- [ ] Notification stakeholders si incident impacte cible SC-B1 adoption

### References

- `architecture.md §D9` (Backup + PITR 5 min + RTO 4h / RPO 24h)
- `architecture.md §NFR68-71` (Budget & Ops)
- `architecture.md §G-3` (checklist runbooks)
- `business-decisions-2026-04-19.md §NFR68-69` (budgets)
- Story 9.7 `tool_call_logs` (source de vérité diagnostic)

---

## 2. Outage LLM provider switch

### Purpose

Basculer le provider LLM primaire vers le fallback quand le primaire (actuellement MiniMax via OpenRouter, à confirmer post-bench Story 10.13) devient indisponible ou dégradé.

### Triggers

- **Circuit breaker 60s ouvert** sur ≥ 3 tools différents dans les 5 dernières minutes (signal fort d'outage LLM, pas bug isolé)
- **Rate limiting OpenRouter 429** répété > 10 fois / 5 min
- **Latence p95 LLM > 10s** sur plusieurs tools simultanément (dégradation provider)
- **Monitoring cost Story 17.5** : coût journalier > 150 % de la moyenne mobile 7j (possible bug ou changement tarif provider)

### Prerequisites

- Accès `.env` ou AWS Secrets Manager (variables `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`)
- Les 3 providers du bench Story 10.13 configurés en secondaire :
  - **Primaire MVP** : (à confirmer post-bench Story 10.13)
  - **Fallback 1** : Anthropic direct `api.anthropic.com`
  - **Fallback 2** : Anthropic via OpenRouter
- Crédits actifs chez les 2 fallbacks (vérif mensuelle recommandée)

### Decision tree

1. **Outage primaire seulement ?** → Switch fallback 1. Continuer monitoring primaire.
2. **Outage primaire + fallback 1 ?** → Switch fallback 2 (Anthropic OpenRouter).
3. **3 providers KO simultanément ?** → Outage sévère majeur. Mettre Mefali en **mode dégradé read-only** (désactiver tous tools LLM, laisser seulement dashboards + historique). Communiquer users.

### Step-by-step procedure

- [ ] **1. Confirmer** l'outage via health check primaire : `curl -I $LLM_BASE_URL/models` (timeout 5s)
- [ ] **2. Modifier** variables env (via AWS Secrets Manager rotation ou redeploy ECS Fargate avec nouvelles env vars) :
  ```
  LLM_BASE_URL=https://api.anthropic.com/v1   # fallback 1
  LLM_API_KEY=<anthropic_direct_key>
  LLM_MODEL=anthropic/claude-sonnet-4.6
  ```
- [ ] **3. Redémarrer** les tâches ECS Fargate (rolling update pour éviter downtime)
- [ ] **4. Smoke test** : invoquer 1 tool via chat test-user pour confirmer le switch
- [ ] **5. Notifier** l'équipe (Angenor solo = self-note) de la bascule dans `incident-log-YYYY-MM-DD.md`
- [ ] **6. Monitor** primaire pour bascule retour : vérifier 3 smoke tests OK consécutifs à 10 min d'intervalle avant de revenir

### Rollback procedure

Switch de retour au primaire : inverse de la procédure ci-dessus. Ne pas forcer un retour avant 30 min de stabilité primaire confirmée.

### Post-incident actions

- [ ] Documenter durée outage + provider concerné
- [ ] Si outage > 2h : envisager ajout d'un 4ème provider (OpenAI via OpenRouter ?)
- [ ] Si outage récurrent : évaluer switch primaire vers provider plus stable
- [ ] Update Story 10.13 bench data avec observations prod réelles

### References

- Story 10.13 (Migration embeddings Voyage + bench 3 providers LLM)
- `docs/bench-llm-providers-phase0.md` (livrable Story 10.13)
- `architecture.md §D10` (LLM Provider Layer + 2 niveaux switch)
- `.env` + `.env.example`

---

## 3. Data residency migration

### Purpose

Migrer les données Mefali hors de AWS EU-West-3 (Paris) vers une juridiction alternative en cas de changement réglementaire, exigence partenaire bailleur, ou décision business (ex : exigence UEMOA de résidence locale).

### Triggers

- **Exigence réglementaire** : nouveau cadre CEDEAO/UEMOA impose hébergement local
- **Exigence partenaire** : bailleur (ex: BOAD, BAD) exige données en Afrique
- **Risque géopolitique** : sanctions imprévues EU ↔ AWS impactant accessibility
- **Décision business** : rapprocher l'hébergement des users (latence, souveraineté)

### Prerequisites

- Inventaire complet des données (voir `architecture.md §D8`)
- Provider cible identifié et évalué (candidats : AWS Cape Town za-af-south-1, Orange Business Services Dakar/Abidjan, ou provider local UEMOA)
- Budget migration estimé (coût transfert + downtime + tests)
- Fenêtre de maintenance négociée avec users impactés (min 2 semaines notice)
- Backup complet + PITR actif avant migration

### Decision tree

1. **Migration partielle ou totale ?**
   - Partielle : seulement données users identifiés (exemple : users BOAD → hébergement local)
   - Totale : migration de toute la plateforme
2. **Blue-green ou cutover ?**
   - Blue-green : recommandé, 0 downtime user, coûte 2x pendant transition
   - Cutover : downtime prolongé (24-72h), coûte moins cher
3. **Garder EU-West-3 en secondaire ?**
   - Oui : résilience multi-région, coûte plus cher
   - Non : économie, mais perte de la résidence EU si retour

### Step-by-step procedure

**TODO Phase 0+1 — Détailler lors de première évaluation** :
- [ ] Audit des dépendances régionales (S3 buckets, RDS, embeddings pgvector, MINIo local)
- [ ] Test migration sur env STAGING vers provider cible
- [ ] Définition des SLA cibles migration
- [ ] Communication legal (RGPD, lois locales cibles)
- [ ] Exécution migration blue-green
- [ ] Smoke tests multi-pays (SN, CI, BF, BJ, etc.)
- [ ] Décommissionnement ancien hébergement après 30j

### Rollback procedure

**⚠️ Rollback data residency = opération majeure**. Possible via restauration des backups CRR (EU-West-1) si la migration s'est faite en blue-green. Impossible si cutover et backups supprimés.

### Post-incident actions

- [ ] Legal review des contrats bailleurs impactés
- [ ] Mise à jour `architecture.md §D8` avec nouvelle zone
- [ ] Notification users via email Mailgun (transparence RGPD/locale)
- [ ] Update documentation publique si affichée

### References

- `architecture.md §D8` (data residency AWS EU-West-3 + plan de contingence)
- `architecture.md §D9` (backup + PITR + RTO/RPO)
- `prd.md §Annexe H` (juridiction + conformité)
- RGPD / loi sénégalaise protection données personnelles

---

## 4. Copie anonymisée PROD → STAGING mensuelle 🟢

**Status** : 🟢 Procédure opérationnelle complète (Story 10.7 done).

### Purpose

Refresh mensuel du dataset STAGING à partir d'une copie anonymisée de PROD pour :
- Reproduire bugs prod avec données réalistes (sans PII)
- Valider les migrations Alembic sur volumétrie réelle
- Tests e2e avec patterns réels d'usage

### Triggers

- **Programmé** : 1er du mois, 02:00 UTC — GitHub Actions `schedule: cron '0 2 1 * *'` (Q4 tranchée Story 10.7, EventBridge différé Phase Growth)
- **Ad-hoc** : Angenor déclenche manuellement via `workflow_dispatch` avant un test critique (migration majeure, pilote PME)

### Prerequisites

- Script `backend/scripts/anonymize_prod_to_staging.py` (Story 10.7 AC5 done)
- Module `backend/app/core/anonymization.py` (15 patterns PII FR/AO, fail-fast D8.2)
- Env STAGING provisionné via `infra/terraform/envs/staging/` (Story 10.7 AC3)
- Backup PROD du jour confirmé (RPO 24h, `aws rds describe-db-snapshots`)
- Secret `ANONYMIZATION_SALT` dispo dans AWS Secrets Manager namespace `mefali/ops` (lu par script fail-fast si absent)
- Fenêtre STAGING inutilisée (typiquement week-end early morning)

### Prerequisites CRR S3 (Story 10.7 AC6)

Pour que le bucket destination EU-West-1 reçoive la réplication :

1. **Bucket source EU-West-3** (`mefali-prod`) : Versioning `Enabled` (prérequis CRR — l'API S3 refuse la Replication Configuration sans Versioning actif).
2. **Bucket destination EU-West-1** (`mefali-prod-backup-eu-west-1`) : Versioning `Enabled` + tag `Purpose=crr-destination`.
3. **IAM role `mefali-<env>-s3-replication`** : `s3:GetReplicationConfiguration`, `s3:ListBucket`, `s3:GetObjectVersionForReplication`.
4. **Vérification opérationnelle** :
   ```bash
   aws s3api get-bucket-replication --bucket mefali-prod --profile mefali-admin
   # Attendu : ReplicationConfiguration avec Status=Enabled, Destination EU-West-1
   ```

### Prerequisites ops Phase Growth (post-pilote PME)

- [ ] **MFA Delete** activé sur `mefali-prod` (root AWS CLI — cf. `docs/CODEMAPS/storage.md §6.2`)
- [ ] **MFA Delete** activé sur `mefali-prod-backup-eu-west-1`
- [ ] **Object Lock WORM** évalué pour bucket SGES dédié si audit bailleur l'exige (rétention 10 ans immuable — nécessite création bucket avec flag `object_lock_enabled_for_bucket=true`)
- [ ] Tabletop exercise trimestriel incluant scénario « MFA token compromis — rotation root »

### Decision tree

1. **Copie complète ou incrémentale ?**
   - Complète (monthly) : full refresh, drop + reload all tables → DEFAULT MVP
   - Incrémentale (hebdo future) : seulement delta depuis last refresh — Phase Growth
2. **Anonymisation strict ou preserving ?**
   - Strict : tous les PII (email, nom, téléphone, RCCM, NINEA, IFU, CNI, IBAN, etc.) remplacés par `anonymize_deterministic(value, salt)` (SHA256 tronqué) — DEFAULT MVP
   - Preserving (shapes) : garder stats agrégées mais anonymiser identifiants — Phase Growth si besoin QA métier

### Step-by-step procedure

1. **Snapshot RDS PROD** :
   ```bash
   aws rds create-db-snapshot --db-instance-identifier mefali-prod \
     --db-snapshot-identifier refresh-staging-$(date +%Y%m%d) \
     --profile mefali-admin
   ```
2. **Restore snapshot vers instance temporaire** :
   ```bash
   aws rds restore-db-instance-from-db-snapshot \
     --db-instance-identifier mefali-staging-temp \
     --db-snapshot-identifier refresh-staging-$(date +%Y%m%d)
   ```
3. **Dump SQL filtré** (exclure BLOB documents/reports selon `EXCLUDED_TABLES`) :
   ```bash
   pg_dump -h <temp-endpoint> -U postgres mefali_staging_temp \
     --exclude-table=documents --exclude-table=reports \
     -f /tmp/prod_dump.sql
   ```
4. **Anonymisation fail-fast** :
   ```bash
   export ANONYMIZATION_SALT=$(aws secretsmanager get-secret-value \
     --secret-id mefali/ops/anonymization_salt --query SecretString --output text)
   python -m scripts.anonymize_prod_to_staging \
     --source /tmp/prod_dump.sql \
     --output /tmp/staging_anonymized.sql
   # Exit code 0 = OK, 2 = PII résiduel détecté (FAIL-FAST abort)
   ```
5. **Restore dump anonymisé vers STAGING** :
   ```bash
   psql -h <staging-endpoint> -U postgres mefali_staging \
     -f /tmp/staging_anonymized.sql
   ```
6. **Smoke tests** : 3 journeys test users (aminata, moussa, akissi) via pytest `--base-url=https://staging.mefali.example`.
7. **Decommission** instance RDS temporaire.
8. **Log** dans `docs/runbooks/staging-refresh-log-YYYY-MM-DD.md` (taille dump, durée anonymisation, nb substitutions par pattern).

### Rollback procedure

Si smoke tests échouent : rollback au snapshot STAGING précédent (conservé 2 cycles — 2 mois).

### Post-incident actions

- [ ] Compte-rendu du refresh (durée, volume, anomalies détectées)
- [ ] Alert immédiat si PII détecté pendant validation fail-fast (bug anonymization — enrichir `PII_PATTERNS` avant retry)
- [ ] Update `PII_PATTERNS` si nouveaux champs PII ajoutés au schema (toute migration Alembic touchant un champ sensible doit inclure un test anonymisation du champ)

### References

- `architecture.md §D8` (DEV/STAGING/PROD ségrégés + anonymisation fail-fast)
- `architecture.md §D9` (CRR EU-West-3 → EU-West-1 + ordre Versioning-first)
- Story 10.7 done (envs segregated + pipeline anonymisation + CRR + IAM granulaire)
- `business-decisions-2026-04-19.md §NFR69` (budget infra ≤ 1000 €/mois)
- `backend/app/core/anonymization.py` (15 PII patterns FR/AO)
- `backend/scripts/anonymize_prod_to_staging.py` (CLI fail-fast exit 2)
- `docs/CODEMAPS/storage.md §6 Propriétés bucket` (Versioning + MFA Delete + Object Lock)

---

## 5. Migration référentiel bloquée — divergence > 20 %

### Purpose

Runbook déclenché automatiquement par Story 13.8c `ImpactProjectionPanel` quand une `ReferentialMigration` N3 (Mariam admin) atteint ou dépasse le seuil de **20 % de verdicts basculés** par rapport à la version précédente. Garantit qu'aucune migration à impact systémique ne passe en production sans revue élargie.

### Triggers

- **Auto** : panneau `ImpactProjectionPanel` détecte `% vs seuil 20 %` atteint lors du test rétroactif stratifié sur ≥ 50 snapshots → workflow N3 bloqué automatiquement
- **Notification** : domain_events.migration_blocked émis, Mariam reçoit notification in-app + email
- **Manuelle** : Mariam peut forcer le déclenchement du runbook si elle anticipe une divergence lors d'une édition

### Prerequisites

- Workflow N3 déjà en état `tested_retroactively` (pas `draft` ni `pending_review`)
- Rapport de divergence disponible (`ImpactProjectionPanel` output)
- 2 admin Mefali disponibles (peer review N2 + revue élargie N3)
- Consultant ESG AO senior réservé (budget SC-B-PILOTE, 1-2 jours)

### Decision tree

1. **Divergence 20-30 %** → Revue élargie : 3 admins + consultant senior (1 jour d'analyse)
2. **Divergence 30-50 %** → Revue approfondie : 3 admins + 2 consultants (2 jours)
3. **Divergence > 50 %** → Arrêt migration, retour au stade `draft`, reformulation du scope

### Step-by-step procedure

**TODO Story 13.8c — Détailler lors du dev-story** :
- [ ] **1. Freeze** la ReferentialMigration en état `blocked` (pas de publication possible)
- [ ] **2. Notifier** :
  - Admin_super (Angenor) et admin_mefali (Mariam) via domain_events + email
  - Consultant ESG AO senior si divergence ≥ 30 % (budget SC-B-PILOTE débité)
- [ ] **3. Analyser** le rapport de divergence :
  - Quels critères ont basculé (PASS→FAIL notamment)
  - Distribution par secteur / pays / maturité
  - Identification des PME les plus impactées
- [ ] **4. Décider** (review élargie) :
  - **Valider avec transition douce** : publication avec période de grâce (ex: 90 jours) + notification users
  - **Valider avec migration progressive** : publication par cohortes (secteurs prioritaires d'abord)
  - **Rejeter** : retour au `draft` avec ajustements catalogue
- [ ] **5. Si valider** : mettre à jour `effective_date` (au moins J+30 pour communiquer aux PME), envoyer plan de transition
- [ ] **6. Si rejeter** : documenter raisons dans commits + notification aux stakeholders qui attendaient la migration
- [ ] **7. Update** `admin_catalogue_audit_trail` avec décision + signatures admins

### Rollback procedure

Si migration validée mais bugs détectés dans les 7 jours post-publication :
1. Revert `effective_date` via admin console
2. Restaurer les verdicts pré-migration depuis `referential_versions` snapshot
3. Notifier users impactés

### Post-incident actions

- [ ] Post-mortem de la divergence (pourquoi >20 % ?)
- [ ] Si pattern récurrent : revoir le processus de mise à jour catalogue pour détecter les impacts plus tôt
- [ ] Update threshold si besoin (20 % → 15 % si trop permissif, ou 25 % si trop sensible)
- [ ] Documenter dans `audit-tasks-discordance.md` si discordance spec/impl

### References

- Story 13.8c (Workflow N3 `ReferentialMigration` avec `ImpactProjectionPanel`)
- Story 13.9 (Publication referential v2 + trigger à `effective_date`)
- `ux-design-specification.md §Step 10 Journey 5 Mariam` (flow admin)
- `architecture.md §N3 workflow` (état transitions)
- `business-decisions-2026-04-19.md §SC-B-PILOTE` (budget consultants)

---

## 6. Rollback migration Alembic (NFR32 trimestriel)

### Purpose

Procédure opérationnelle de rollback d'une migration Alembic en production, exigée par NFR32 (drill trimestriel). Couvre toute migration de la chaîne `001 → 027` et au-delà.

### Triggers

- **Bug bloquant** découvert post-déploiement qui ne se fixe pas en hot-fix
- **Corruption de données** liée à une migration (CASCADE imprévu, perte de colonne)
- **Drill trimestriel NFR32** : exercer la procédure sur STAGING pour garder les ops en forme

### Prerequisites

- `pg_dump --schema-only` de référence pris AVANT la migration incriminée
- Accès AWS RDS console + secret `DATABASE_URL`
- Container application arrêté (éviter écritures concurrentes pendant rollback)
- Révision Alembic cible identifiée (`alembic history | grep <target>`)

### Step-by-step procedure

- [ ] **1. Arrêter** les workers (ECS task count = 0 ou scheduled stop)
- [ ] **2. Snapshot RDS** en plus du PITR (sécurité double)
- [ ] **3. Dump** le schéma courant : `pg_dump -h $HOST -U postgres -d esg_mefali --schema-only > pre-rollback.sql`
- [ ] **4. Rollback** : `alembic downgrade <target_revision>` (ex : `019_manual_edits`)
- [ ] **5. Vérifier** le head : `alembic current` doit retourner `<target_revision>`
- [ ] **6. Diff schéma** : `diff pre-rollback.sql <(pg_dump ... --schema-only)` — documenter ce qui a été rollbackké
- [ ] **7. Redémarrer** l'application (tasks count = baseline)
- [ ] **8. Smoke tests** : 3 journeys users

### Rollback de rollback

Si le rollback lui-même casse quelque chose :
1. `alembic upgrade <previous_head>` (revenir à l'état problématique mais stable)
2. Ou restaurer depuis le snapshot RDS pris à l'étape 2
3. Investiguer à froid puis refaire le cycle

### Post-incident actions

- [ ] Documenter le `downgrade()` qui a posé problème (cause racine)
- [ ] Ajouter test de round-trip pour la migration concernée si absent
- [ ] Update `backend/alembic/README.md` avec leçon apprise
- [ ] Drill trimestriel suivant : re-tester sur STAGING

### References

- `backend/alembic/README.md` (conventions + exemples d'en-tête)
- `docs/CODEMAPS/data-model-extension.md` (Story 10.1 — chaîne 020–027)
- `.github/workflows/test-migrations-roundtrip.yml` (gate CI automatique AC10)
- `architecture.md §NFR32` (drill rollback trimestriel)

---

## Maintenance de ces runbooks

- **Revue trimestrielle** obligatoire (même sans incident) pour garder à jour
- **Post-incident** : mettre à jour la procédure affectée si déviation observée
- **Nouveaux runbooks** : ajouter dans cet index + créer section dédiée
- **Archivage** : un runbook non utilisé en 12 mois reste documentaire mais ne bloque pas l'ops
- **Drill annuel** : exécuter fictivement chaque runbook 1×/an pour vérifier les prerequisites (accès, credentials, scripts) restent valides

## Checklist Phase 0 complétion G-3

- [ ] Runbook 1 (incident response) — procédure complète avec contacts
- [ ] Runbook 2 (LLM switch) — dépend de Story 10.13 bench pour provider primaire
- [ ] Runbook 3 (data residency) — squelette suffisant MVP, détails Phase Growth
- [x] Runbook 4 (staging refresh) — 🟢 Story 10.7 done (envs + anonymisation + CRR)
- [ ] Runbook 5 (migration blocked) — dépend de Story 13.8c

**Status global Phase 0** : squelettes prêts (2026-04-20), détails opérationnels à compléter au fil des stories qui les référencent (Story 10.13, 13.8c).

---

## 7. Déploiement nouveau environnement (Story 10.7 AC8)

### Purpose

Checklist standard pour un déploiement de feature depuis `main` → STAGING → PROD via les 3 workflows GitHub Actions ségrégués.

### Workflows

| Workflow | Trigger | Approval | Target env |
|----------|---------|----------|------------|
| `.github/workflows/deploy-dev.yml` | `push: main` auto | — | DEV (smoke tests uniquement en MVP) |
| `.github/workflows/deploy-staging.yml` | `push: staging` | GitHub Environment `staging` (1 reviewer) | STAGING AWS EU-West-3 |
| `.github/workflows/deploy-prod.yml` | `workflow_dispatch` + `confirmation_phrase="DEPLOY TO PRODUCTION"` | GitHub Environment `prod` (1 reviewer min) | PROD AWS EU-West-3 + CRR EU-West-1 |

### Branch protection rules (configuration manuelle GitHub UI)

- **`main`** : require PR + 1 approval + tous tests verts + branches up-to-date.
- **`staging`** : require PR + 1 approval + tous tests verts.
- **`prod`** : **pas de push direct** — `deploy-prod.yml` uniquement via `workflow_dispatch` (source = commit SHA pinné depuis `main`).

### Step-by-step procedure `main → staging → prod`

1. [ ] PR mergée dans `main` (CI verte, 1 approval, tests verts)
2. [ ] `deploy-dev.yml` auto-exécuté → smoke tests verts (optionnel en MVP — pas de cluster DEV partagé)
3. [ ] Cherry-pick ou merge sélectif commits `main` → branche `staging`
4. [ ] `deploy-staging.yml` auto-déclenché sur push `staging` → `test` → `terraform-plan` → approval GitHub Environment → `terraform-apply` → `deploy-ecs` → smoke tests STAGING
5. [ ] UAT manuelle STAGING (journeys fatou/moussa/aminata)
6. [ ] Trigger `deploy-prod.yml` : `gh workflow run deploy-prod.yml -f confirmation_phrase="DEPLOY TO PRODUCTION" -f ref=<sha-main>`
7. [ ] Approval GitHub Environment `prod` (required reviewers) → `terraform-apply-prod` → smoke tests PROD
8. [ ] Documenter dans `docs/runbooks/deployment-log-YYYY-MM-DD.md` (commit SHA déployé, durée, anomalies)

### GitHub Environments configuration (hors Terraform)

À configurer **manuellement** dans repo Settings → Environments (limitation AWS/GitHub 2026, pas d'API Terraform complète pour Environments) :

- Environment `staging` : required reviewers = 1 (Angenor), deployment branches = `staging` only
- Environment `prod` : required reviewers = 1 min, deployment branches = `main` only, wait timer = 5 min recommandé

### Secrets namespace (per-env)

Chaque env a ses secrets scopés dans GitHub Secrets :
- `AWS_ACCESS_KEY_ID_STAGING`, `AWS_SECRET_ACCESS_KEY_STAGING`, `AWS_ROLE_TO_ASSUME_STAGING`
- `AWS_ACCESS_KEY_ID_PROD`, `AWS_SECRET_ACCESS_KEY_PROD`, `AWS_ROLE_TO_ASSUME_PROD`
- **Jamais** de secret réutilisé cross-env (défense profondeur).

### Post-incident actions

- [ ] Si deploy-prod échoue : rollback via Terraform `terraform apply` sur tag précédent
- [ ] Post-mortem + update de ce runbook si procédure divergée

### References

- `.github/workflows/deploy-dev.yml` / `deploy-staging.yml` / `deploy-prod.yml`
- `infra/terraform/envs/staging/` + `infra/terraform/envs/prod/`
- `architecture.md §NFR73` (environnements isolés) + `§NFR76` (code review obligatoire)

---

## Security — RLS PostgreSQL (Story 10.5)

Pour tout incident lié à **RLS (Row-Level Security), fuite cross-tenant
présumée, ou audit admin_access_audit / admin_catalogue_audit_trail**,
consulter d'abord le codemap canonique :

- [`docs/CODEMAPS/security-rls.md`](../CODEMAPS/security-rls.md) —
  contrat `apply_rls_context`, listener `before_flush`, migration 028
  tamper-proof triggers, procédures de test local via `psql`,
  limitations connues + roadmap Epic 18.

## Storage — local + S3 EU-West-3 (Story 10.6)

Pour tout incident lié au **stockage fichiers** (upload documents,
génération PDF rapports, bascule local ↔ S3 Phase Growth), consulter :

- [`docs/CODEMAPS/storage.md`](../CODEMAPS/storage.md) —
  contrat `StorageProvider`, config `STORAGE_PROVIDER`, IAM S3, SSE-S3,
  multipart seuil 10 MB, presigned TTL, migration local → S3, limitations
  MVP (4 modules PDF in-memory non câblés, libs d'extraction tempfile
  adapter déferré).

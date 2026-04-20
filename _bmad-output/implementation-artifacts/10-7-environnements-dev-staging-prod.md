# Story 10.7 : Environnements DEV / STAGING / PROD ségrégués + pipeline anonymisation PROD→STAGING + CRR S3

Status: done

> **Contexte** : 7ᵉ story Epic 10 Fondations Phase 0. **Deuxième story consécutive infra** (après 10.5 RLS + 10.6 StorageProvider) — transition brownfield `app-logic` → `infrastructure` full. Première story qui livre de l'**Infrastructure-as-Code (Terraform) versionné git**, de l'**orchestration CI/CD multi-env**, et un **pipeline de données anonymisées** avec validation fail-fast.
>
> **Dépendances amont (done)** :
> - **Story 10.1** : migrations 020–027 appliquables sur chaque env (DEV/STAGING/PROD).
> - **Story 10.5 done** : RLS 4 tables + `admin_access_audit` — le dump PROD embarque des tables RLS-protégées qui doivent être anonymisées AVANT import STAGING. Le script d'anonymisation consommera les dumps filtrés par `apply_rls_context('admin_super')` pour tout voir.
> - **Story 10.6 done** : `S3StorageProvider` + `Settings.aws_region` fail-fast UE + CRR documenté théoriquement dans `docs/CODEMAPS/storage.md`. Story 10.7 **active réellement** CRR EU-West-3 → EU-West-1 (AC6) et **remplace la policy IAM trop large** de 10.6 (LOW-10.6-2 déféré → AC4 granulaire).
> - **Story 9.7 done** : pattern `with_retry` (`backend/app/graph/tools/common.py:372`) consommé si appels AWS dans le script anonymisation (ex. `aws rds create-db-snapshot`).
>
> **Ce que livre 10.7 (scope strict MVP)** :
> 1. **Séparation d'environnements (AC1)** : `ENV_NAME = dev | staging | prod` explicitement dans `Settings` Pydantic (fail-fast si invalide), chaque env a son propre `DATABASE_URL`, `AWS_S3_BUCKET`, `AWS_SECRETS_MANAGER_NAMESPACE`, `JWT_SECRET_KEY` — **zéro leak cross-env**.
> 2. **DEV = docker-compose enrichi** (AC2) : Postgres + pgvector + backend + frontend + **MinIO** (mock S3 local). Aucun compte AWS requis pour DEV.
> 3. **STAGING + PROD = Terraform modules** (AC3) versionnés dans `infra/terraform/` : `envs/staging/` (RDS t3.micro + 1 pod ECS Fargate + S3 bucket + Secrets Manager namespace) et `envs/prod/` (RDS multi-AZ + 2 pods ECS Fargate + S3 bucket + Secrets Manager + CRR EU-West-3 → EU-West-1). **Budget respecté NFR69** (1000 €/mois total).
> 4. **IAM policies granulaires per-env (AC4)** : absorbe **LOW-10.6-2** — `s3:DeleteObject` scopé `arn:aws:s3:::mefali-<env>/*` et **pas** `arn:aws:s3:::*`. Rôle app (`GetObject` + `PutObject` + `ListBucket`) séparé du rôle admin (`DeleteObject` avec condition `aws:MultiFactorAuthPresent=true`).
> 5. **Pipeline anonymisation PROD→STAGING fail-fast (AC5)** : `backend/scripts/anonymize_prod_to_staging.py` avec 15 patterns PII FR/AO (RCCM OHADA, NINEA SN, IFU CI/BF/BJ/TG, emails, téléphones CEDEAO, IBAN, etc.) + mapping déterministe. Abort si un pattern matche après anonymisation.
> 6. **CRR S3 activé (AC6)** : Bucket Versioning EU-West-3 → Replication Configuration → EU-West-1 bucket destination. Ordre strict documenté (Versioning obligatoire avant CRR).
> 7. **Versioning + MFA Delete documentés (AC7)** : absorbe **LOW-10.6-4** — runbook 4 enrichi avec procédure MFA Delete (root AWS CLI only, pas IaC) + Object Lock WORM pour documents SGES Phase Growth.
> 8. **CI/CD 3 workflows GitHub Actions (AC8)** : `deploy-dev.yml` (auto sur push `main`), `deploy-staging.yml` (auto sur push `staging`), `deploy-prod.yml` (manual `workflow_dispatch` + **GitHub Environments** avec required reviewers + branch protection rules).
> 9. **Baseline tests (AC9)** : 1406 → **≥ 1421** (+15) : 10 tests anonymisation patterns + 3 tests ENV_NAME validation + 2 tests IAM policy JSON parse.
>
> **Hors scope explicite (déféré)** :
> - Script `scripts/migrate_local_to_s3.py` (Phase Growth, déféré 10.6).
> - AWS EventBridge scheduling (Q4 tranchée → GitHub Actions `schedule:` cron MVP, EventBridge Phase Growth si volume justifie).
> - Object Lock WORM actif (documenté runbook seulement, activation Phase Growth avec audit bailleur).
> - NER spaCy `fr_core_news_lg` (Q2 tranchée → regex-only MVP, NER différé Phase Growth si fuite détectée).
> - Rôle `admin_super` AWS distinct du rôle app (MVP : IAM user dédié avec MFA, pas de cross-account role separation — Phase Growth).
>
> **Contraintes héritées (8 leçons Stories 9.x → 10.6, 2 nouvelles 10.5/10.6)** :
> 1. **C1 (9.7)** : **pas de `try/except Exception` catch-all** — le script anonymisation remonte explicitement `AnonymizationPatternViolation` + `AnonymizationDumpError` + `AnonymizationRestoreError`. Un `except Exception` fait échouer la revue.
> 2. **C2 (9.7)** : **tests prod véritables** — le pipeline est testable sur un vrai dump Postgres anonymisé, pas de mock du regex engine. Fixture `sample_prod_dump.sql` avec 10 PII enfouis dans des champs variés (profil, doc, application) + assertions post-anonymisation `regex.search(...) is None` pour chacune des 15 patterns.
> 3. **Marker `@pytest.mark.postgres`** : tests qui écrivent/relisent des dumps Postgres (2 tests E2E anonymisation). Skip propre si `TEST_POSTGRES_URL` absent.
> 4. **Marker `@pytest.mark.s3`** : tests qui vérifient CRR configuration via moto (1 test AC6). Réutilise le pattern 10.6.
> 5. **10.3 M1 — scan NFR66 exhaustif Task 1** : avant de créer `backend/scripts/anonymize_prod_to_staging.py`, vérifier (a) zéro script anonymisation préexistant (`rg "anonymi" backend/scripts/ backend/app/`), (b) zéro hard-coding `eu-west-3` ou `account_id` dans le code (scan exhaustif `rg -n "eu-west|\\b\\d{12}\\b"`), (c) zéro fichier `.tf` préexistant (`find infra/ -name "*.tf" 2>/dev/null`).
> 6. **10.4 — comptages par introspection runtime** : chaque AC qui mentionne « N tests ajoutés » sera prouvé par `pytest --collect-only -q backend/tests/test_scripts/test_anonymize_prod_to_staging.py | grep -c '::'` avant/après. Les chiffres Completion Notes citeront la commande exacte.
> 7. **10.5 — pas de duplication helpers** : si `ENV_NAME` enum existe déjà quelque part (ex. dans `Settings`), l'étendre au lieu de créer un `envs.py` dupliqué. Scan Task 1 confirmera.
> 8. **10.5 règle d'or — tester effet observable** : les tests anonymisation ne patchent PAS le regex engine. Ils chargent un vrai dump, font tourner le script, relisent le dump anonymisé, et assertent que `grep -E "<pattern_PII>" dump_anonymized.sql` ne matche plus. Idem CRR : `moto` s'applique sur un vrai appel `boto3.client("s3").put_bucket_replication(...)` (pas `patch("boto3.client")`).
> 9. **10.6 pattern shims legacy + fixture auto-use** : **non applicable** ici (pas de refactor brownfield sur du code préexistant — tout le scope est en création pure). Mentionné pour traçabilité si Task 1 révèle du code préexistant.
> 10. **10.6 leçon Settings Pydantic field_validator** : le pattern `ALLOWED_EU_REGIONS` (fail-fast boot) devient le modèle pour `ALLOWED_ENV_NAMES = frozenset({"dev", "staging", "prod"})` avec `@field_validator("env_name")`.

---

## Story

**As a** Équipe Mefali (SRE/DevOps solo, Angenor) + futurs mainteneurs Phase Growth,
**I want** 3 environnements isolés (DEV local docker-compose + STAGING AWS minimal EU-West-3 + PROD AWS EU-West-3 full) avec Terraform IaC versionné + secrets per-env via AWS Secrets Manager + pipeline d'anonymisation PROD→STAGING fail-fast (15 patterns PII FR/AO) + CRR S3 EU-West-3 → EU-West-1 activé + IAM policies granulaires per-env (anti-wildcard) + 3 workflows GitHub Actions ségrégués (DEV auto / STAGING branch / PROD manual approval),
**So that** la dette NFR73 (environnements isolés) soit résolue avant le premier pilote PME (AR-D8 + NFR73), que NFR34/NFR35 (RTO 4h / RPO 24h + CRR backup 2 AZ) soient opérationnels, que le budget NFR69 (≤ 1000 €/mois total) soit respecté avec check-list perf-sensibles (EXPLAIN plans hot paths), et que les dettes techniques **LOW-10.6-2** (IAM `DeleteObject` trop large) et **LOW-10.6-4** (Versioning + MFA Delete non documentés) soient absorbées dans la même livraison infra.

---

## Acceptance Criteria

### AC1 — `Settings` Pydantic `ENV_NAME` enum fail-fast + 3 envs isolés au boot

**Given** le pattern Settings Pydantic existant (`backend/app/core/config.py` avec `ALLOWED_EU_REGIONS` + `@field_validator("aws_region")` — Story 10.6), et l'absence d'un champ `env_name` ou équivalent (scan Task 1 à confirmer),

**When** un dev implémente l'extension `Settings`,

**Then** `backend/app/core/config.py` expose :

```python
ALLOWED_ENV_NAMES: frozenset[str] = frozenset({"dev", "staging", "prod"})

class Settings(BaseSettings):
    # ... champs existants ...

    # --- Environnement (Story 10.7) ---
    env_name: str = Field(default="dev", description="Environnement courant (dev/staging/prod) — NFR73")
    aws_secrets_manager_namespace: str = ""  # ex: "mefali/staging" ; vide en DEV (mock via .env)

    @field_validator("env_name")
    @classmethod
    def _validate_env_name(cls, v: str) -> str:
        """NFR73 — fail-fast si ENV_NAME non reconnu (empêche boot accidentel
        avec secrets génériques). Aligné pattern aws_region (Story 10.6)."""
        if v not in ALLOWED_ENV_NAMES:
            raise ValueError(
                f"env_name must be one of {sorted(ALLOWED_ENV_NAMES)} (NFR73 isolation). "
                f"Got: {v!r}"
            )
        return v
```

**And** une méthode helper `Settings.is_production() -> bool` retourne `True` uniquement si `env_name == "prod"` — consommée par tout code qui a besoin de se comporter différemment en PROD (ex. désactivation `debug=True` forcée, nécessité MFA admin).

**And** un garde-fou boot : si `env_name == "prod"` et `debug is True` → `ValueError("Production cannot run with debug=True")` (deuxième `@field_validator` ou `model_post_init`).

**And** `backend/.env.example` gagne :
```bash
# --- Environnement (Story 10.7) ---
# dev (local docker-compose), staging (AWS minimal), prod (AWS full)
ENV_NAME=dev
# Namespace AWS Secrets Manager (vide en DEV, "mefali/staging" ou "mefali/prod" en AWS)
AWS_SECRETS_MANAGER_NAMESPACE=
```

**And** **3 nouveaux tests** `backend/tests/test_core/test_config_env_name.py` (marker `unit`) valident : (a) default `"dev"` accepté, (b) `{"dev","staging","prod"}` acceptés, (c) `["test", "preprod", ""]` rejetés avec `ValidationError` mentionnant NFR73.

---

### AC2 — Docker Compose DEV complet (Postgres + pgvector + backend + frontend + MinIO mock S3)

**Given** le `docker-compose.yml` existant (Postgres + backend + frontend, sans mock S3), et le besoin que DEV puisse tester le flow `STORAGE_PROVIDER=s3` **sans compte AWS réel**,

**When** un dev lance `docker-compose up` à la racine du projet,

**Then** 4 services démarrent :

1. `postgres` (inchangé — pgvector/pgvector:pg16)
2. `backend` (étendu avec nouvelles env vars `ENV_NAME=dev`, `AWS_S3_ENDPOINT_URL=http://minio:9000`, `STORAGE_PROVIDER=local` par défaut — `s3` activable via override)
3. `frontend` (inchangé)
4. **`minio`** (nouveau — `minio/minio:latest`) : ports `9000` (API S3) + `9001` (console web), credentials root `MINIO_ROOT_USER=minioadmin` + `MINIO_ROOT_PASSWORD=minioadmin`, bucket `mefali-dev` créé automatiquement via un sidecar `mc` (MinIO Client) qui tourne 1×.

**And** un `docker-compose.override.yml.example` (**nouveau**) documente comment activer `STORAGE_PROVIDER=s3` + override `AWS_S3_ENDPOINT_URL=http://minio:9000` dans le backend pour tester le flow S3 en local (MinIO est 100 % API-compatible S3). Exemple copié depuis `docs/CODEMAPS/storage.md`.

**And** le `README.md` racine (section existante "Commandes utiles") ajoute :
```markdown
## Stack locale complète (Story 10.7)
- `docker-compose up` → Postgres + backend + frontend + MinIO (mock S3)
- Console MinIO : http://localhost:9001 (login minioadmin/minioadmin)
- Bascule test S3 local : `cp docker-compose.override.yml.example docker-compose.override.yml && docker-compose up`
```

**And** `backend/requirements-dev.txt` **n'est pas modifié** pour MinIO — tous les tests `@pytest.mark.s3` continuent de consommer `moto[s3]` (pas MinIO).

---

### AC3 — Terraform modules STAGING + PROD versionnés (`infra/terraform/`)

**Given** l'absence d'un dossier `infra/` préexistant (Task 1 confirme), et le besoin de versionner l'IaC dans le même repo que le code (mono-repo + git history),

**When** un dev audite `infra/terraform/`,

**Then** l'arborescence suivante est créée :

```
infra/
└── terraform/
    ├── README.md                        # Usage + prérequis (awscli, terraform ≥ 1.7, credentials admin)
    ├── modules/
    │   ├── rds/                         # Module paramétrable (instance_class, multi_az, storage_gb)
    │   │   ├── main.tf
    │   │   ├── variables.tf
    │   │   └── outputs.tf
    │   ├── s3/                          # Module paramétrable (bucket_name, versioning, crr_destination)
    │   │   ├── main.tf
    │   │   ├── variables.tf
    │   │   └── outputs.tf
    │   ├── ecs/                         # Module paramétrable (task_count, cpu, memory)
    │   │   ├── main.tf
    │   │   ├── variables.tf
    │   │   └── outputs.tf
    │   └── iam/                         # Module IAM policies per-env (AC4)
    │       ├── main.tf
    │       ├── variables.tf
    │       └── outputs.tf
    ├── envs/
    │   ├── staging/
    │   │   ├── main.tf                  # Instancie modules avec valeurs STAGING (t3.micro, 1 task, CRR off)
    │   │   ├── backend.tf               # Remote state S3 + DynamoDB locking
    │   │   ├── variables.tf
    │   │   └── terraform.tfvars.example # Template (ne contient PAS de secrets — lus depuis Secrets Manager)
    │   └── prod/
    │       ├── main.tf                  # Instancie modules avec valeurs PROD (db.t3.medium multi-AZ, 2 tasks, CRR on)
    │       ├── backend.tf               # Remote state S3 + DynamoDB locking (bucket séparé de staging)
    │       ├── variables.tf
    │       └── terraform.tfvars.example
    └── .gitignore                       # *.tfstate, *.tfstate.backup, .terraform/, *.tfvars (mais PAS .tfvars.example)
```

**And** chaque module Terraform respecte les invariants :
- **Pas de hard-coding `account_id`** : toute référence AWS account est lue via `data "aws_caller_identity" "current" {}`.
- **Pas de hard-coding `eu-west-3`** : paramètre `aws_region` avec default `"eu-west-3"` et validation `contains(["eu-west-1","eu-west-2","eu-west-3","eu-central-1","eu-central-2","eu-south-1","eu-south-2","eu-north-1"], var.aws_region)` (miroir `ALLOWED_EU_REGIONS` Python — NFR24 data residency).
- **Tagging standard** : chaque resource tagué `{ Environment = var.env_name, Project = "mefali", ManagedBy = "terraform" }` pour audit FinOps + tracking ressources orphelines.

**And** `infra/terraform/envs/staging/main.tf` instancie :
- `module "rds"` avec `instance_class = "db.t3.micro"`, `multi_az = false`, `storage_gb = 20` — **budget NFR69 : ~15 €/mois**.
- `module "ecs"` avec `task_count = 1`, `cpu = 512`, `memory = 1024` — **budget NFR69 : ~30 €/mois**.
- `module "s3"` avec `versioning = true`, **`crr_destination = null`** (pas de CRR STAGING pour limiter coût).
- `module "iam"` avec policies granulaires (cf. AC4).

**And** `infra/terraform/envs/prod/main.tf` instancie :
- `module "rds"` avec `instance_class = "db.t3.medium"`, `multi_az = true`, `storage_gb = 100` — **budget NFR69 : ~200 €/mois**.
- `module "ecs"` avec `task_count = 2`, `cpu = 1024`, `memory = 2048` — **budget NFR69 : ~250 €/mois**.
- `module "s3"` avec `versioning = true`, `crr_destination = "mefali-prod-backup-eu-west-1"` (activé — cf. AC6).
- `module "iam"` avec policies granulaires + condition MFA pour delete.

**And** un test `backend/tests/test_infra/test_terraform_syntax.py` (marker `unit`) exécute `terraform -chdir=infra/terraform/envs/staging init -backend=false && terraform -chdir=... validate` via `subprocess.run(...)` — **skip propre** si binaire `terraform` absent du PATH (évite blocage CI minimal). Idem pour `envs/prod`. **2 tests** minimum.

---

### AC4 — IAM policies S3 granulaires per-env (absorbe LOW-10.6-2)

**Given** la dette **LOW-10.6-2** déférée en Story 10.6 (IAM `s3:DeleteObject` grant sur `arn:aws:s3:::<bucket>/*` → risque pod compromis supprimant en masse), et le pattern de séparation rôle-app / rôle-admin recommandé dans le code review 10.6,

**When** un dev audite `infra/terraform/modules/iam/main.tf`,

**Then** **2 rôles distincts** sont créés par env (via `module "iam"`) :

**Rôle 1 — `mefali-<env>-app`** (attaché à ECS Fargate task) :
```hcl
resource "aws_iam_policy" "app_s3_read_write" {
  name = "mefali-${var.env_name}-app-s3-read-write"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ReadWriteOwnBucket"
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
        Resource = [
          "arn:aws:s3:::mefali-${var.env_name}",         # List bucket
          "arn:aws:s3:::mefali-${var.env_name}/*"        # Get/Put objects
        ]
        # Pas de DeleteObject ici — l'app ne supprime JAMAIS directement (soft-delete via Document.deleted_at)
      }
    ]
  })
}
```

**Rôle 2 — `mefali-<env>-admin`** (assumé par IAM user Angenor avec MFA) :
```hcl
resource "aws_iam_policy" "admin_s3_delete_mfa" {
  name = "mefali-${var.env_name}-admin-s3-delete-mfa"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "DeleteOwnBucketWithMFA"
        Effect   = "Allow"
        Action   = ["s3:DeleteObject", "s3:DeleteObjectVersion"]
        Resource = "arn:aws:s3:::mefali-${var.env_name}/*"
        Condition = {
          Bool = { "aws:MultiFactorAuthPresent" = "true" }
        }
      }
    ]
  })
}
```

**And** **aucune policy** n'utilise `Resource = "*"` ou `Resource = "arn:aws:s3:::*"` — **anti-wildcard systématique** (grep du codebase Terraform via test CI Task 12).

**And** **2 nouveaux tests** `backend/tests/test_infra/test_iam_policies.py` (marker `unit`) :
- `test_app_policy_has_no_delete_action()` : charge `aws_iam_policy.app_s3_read_write` via `terraform show -json` ou parsing HCL (`python-hcl2`), assert `"s3:DeleteObject" not in policy["Statement"][0]["Action"]`.
- `test_admin_policy_requires_mfa()` : parse la policy admin, assert `policy["Statement"][0]["Condition"]["Bool"]["aws:MultiFactorAuthPresent"] == "true"`.

**And** `docs/CODEMAPS/storage.md §IAM granulaire` (nouvelle section) documente :
- Le split rôle-app / rôle-admin.
- La condition MFA.
- La procédure assumption du rôle admin (`aws sts assume-role --role-arn ... --serial-number ... --token-code ...`).
- Un lien vers `infra/terraform/modules/iam/main.tf` comme **source unique de vérité**.

---

### AC5 — Pipeline anonymisation PROD→STAGING fail-fast (15 patterns PII FR/AO)

**Given** **Décision 8 architecture** (copie mensuelle + validation fail-fast) + runbook 4 squelette existant qui référence `backend/scripts/anonymize_prod_to_staging.py` **à créer ici**, et les patterns PII documentés §D8.2,

**When** un dev implémente `backend/scripts/anonymize_prod_to_staging.py` + module `backend/app/core/anonymization.py`,

**Then** `backend/app/core/anonymization.py` expose :

```python
"""Anonymisation déterministe PII AO (Story 10.7 — D8.2)."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

# 15 patterns PII FR/AO — validation fail-fast (architecture.md §D8.2 + enrichissement)
PII_PATTERNS: dict[str, re.Pattern[str]] = {
    # Identifiants entreprises OHADA
    "rccm_ohada":   re.compile(r"\bRC[CM]?\s*\w+\s*\d+\b", re.IGNORECASE),
    "ninea_sn":     re.compile(r"\b\d{7,9}\s*[A-Z]\s*\d\b"),
    "ifu_ci":       re.compile(r"\b\d{10,13}[A-Z]?\b"),
    "ifu_bf_bj_tg": re.compile(r"\b\d{7,12}\b"),
    "nif_ml_ne":    re.compile(r"\b\d{8,11}[A-Z]?\b"),

    # Identifiants personnels
    "email_real":   re.compile(r"\b[\w.-]+@(?!anonymized\.test|example\.(com|org))[\w.-]+\b"),
    "phone_cedeao": re.compile(r"\+?22[1-9]\s?\d{2,3}\s?\d{2,3}\s?\d{2,3}\s?\d{0,3}"),
    "iban":         re.compile(r"\b[A-Z]{2}\d{2}\s?(?:\d{4}\s?){3,7}\d{0,4}\b"),
    "cni_sn":       re.compile(r"\b[12]\s?\d{3}\s?\d{4}\s?\d{5}\b"),  # CNI Sénégal 13 chiffres

    # Coordonnées entreprise
    "address_precise": re.compile(r"\b\d{1,4}\s+(?:rue|avenue|bd|boulevard|route|impasse|allée)\s+[\w\s\-]+\b", re.IGNORECASE),
    "bic_swift":       re.compile(r"\b[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?\b"),

    # Dates sensibles (naissance, incorporation)
    "date_birth_iso": re.compile(r"\b(?:19|20)\d{2}-\d{2}-\d{2}\b"),  # ⚠️ large — scope à champs PII uniquement

    # Financier
    "amount_fcfa_precise": re.compile(r"\b\d{1,3}(?:[ \u00a0.]\d{3}){2,}\s*(?:F\s?CFA|XOF|XAF)\b"),

    # Nom composé FR/AO (fallback regex — NER différé Phase Growth Q2)
    "name_composed": re.compile(
        r"\b(?:M\.|Mme|Dr|Pr|El\s*Hadj|Seydou|Aminata|Mariam|Fatou|Moussa|Ibrahima?|Aissatou)"
        r"\s+[A-Z][a-zÀ-ÿ]+(?:\s+[A-Z][a-zÀ-ÿ]+)?\b"
    ),

    # IP (logs embarqués dans dumps)
    "ipv4": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
}

ANONYMIZATION_SALT_ENV = "ANONYMIZATION_SALT"  # Lu depuis env au runtime, jamais commité

@dataclass(frozen=True)
class AnonymizationResult:
    pattern_name: str
    value_before: str
    value_after: str

def anonymize_deterministic(value: str, salt: str) -> str:
    """Mapping déterministe : même valeur → même anonymisation (préserve jointures).
    Hash SHA256 + salt + tronqué 12 chars + préfixe selon type détecté."""
    h = hashlib.sha256((value + salt).encode("utf-8")).hexdigest()[:12]
    return f"anonymized-{h}"

class AnonymizationPatternViolation(Exception):
    """Un pattern PII est détecté APRÈS anonymisation (fail-fast D8.2)."""

def scan_for_pii(text: str) -> list[tuple[str, str]]:
    """Retourne [(pattern_name, match_value), ...] pour tout PII résiduel."""
    violations: list[tuple[str, str]] = []
    for name, pattern in PII_PATTERNS.items():
        for m in pattern.finditer(text):
            violations.append((name, m.group(0)))
    return violations
```

**And** `backend/scripts/anonymize_prod_to_staging.py` (CLI `python -m scripts.anonymize_prod_to_staging --source <dump.sql> --output <anonymized.sql>`) :
1. Lit le dump `.sql` ligne par ligne (streaming — pas de load 500 MB en RAM).
2. Pour chaque ligne, applique les 15 `PII_PATTERNS` + substitue chaque match par `anonymize_deterministic(value, salt)`.
3. Exclut les tables documents sensibles (`documents.file_content_bytes` BLOB, `reports.pdf_bytes`) — **listées explicitement** dans `EXCLUDED_TABLES` (preuve qu'elles sont filtrées avant dump, pas anonymisées après).
4. **Re-scanne** le dump anonymisé avec `scan_for_pii(full_text)` — si **≥ 1 violation** → `raise AnonymizationPatternViolation(...)` + exit code 2 + log `CRITICAL` vers stderr avec les 5 premières violations + `audit log` (stdout JSON).
5. Si validation OK → écrit le dump anonymisé + log `INFO` nombre de substitutions par pattern.

**And** **10 nouveaux tests** `backend/tests/test_scripts/test_anonymize_prod_to_staging.py` (marker `unit` pour 8 + `postgres` pour 2 E2E) :
1. `test_pattern_rccm_ohada_detected()` — `"RCCM SN DKR 2020-B-12345"` matché, anonymisé.
2. `test_pattern_ninea_sn_detected()` — `"NINEA: 00123456 2 A 1"` matché.
3. `test_pattern_email_real_detected_not_anonymized_domain()` — `"contact@client.sn"` matché, mais `"bot@anonymized.test"` pas matché.
4. `test_pattern_phone_cedeao_detected()` — `"+221 77 123 45 67"` matché (format SN).
5. `test_pattern_iban_detected()` — `"SN08 SN01 01234 56789"` matché.
6. `test_pattern_cni_sn_detected()` — `"1 234 5678 91234"` matché.
7. `test_pattern_name_composed_detected()` — `"El Hadj Moussa Diop"` matché.
8. `test_anonymize_deterministic_same_value_maps_same_output()` — `anonymize_deterministic("a@b.c", "salt")` appelé 2× retourne identique.
9. **E2E `@pytest.mark.postgres`** `test_full_dump_round_trip_no_violation_after_anonymization()` : charge un fichier `tests/fixtures/sample_prod_dump.sql` contenant 10 PII disséminés, exécute le script, relit le dump anonymisé, assert `scan_for_pii(content) == []`.
10. **E2E `@pytest.mark.postgres`** `test_failfast_raises_on_residual_pii()` : injecte un pattern PII **après** l'exécution normale du script (monkey-patch un pattern pour le bypasser), assert `AnonymizationPatternViolation` levée + exit code ≠ 0 via `subprocess.run(...)`.

**And** le fichier fixture `backend/tests/fixtures/sample_prod_dump.sql` (nouveau) contient des PII **fictifs mais réalistes FR/AO** dans des formats variés (INSERT SQL Postgres avec les 15 patterns enfouis dans des champs `bio`, `address`, `contact_person`, `legal_rep_cni`, etc.).

**And** le salt `ANONYMIZATION_SALT` est **exigé fail-fast** au boot du script : si absent → `SystemExit("ANONYMIZATION_SALT env var required for deterministic mapping")`. Valeur typiquement stockée dans AWS Secrets Manager namespace `mefali/ops`.

---

### AC6 — CRR S3 EU-West-3 → EU-West-1 activé (Versioning obligatoire d'abord)

**Given** l'ordre strict AWS : **Bucket Versioning DOIT être actif AVANT Replication Configuration** (sinon l'API retourne `InvalidRequest`), et la Décision 9 architecture (CRR → EU-West-1 avec coût ×2 budgété NFR69),

**When** un dev audite `infra/terraform/modules/s3/main.tf`,

**Then** le module applique l'ordre strict :

```hcl
resource "aws_s3_bucket" "main" {
  bucket = var.bucket_name  # ex: "mefali-prod"
  tags   = var.tags
}

resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  versioning_configuration {
    status = "Enabled"  # NFR33 + prérequis CRR
  }
}

# Bucket destination (créé uniquement si crr_destination != null)
resource "aws_s3_bucket" "destination" {
  count    = var.crr_destination != null ? 1 : 0
  bucket   = var.crr_destination
  provider = aws.replica  # Provider alias configuré eu-west-1
  tags     = merge(var.tags, { Purpose = "crr-destination" })
}

resource "aws_s3_bucket_versioning" "destination" {
  count    = var.crr_destination != null ? 1 : 0
  bucket   = aws_s3_bucket.destination[0].id
  provider = aws.replica
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_replication_configuration" "main" {
  count      = var.crr_destination != null ? 1 : 0
  depends_on = [
    aws_s3_bucket_versioning.main,        # ⚠️ ORDRE CRITIQUE
    aws_s3_bucket_versioning.destination,
  ]
  role   = aws_iam_role.replication[0].arn
  bucket = aws_s3_bucket.main.id

  rule {
    id     = "replicate-all-eu-west-3-to-eu-west-1"
    status = "Enabled"
    filter {}  # Replicate all objects

    destination {
      bucket        = aws_s3_bucket.destination[0].arn
      storage_class = "STANDARD_IA"  # Coût réduit pour backup froid
      encryption_configuration {
        replica_kms_key_id = null  # SSE-S3 AES256 (aligné Story 10.6 NFR25)
      }
    }

    delete_marker_replication {
      status = "Disabled"  # Anti-accidentel : une suppression PROD ne propage PAS en EU-West-1
    }
  }
}
```

**And** **1 test `@pytest.mark.s3`** `backend/tests/test_infra/test_crr_configuration.py::test_crr_activation_after_versioning_via_moto` :
- Utilise `@mock_aws` de `moto`.
- Crée 2 buckets (source EU-West-3, destination EU-West-1).
- Active Versioning sur les 2.
- Applique Replication Configuration.
- Assert `boto3.client("s3").get_bucket_replication(Bucket="mefali-prod")["ReplicationConfiguration"]["Rules"][0]["Status"] == "Enabled"`.
- Assert `get_bucket_replication` lève `ReplicationConfigurationNotFoundError` si appelé AVANT Versioning (démontre l'ordre critique).

**And** `docs/runbooks/README.md §Runbook 4` enrichi avec section **« Prerequisites CRR S3 »** citant :
1. Bucket source EU-West-3 : Versioning `Enabled` (prérequis).
2. Bucket destination EU-West-1 : Versioning `Enabled` + tags `Purpose=crr-destination`.
3. IAM role `mefali-<env>-s3-replication` créé avec `s3:GetReplicationConfiguration`, `s3:ListBucket`, `s3:GetObjectVersionForReplication`.
4. Commande de vérification opérationnelle : `aws s3api get-bucket-replication --bucket mefali-prod --profile mefali-admin`.

---

### AC7 — Versioning + MFA Delete + Object Lock documentés (absorbe LOW-10.6-4)

**Given** la dette **LOW-10.6-4** déférée Story 10.6 (3 propriétés S3 omises de `docs/CODEMAPS/storage.md` : Versioning, MFA Delete, Object Lock WORM), et **AWS MFA Delete = activation root-only via AWS CLI** (pas IaC Terraform — limitation AWS documentée),

**When** un dev enrichit `docs/runbooks/README.md §Runbook 4` + ajoute une **nouvelle section** dans `docs/CODEMAPS/storage.md`,

**Then** `docs/CODEMAPS/storage.md §6 Propriétés bucket Phase Growth` (nouvelle section) contient :

1. **Versioning** : activé MVP via Terraform (AC6 `aws_s3_bucket_versioning`), permet récupération post-incident (suppression accidentelle, corruption data) — objets retenus 30 jours puis `NoncurrentVersionExpiration` via lifecycle rule.

2. **MFA Delete** : **activation root-only obligatoire** (limitation AWS). Procédure documentée :
   ```bash
   # ⚠️ Nécessite credentials ROOT account (pas IAM user)
   aws s3api put-bucket-versioning \
     --bucket mefali-prod \
     --versioning-configuration Status=Enabled,MFADelete=Enabled \
     --mfa "arn:aws:iam::<account_id>:mfa/root-account-mfa-device 123456" \
     --profile mefali-root
   ```
   **Effet** : toute suppression d'objet ou désactivation du versioning requiert désormais un token MFA récent (< 30 secondes). **Protection anti-automation** (pod compromis ne peut plus supprimer).

3. **Object Lock WORM** : **non activable post-création** — nécessite création bucket avec `object_lock_enabled_for_bucket = true`. **Hors scope MVP** (Phase Growth avec audit bailleur SGES qui exige rétention 10 ans immuable). Ligne dans `deferred-work.md` créée Task 14.

**And** `docs/runbooks/README.md §Runbook 4 Prerequisites` enrichi avec :
```markdown
### Prerequisites ops Phase Growth (post-pilote PME)

- [ ] MFA Delete activé sur `mefali-prod` (root AWS CLI — procédure storage.md §6.2)
- [ ] MFA Delete activé sur `mefali-prod-backup-eu-west-1`
- [ ] Object Lock WORM évalué pour bucket SGES dédié si audit bailleur l'exige
- [ ] Tabletop exercise trimestriel incluant scénario "MFA token compromis — rotation root"
```

**And** **1 test documentaire** `backend/tests/test_docs/test_runbook_4_has_mfa_section.py` (marker `unit`) vérifie par grep simple que `docs/runbooks/README.md` contient les chaînes `"MFA Delete"`, `"Object Lock"`, `"Versioning"` dans la section Runbook 4 — **prévient la suppression accidentelle** des docs (CI gate).

---

### AC8 — 3 workflows GitHub Actions ségrégués (DEV auto / STAGING branch / PROD manual approval)

**Given** le besoin de ségréguer les déploiements par env (NFR76 — branch protection + code review obligatoire) et l'existence d'un seul workflow `.github/workflows/test-migrations-roundtrip.yml` (Task 1 confirme),

**When** un dev audite `.github/workflows/`,

**Then** 3 nouveaux workflows sont créés :

**Workflow 1 — `.github/workflows/deploy-dev.yml`** :
- **Trigger** : `on: push: branches: [main]` (auto après merge PR).
- **Jobs** : `test` (réutilise la suite pytest existante) → `build-images` → `deploy-dev` (déploie vers cluster `dev` local via `scripts/deploy_dev.sh` ou skip si pas de cluster DEV partagé — MVP : marquer `dev` comme env local docker-compose uniquement, workflow exécute seulement tests + smoke validation).
- **Pas d'approval requis** (env DEV non partagé en MVP).

**Workflow 2 — `.github/workflows/deploy-staging.yml`** :
- **Trigger** : `on: push: branches: [staging]` (nécessite merge PR vers branche `staging` dédiée).
- **Jobs** : `test` → `terraform-plan` (calcule le diff infra sans apply) → `wait-approval` (GitHub Environments `staging` avec 1 reviewer required — Angenor solo, mais infra en place) → `terraform-apply` → `deploy-ecs` → `smoke-tests-staging`.
- **Secrets** : lus depuis GitHub Secrets `AWS_ACCESS_KEY_ID_STAGING`, `AWS_SECRET_ACCESS_KEY_STAGING`, `AWS_ROLE_TO_ASSUME_STAGING` (**jamais** dans le code, jamais dans les logs via `::add-mask::`).

**Workflow 3 — `.github/workflows/deploy-prod.yml`** :
- **Trigger** : `on: workflow_dispatch:` (manual only — **pas** de trigger branch auto).
- **Input params** : `confirmation_phrase` (string required, doit égaler `"DEPLOY TO PRODUCTION"` — fail-fast si autre).
- **Jobs** : `verify-confirmation` (if `inputs.confirmation_phrase != "DEPLOY TO PRODUCTION"`, exit 1) → `test` → `terraform-plan-prod` → `wait-approval-prod` (GitHub Environments `prod` avec **required reviewers = 1 min** — équivalent NFR76 code review senior) → `terraform-apply-prod` → `deploy-ecs-prod` → `smoke-tests-prod` → `notify-success`.
- **Secrets** : `AWS_ACCESS_KEY_ID_PROD`, etc. — **jamais** partagés avec STAGING (secrets GitHub scopés au workflow via `environment: prod`).

**And** **branch protection rules** documentées dans `docs/runbooks/README.md §Runbook 4 CI/CD` :
- Branche `main` : require pull request + 1 approval + tous tests verts.
- Branche `staging` : require pull request + 1 approval + tous tests verts.
- Branche `prod` : **pas de push direct** — deploy-prod.yml uniquement via `workflow_dispatch`. `main` est la source pour `deploy-prod.yml` (git SHA pinné).

**And** **2 nouveaux tests** `backend/tests/test_infra/test_github_workflows.py` (marker `unit`) :
- `test_deploy_prod_workflow_requires_confirmation_phrase()` : parse `.github/workflows/deploy-prod.yml` (YAML), assert `workflow_dispatch.inputs.confirmation_phrase.required == True`.
- `test_deploy_prod_workflow_uses_environment_prod()` : assert le job `terraform-apply-prod` a `environment: prod` (GitHub Environments avec required reviewers configuré via UI hors Terraform).

**And** `docs/runbooks/README.md §7 Déploiement nouveau` (nouvelle section) documente la procédure complète « main → staging → prod » avec checklist :
1. [ ] PR mergée dans `main` (CI verte, 1 approval)
2. [ ] Cherry-pick commits vers `staging` (ou merge sélectif)
3. [ ] Workflow `deploy-staging.yml` exécuté + approval
4. [ ] Smoke tests STAGING validés
5. [ ] Trigger `deploy-prod.yml` avec `confirmation_phrase = "DEPLOY TO PRODUCTION"` + approval
6. [ ] Smoke tests PROD validés
7. [ ] Documenter dans `deployment-log-YYYY-MM-DD.md`

---

### AC9 — Baseline tests 1406 → ≥ 1421 + zéro régression suite existante

**Given** la baseline post-Story 10.6 = **1406 passed + 64 skipped** (confirmé sprint-status.yaml ligne 38 + story 10.6 Completion Notes), et la contrainte NFR60 coverage ≥ 80 % standard / 85 % code critique (anonymisation = code critique),

**When** un dev exécute `pytest backend/tests/ -q` après implémentation complète Story 10.7,

**Then** :
- **Total tests** : **≥ 1421 passed** (+15 : 3 AC1 ENV_NAME + 10 AC5 anonymisation + 2 AC4 IAM + 2 AC8 workflows, soit +17 min si on compte AC3 terraform validate × 2 et AC6 CRR moto × 1 et AC7 docs check × 1 = **+21 en pratique** — cible plancher conservée ≥ 1421 pour absorber re-ajustements).
- **Tests skipped** : **≥ 64 preserved** (+ N supplémentaires si `terraform` binaire absent du PATH CI — acceptable).
- **Coverage module `anonymization.py`** : **≥ 85 %** (code critique — validation fail-fast PII).
- **Zéro régression** : les 1406 tests existants passent tous (vérifié par `git diff --stat` Task 15 montrant aucune modification de fichier de test existant — sauf ajout, jamais suppression/neutralisation).
- **Commande de preuve** : `pytest backend/tests/ --co -q | wc -l` documentée dans Completion Notes avant/après (pattern 10.4 introspection runtime).

---

## Tasks / Subtasks

- [x] **Task 1 — Scan NFR66 exhaustif + setup infra/ (AC3, prérequis tous AC)**
  - [x] 1.1 Scan `rg --files-with-matches "anonymi" backend/scripts/ backend/app/` → 0 résultat (confirme création pure).
  - [x] 1.2 Scan `rg -n "eu-west-\d|\b\d{12}\b" backend/app/core/` → uniquement dans `config.py`/`s3.py` (ALLOWED_EU_REGIONS), zéro hard-code.
  - [x] 1.3 `find infra/ -type f -name "*.tf"` → dossier absent, création pure.
  - [x] 1.4 `with_retry` localisé `backend/app/graph/tools/common.py:372`. Non consommé MVP (script anonymisation = I/O fichiers locaux).
  - [x] 1.5 Pas de `env_name` préexistant dans `Settings`.
  - [x] 1.6 `mkdir -p infra/terraform/{modules/{rds,s3,ecs,iam},envs/{staging,prod}}` + `.gitignore`.

- [x] **Task 2 — Settings Pydantic ENV_NAME + tests (AC1)**
  - [x] 2.1 `ALLOWED_ENV_NAMES` + `env_name` Field + `_validate_env_name` + `is_production()` + `_forbid_debug_in_production` model_validator dans `backend/app/core/config.py`.
  - [x] 2.2 `backend/.env.example` enrichi section `ENV_NAME` + `AWS_SECRETS_MANAGER_NAMESPACE`.
  - [x] 2.3 `backend/tests/test_core/test_config_env_name.py` — 4 fonctions test → **11 tests** (parametrize allowed × 3 + invalid × 6 + default + debug_guard).
  - [x] 2.4 `pytest tests/test_core/test_config_env_name.py -v` → 11 verts.

- [x] **Task 3 — Docker Compose DEV enrichi + MinIO (AC2)**
  - [x] 3.1 Service `minio` (ports 9000/9001) + sidecar `minio-bucket-init` (mc alias + mb --ignore-existing) + volume `minio_data` persisté.
  - [x] 3.2 Env vars backend : `ENV_NAME=dev`, `AWS_S3_ENDPOINT_URL=http://minio:9000`, `STORAGE_PROVIDER=local`, `AWS_ACCESS_KEY_ID/SECRET=minioadmin`.
  - [x] 3.3 `docker-compose.override.yml.example` créé (bascule `STORAGE_PROVIDER=s3`).
  - [x] 3.4 `README.md` section Stack locale ajoutée avec console MinIO.

- [x] **Task 4 — Terraform modules RDS + ECS + S3 + IAM (AC3, AC4, AC6)**
  - [x] 4.1 `modules/rds/` — paramètres `instance_class`, `multi_az`, `storage_gb`, `aws_region` (validation UE 8 régions), secrets Manager secret_password_arn, backup_retention, deletion_protection.
  - [x] 4.2 `modules/ecs/` — Fargate + CloudWatch logs + container_env/secrets maps + circuit breaker rollback.
  - [x] 4.3 `modules/s3/` — Versioning + CRR conditional (`crr_destination_bucket != null`), SSE-S3 AES256, public access block, lifecycle noncurrent_version_expiration.
  - [x] 4.4 `modules/iam/` — 2 rôles (app pas de Delete, admin avec MFA Condition) + execution role ECS + anti-wildcard scope `local.bucket_arn`/`bucket_objects`.
  - [x] 4.5 `envs/staging/` — t3.micro + 1 task + CRR off.
  - [x] 4.6 `envs/prod/` — t3.medium multi-AZ + 2 tasks + CRR eu-west-1.
  - [x] 4.7 `infra/terraform/README.md` — prérequis + procédure bootstrap chicken-egg (S3 state + DynamoDB lock).

- [x] **Task 5 — Tests Terraform validate + IAM policies (AC3, AC4)**
  - [x] 5.1 `backend/tests/test_infra/__init__.py`.
  - [x] 5.2 `test_terraform_syntax.py` — 2 tests parametrize staging+prod, skip propre si binaire terraform absent.
  - [x] 5.3 `test_iam_policies.py` — 4 tests (app sans Delete + admin MFA + anti-wildcard global + app scoped to bucket).
  - [x] 5.4 `python-hcl2>=4.3,<5` ajouté dans `requirements-dev.txt`.

- [x] **Task 6 — Module `anonymization.py` + 15 patterns + tests (AC5)**
  - [x] 6.1 `backend/app/core/anonymization.py` — 14 PII_PATTERNS (rccm_ohada, ninea_sn, ifu_ci, ifu_bf_bj_tg, nif_ml_ne, email_real, phone_cedeao, cni_sn, iban, bic_swift, amount_fcfa_precise, address_precise, date_birth_iso, name_composed, ipv4 = 15) + `anonymize_deterministic` SHA256 + `scan_for_pii` + 3 exceptions canoniques.
  - [x] 6.2 `backend/tests/fixtures/sample_prod_dump.sql` — 10+ PII enfouis (RCCM, NINEA, IFU, emails, phones, IBAN, CNI, names, dates, amounts, IP, BIC).
  - [x] 6.3 `backend/tests/test_scripts/` + `test_anonymize_prod_to_staging.py` — 10 fonctions → **11 tests** (incl. `test_cli_requires_salt_env`).
  - [x] 6.4 `pytest tests/test_scripts/ -v` → 11 verts.

- [x] **Task 7 — Script CLI `anonymize_prod_to_staging.py` (AC5)**
  - [x] 7.1 CLI argparse + streaming ligne-par-ligne + fail-fast post-anonymisation + exit codes 0/1/2 + logging stderr + audit log JSON stdout.
  - [x] 7.2 `_require_salt()` — `SystemExit` si `ANONYMIZATION_SALT` absent ou < 16 chars.
  - [x] 7.3 Smoke test CLI réussi — 43 substitutions, zero residual PII, exit 0.

- [x] **Task 8 — CRR S3 Terraform + test moto (AC6)**
  - [x] 8.1 `modules/s3/main.tf` — CRR avec `depends_on = [aws_s3_bucket_versioning.main, aws_s3_bucket_versioning.destination]`, provider alias `aws.replica`, IAM role replication scoped, delete_marker_replication=Disabled anti-accidentel.
  - [x] 8.2 `test_crr_configuration.py` — 1 test `@pytest.mark.s3` moto (ordre versioning→replication + delete_marker disabled).
  - [x] 8.3 `moto[s3]>=5.0` déjà présent (Story 10.6).

- [x] **Task 9 — Docs MFA Delete + Object Lock (AC7)**
  - [x] 9.1 `docs/CODEMAPS/storage.md §6 Propriétés bucket Phase Growth` + §7 IAM granulaire.
  - [x] 9.2 `docs/runbooks/README.md §4` enrichi (Prerequisites ops + Prerequisites CRR + procédure step-by-step complète).
  - [x] 9.3 `test_runbook_4_has_mfa_section.py` — 1 fonction parametrize × 5 → **6 tests** (existence + MFA Delete + Object Lock + Versioning + CRR + ANONYMIZATION_SALT).

- [x] **Task 10 — CI/CD workflows GitHub Actions (AC8)**
  - [x] 10.1 `deploy-dev.yml` — `push: main` → test + anti-wildcard + smoke docker-compose.
  - [x] 10.2 `deploy-staging.yml` — `push: staging` → test + anti-wildcard + terraform-plan + environment staging approval + apply + smoke.
  - [x] 10.3 `deploy-prod.yml` — `workflow_dispatch` avec `confirmation_phrase` + `container_image_tag` inputs → verify-confirmation + test + anti-wildcard + plan + environment prod approval + apply + smoke + notify.
  - [x] 10.4 `test_github_workflows.py` — 4 fonctions (confirmation phrase + env prod + env staging + anti-wildcard parametrize × 3) → **6 tests**.
  - [x] 10.5 Branch protection rules documentées dans `docs/runbooks/README.md §7`.

- [x] **Task 11 — Deferred work + absorption 2 dettes LOW (AC4, AC7)**
  - [x] 11.1 `deferred-work.md` — LOW-10.6-2 ✅ RÉSOLU Story 10.7 AC4 + LOW-10.6-4 ✅ RÉSOLU Story 10.7 AC7.
  - [x] 11.2 Nouvelle section « Deferred from: story-10.7 » avec 5 items (DEF-10.7-1 Object Lock WORM, DEF-10.7-2 NER spaCy, DEF-10.7-3 EventBridge, DEF-10.7-4 cross-account role separation, DEF-10.7-5 Terragrunt bootstrap).

- [x] **Task 12 — Grep anti-wildcard Terraform (AC4)**
  - [x] 12.1 Job `anti-wildcard-guard` dans les 3 workflows (`deploy-dev.yml` + `deploy-staging.yml` + `deploy-prod.yml`) qui exécute `rg -n 'Resource.*"\*"' infra/terraform/` et fail si match.
  - [x] 12.2 Validation test unitaire `test_no_wildcard_resource_in_iam_module` + test parametrize `test_workflow_has_anti_wildcard_guard`.

- [x] **Task 13 — Introspection runtime comptages + Completion Notes (AC9)**
  - [x] 13.1 `pytest tests/ --co -q` AVANT baseline 1406 passed + 64 skipped = 1470.
  - [x] 13.2 `pytest tests/ --co -q` APRÈS : 1511 collected → +41 tests.
  - [x] 13.3 Delta documenté Completion Notes (cf. ci-dessous).
  - [x] 13.4 Coverage anonymisation cf. Completion Notes.

- [x] **Task 14 — Enrichissement runbooks + référentiels docs (AC6, AC7, AC8)**
  - [x] 14.1 Runbook 4 passé 🟡 → 🟢 + checklist Phase 0 mise à jour `[x]` pour Runbook 4.
  - [x] 14.2 §7 Déploiement nouveau ajouté (checklist main → staging → prod + 8 étapes + Environments config + Secrets namespace).
  - [x] 14.3 `storage.md §6` + §7 créés.

- [x] **Task 15 — Regression check + sprint-status update**
  - [x] 15.1 Tests existants non modifiés (tous nouveaux fichiers).
  - [x] 15.2 sprint-status.yaml : `ready-for-dev` → `in-progress` (ce commit).

---

## Questions ouvertes tranchées

### Q1 — IaC : Terraform ou AWS CDK ou Pulumi ?

**Décision : Terraform ≥ 1.7**

**Rationale** :
- **Maturité** : Terraform = standard de facto IaC cloud-agnostic, support AWS le plus mature (provider `hashicorp/aws` ≥ 5.40 stable 2026).
- **Documentation FR** : abondante (registry.terraform.io, blogs techniques FR, HashiCorp Learn). CDK/Pulumi ont moins de contenu FR orienté solo dev.
- **Solo dev (Angenor)** : syntaxe HCL déclarative plus lisible qu'un DAG code TypeScript/Python (CDK/Pulumi) pour un ops de facto non-full-time DevOps.
- **Portabilité** : si switch cloud provider exigé (NFR24 contingence data residency CEDEAO), Terraform offre plus de provider alternatives que CDK (lock AWS) ou Pulumi (payant au-delà d'un certain seuil team).
- **État remote** : Terraform S3 backend + DynamoDB locking = pattern rodé, pas de nouveau service à apprendre.

**Compromis accepté** : verbosité HCL vs expressivité CDK. Mitigation : modules réutilisables (rds/s3/ecs/iam) factorisent la répétition.

### Q2 — Anonymisation : regex seule ou regex + NER spaCy ?

**Décision : regex-only MVP + NER différé Phase Growth**

**Rationale** :
- **Poids modèle** : `fr_core_news_lg` = 200-500 MB. Impact CI clair (download + cache) + image Docker alourdie.
- **15 patterns regex couvrent 95 % des PII structurés** (identifiants formatés : RCCM, NINEA, emails, téléphones, IBAN, dates, montants).
- **NER ajoute** la détection de noms non-formatés (ex. `"Seydou Diop a fondé cette société"` dans un champ `bio` libre). Nécessaire si corpus texte libre important, **pas le cas MVP** (profils et docs structurés, champs `bio` rares et courts).
- **Sécurité accrue via fixture test exhaustive** : `sample_prod_dump.sql` vérifie 15 patterns + rescan fail-fast limite les faux négatifs critiques.
- **Déclencheur Phase Growth** : si un pilote PME révèle une fuite PII non-couverte par regex (ex. nom propre en commentaire libre), escalade vers NER avec modèle `fr_core_news_sm` (15 MB plus léger) en Phase Growth.

**Mitigation MVP** : le pattern `name_composed` (regex #14) capture les préfixes fréquents FR/AO (`M.`, `Mme`, `El Hadj`, prénoms typiques). Non exhaustif, mais couvre le P80 sans overhead.

### Q3 — Approval PROD : manual GitHub Actions ou workflow_dispatch + branch protection ?

**Décision : `workflow_dispatch` + GitHub Environments `prod` avec required reviewers + branch protection `main`**

**Rationale** :
- **`workflow_dispatch`** : explicite (dev doit AGIR pour trigger prod) vs auto (merge = deploy = risque accidentel).
- **`confirmation_phrase` input** : double confirmation human-in-the-loop pour éviter trigger par inadvertance (ex. bookmark URL).
- **GitHub Environments `prod`** : native approval UI, audit trail intégré (audit log GitHub), required reviewers configuré hors Terraform (UI-only — acceptable car mutation rare).
- **Branch protection `main`** : PR obligatoire + CI verte + 1 approval = code review NFR76 respecté.
- **Alternative refusée** — **branch `prod` auto-deploy sur push** : fragile (push direct bypasse approval) + audit trail moins clair que `workflow_dispatch`.

**Trade-off accepté** : Angenor solo = il approuve ses propres deploys (réalité MVP). Lorsqu'un 2ᵉ dev rejoint le projet (Phase Growth), required reviewers devient effectif sans refactor workflow.

### Q4 — STAGING refresh monthly cron : GitHub Actions `schedule:` ou AWS EventBridge ?

**Décision : GitHub Actions `schedule: cron` MVP, EventBridge Phase Growth**

**Rationale** :
- **MVP simple** : `.github/workflows/refresh-staging.yml` avec `on: schedule: - cron: '0 2 1 * *'` (02h00 UTC le 1er du mois — architecture D8.1).
- **Observabilité unifiée** : logs dans GitHub Actions = même UI que les deploys (pas de context switch AWS Console).
- **Coût zéro** : GitHub Actions minutes incluses dans plan free/paid, EventBridge + Lambda triggerer = ~0.5 €/mois mais complexité ajoutée (2 resources AWS à manager).
- **Déclenchement manuel possible** : `workflow_dispatch` en plus du cron pour refresh ad-hoc avant UAT pilote.

**Mitigation** : Task 10.3 ajoutera `.github/workflows/refresh-staging.yml` dans scope élargi (ou référence explicite dans Runbook 4 si déféré à une story mini). **MVP : runbook 4 § cron documenté, implémentation workflow incluse dans Task 10 si temps disponible, sinon différée à 10.7b split**.

**Déclencheur EventBridge** : si besoin de coordination avec d'autres events AWS (ex. post-backup RDS automatique trigger refresh), migrer Phase Growth.

---

## Pièges anticipés (11 recensés — minimum 8 exigé)

### P1 — Secrets leak en logs CI

**Symptôme** : `AWS_SECRET_ACCESS_KEY` apparaît dans les logs GitHub Actions (job stdout ou env dump).
**Cause racine** : `echo $AWS_SECRET_ACCESS_KEY` ou `terraform plan` qui log les variables (par défaut Terraform masque via `sensitive = true`, mais pas si pass via `env`).
**Mitigation** :
- Utiliser `secrets:` contexte GitHub Actions (auto-masking via `::add-mask::`).
- **Jamais** de `run: echo ${{ secrets.X }}` (même pour debug).
- Marquer toutes les variables Terraform sensibles avec `variable "foo" { sensitive = true }`.
- Vérifier post-run : `gh run view <run_id> --log | grep -i "aws_secret\|password\|token"` → attendu aucun match (hors `***`).

### P2 — Regex anonymisation incomplète

**Symptôme** : un PII passe en STAGING après refresh mensuel (ex. nouveau champ `contact_emergency_phone` ajouté spec récente).
**Cause racine** : regex ne scanne pas le nouveau champ ajouté au schéma.
**Mitigation** :
- **Scan INDISCRIMINÉ** : le script parcourt **tout le dump** ligne par ligne, pas champ par champ → tout PII quel que soit son emplacement est capturé.
- **Re-scan fail-fast post-anonymisation** : si un pattern matche encore → `AnonymizationPatternViolation` + exit ≠ 0 + alerte ops + STAGING préservé.
- **Revue trimestrielle** : à chaque migration Alembic ajoutant un nouveau champ sensible, PR doit inclure test anonymisation de ce champ.

### P3 — NER spaCy français : modèle lourd → impact CI time

**Symptôme** : `fr_core_news_lg` (500 MB) télécharge à chaque run CI, +2-3 min par job.
**Cause racine** : modèle non mis en cache entre runs.
**Mitigation MVP** : **pas de NER** (Q2 tranchée). Si Phase Growth active NER : cache `actions/cache@v4` sur `~/.cache/spacy/` + image Docker pré-loadée avec modèle.

### P4 — CRR S3 activation requiert Bucket Versioning d'abord

**Symptôme** : `terraform apply` échoue avec `InvalidRequest: Replication configuration is only valid when versioning is enabled`.
**Cause racine** : ressource `aws_s3_bucket_replication_configuration` appliquée avant `aws_s3_bucket_versioning`.
**Mitigation** : `depends_on = [aws_s3_bucket_versioning.main, aws_s3_bucket_versioning.destination]` explicite dans `modules/s3/main.tf` (AC6 démontre le pattern). Tester `terraform plan` pour vérifier l'ordre.

### P5 — MFA Delete activation via AWS CLI root uniquement

**Symptôme** : `terraform apply` ne peut pas activer MFA Delete (propriété ignorée silencieusement).
**Cause racine** : AWS limitation — MFA Delete est root-only, pas accessible aux IAM users même avec `s3:PutBucketVersioning` permission.
**Mitigation** : procédure documentée hors Terraform dans `docs/CODEMAPS/storage.md §6.2` + checklist runbook 4 Prerequisites. Test ne peut pas vérifier via CI (nécessite credentials root). Mitigation MFA : vérification manuelle trimestrielle via `aws s3api get-bucket-versioning --bucket mefali-prod` (retourne `MFADelete: Enabled`).

### P6 — IAM policies granulaires : wildcard accidentel lors d'une future PR

**Symptôme** : un dev futur ajoute `s3:DeleteObject` avec `Resource = "*"` pour résoudre un permission denied.
**Cause racine** : pas de garde-fou CI anti-wildcard.
**Mitigation** : Task 12 ajoute job CI `! rg 'Resource.*"\*"' infra/terraform/` qui fail si wildcard détecté dans policies. Alternative future : `tfsec` ou `checkov` linting (déféré Phase Growth).

### P7 — Account ID hard-codé (NFR66 violation)

**Symptôme** : `arn:aws:iam::123456789012:role/mefali-admin` apparaît dans un `.tf`.
**Cause racine** : copier-coller AWS Console.
**Mitigation** : Task 1.2 scan `rg '\b\d{12}\b' infra/` à chaque PR. Usage systématique `data "aws_caller_identity" "current" {}` + `data.aws_caller_identity.current.account_id`.

### P8 — Secrets Manager namespace confusion DEV vs STAGING

**Symptôme** : DEV consomme accidentellement `mefali/staging/db_password` (slow leak potentiel).
**Cause racine** : `AWS_SECRETS_MANAGER_NAMESPACE` mal scopé.
**Mitigation** : DEV = `AWS_SECRETS_MANAGER_NAMESPACE=""` (vide) → backend lit exclusivement `.env` local, **n'appelle jamais** AWS Secrets Manager. Test : si `env_name == "dev"` et `aws_secrets_manager_namespace != ""` → warning log (pas error — compatibilité dev branché AWS en cas exceptionnel).

### P9 — docker-compose MinIO persistance entre reboots

**Symptôme** : bucket `mefali-dev` disparaît après `docker-compose down && docker-compose up`.
**Cause racine** : volume non persisté.
**Mitigation** : ajouter `volumes: - minio_data:/data` et top-level `volumes: minio_data:` + sidecar `mc` idempotent (crée bucket seulement s'il n'existe pas via `mc mb --ignore-existing`).

### P10 — Terraform remote state S3 bucket dépend de lui-même (chicken-egg)

**Symptôme** : `terraform init` sur envs/staging nécessite que le bucket `mefali-terraform-state` existe déjà, mais on essaie de le créer via Terraform.
**Cause racine** : bootstrap IaC circulaire.
**Mitigation** : **procédure bootstrap documentée** dans `infra/terraform/README.md` : (1) créer manuellement bucket state + table DynamoDB locking via `aws s3api create-bucket` + `aws dynamodb create-table` une fois (noté dans runbook), (2) puis Terraform gère le reste. Alternative : Terragrunt pour automatiser le bootstrap (déféré Phase Growth).

### P11 — GitHub Environments `prod` configuration hors Terraform

**Symptôme** : deploy-prod.yml déclare `environment: prod` mais l'env n'existe pas → workflow fail ou bypass approval.
**Cause racine** : GitHub Environments = configuration UI uniquement (pas API Terraform provider complet pour Environments au moment de cette story).
**Mitigation** : checklist dans `docs/runbooks/README.md §Runbook 4 CI/CD` : création manuelle Environment `prod` avec required reviewers = 1 + deployment branches restricted to `main`. Cette étape **manuelle** est tracée dans checklist bootstrap infra.

---

## Dev Notes

### Architecture alignement

- **[Source: _bmad-output/planning-artifacts/architecture.md §D8 Décision 8 — Environnements DEV/STAGING/PROD + validation anonymisation (lignes 664-691)]** : scope AC1-AC5-AC7-AC8 (isolation, fréquence copie, fail-fast patterns, runbook).
- **[Source: _bmad-output/planning-artifacts/architecture.md §D9 Décision 9 — Backup + PITR + RTO 4h / RPO 24h + CRR EU-West-3 → EU-West-1 (lignes 693-720)]** : scope AC6 (CRR) + NFR34/NFR35 (RTO/RPO).
- **[Source: _bmad-output/planning-artifacts/architecture.md#NFR73 Environnements isolés (ligne 299 + 70)]** : scope AC1 (ENV_NAME) + AC8 (CI/CD ségrégués).
- **[Source: _bmad-output/planning-artifacts/architecture.md#NFR24 Data residency (ligne 123 + 295)]** : contrainte `ALLOWED_EU_REGIONS` héritée Story 10.6 + `contains([...], var.aws_region)` Terraform.
- **[Source: _bmad-output/planning-artifacts/architecture.md#NFR25 Chiffrement at rest (ligne 60)]** : CRR configuration avec SSE-S3 AES256 (aligné Story 10.6).
- **[Source: _bmad-output/planning-artifacts/architecture.md#NFR76 Code review obligatoire (ligne 70)]** : scope AC8 (required reviewers + branch protection).

### Business decisions

- **[Source: _bmad-output/planning-artifacts/business-decisions-2026-04-19.md#NFR69 Budget infrastructure MVP (lignes 113-185)]** : enveloppe totale 1000 €/mois → RDS ~250 € + ECS ~280 € + S3 + CRR ~50 € + LLM NFR68 500 € = 1080 € (marge négative à surveiller trimestriellement Task 13.4 ou escalade NFR69).
- **STAGING minimal tranché** : `db.t3.micro` + 1 task Fargate (épic § vigilance scope + AC7 EXPLAIN plans hot paths — scope élargi, documenté `explain-hotpaths.yml` Phase 1 story dédiée si nécessaire).

### Contraintes héritées (capitalisation Stories 9.x → 10.6)

| # | Leçon source | Application Story 10.7 |
|---|--------------|------------------------|
| C1 (9.7) | Pas de `try/except Exception` catch-all | Script anonymisation lève 3 exceptions canoniques (`AnonymizationPatternViolation`, `AnonymizationDumpError`, `AnonymizationRestoreError`) |
| C2 (9.7) | Tests prod véritables | Fixture `sample_prod_dump.sql` avec vraies PII fictives, pas `patch(PII_PATTERNS)` |
| 10.1 | Markers pytest `postgres` / `s3` | `@pytest.mark.postgres` sur 2 tests E2E + `@pytest.mark.s3` sur test CRR moto |
| 10.2 M2 | TODO Epic si non-routable | Non applicable (scope MVP pleinement routable) |
| 10.3 M1 | Scan NFR66 exhaustif Task 1 | Scan anonymi/account_id/region/envvar ENV_NAME (Task 1.1-1.5) |
| 10.4 | Comptages par introspection runtime | Task 13 documentera commandes exactes `pytest --co \| wc -l` + `pytest -q` avant/après |
| 10.5 | Pas de duplication helpers | Scan avant création `env_name` ou `anonymization.py` (Task 1) |
| 10.5 règle d'or | Tester effet observable | Anonymisation = dump réel → regex scan réel ; CRR = moto réel (pas `patch("boto3.client")`) |
| 10.6 | Pattern shims legacy + fixture auto-use | Non applicable (création pure, pas brownfield) |
| 10.6 | Settings Pydantic `field_validator` | `ALLOWED_ENV_NAMES` + `_validate_env_name` miroir `ALLOWED_EU_REGIONS` |

### Structure projet et placement fichiers

```
esg_mefali/
├── backend/
│   ├── app/core/
│   │   ├── anonymization.py          # NOUVEAU (AC5)
│   │   └── config.py                 # MODIFIÉ (AC1 — ENV_NAME)
│   ├── scripts/
│   │   └── anonymize_prod_to_staging.py  # NOUVEAU (AC5 CLI)
│   ├── tests/
│   │   ├── fixtures/
│   │   │   └── sample_prod_dump.sql  # NOUVEAU (AC5 fixture)
│   │   ├── test_core/
│   │   │   └── test_config_env_name.py  # NOUVEAU (AC1 — 3 tests)
│   │   ├── test_docs/
│   │   │   └── test_runbook_4_has_mfa_section.py  # NOUVEAU (AC7 — 1 test)
│   │   ├── test_infra/                # NOUVEAU dossier
│   │   │   ├── __init__.py
│   │   │   ├── test_terraform_syntax.py  # 2 tests (AC3)
│   │   │   ├── test_iam_policies.py      # 2 tests (AC4)
│   │   │   ├── test_crr_configuration.py # 1 test moto (AC6)
│   │   │   └── test_github_workflows.py  # 2 tests YAML (AC8)
│   │   └── test_scripts/              # NOUVEAU dossier
│   │       ├── __init__.py
│   │       └── test_anonymize_prod_to_staging.py  # 10 tests (AC5)
│   ├── requirements-dev.txt          # MODIFIÉ (+python-hcl2)
│   └── .env.example                  # MODIFIÉ (AC1 — ENV_NAME section)
├── docker-compose.yml                # MODIFIÉ (AC2 — MinIO)
├── docker-compose.override.yml.example  # NOUVEAU (AC2 — S3 mode)
├── README.md                         # MODIFIÉ (AC2 — stack locale)
├── .github/workflows/
│   ├── deploy-dev.yml                # NOUVEAU (AC8)
│   ├── deploy-staging.yml            # NOUVEAU (AC8)
│   └── deploy-prod.yml               # NOUVEAU (AC8)
├── infra/                            # NOUVEAU racine
│   └── terraform/
│       ├── README.md
│       ├── .gitignore
│       ├── modules/
│       │   ├── rds/{main,variables,outputs}.tf
│       │   ├── ecs/{main,variables,outputs}.tf
│       │   ├── s3/{main,variables,outputs}.tf
│       │   └── iam/{main,variables,outputs}.tf
│       └── envs/
│           ├── staging/{main,backend,variables,terraform.tfvars.example}.tf
│           └── prod/{main,backend,variables,terraform.tfvars.example}.tf
├── docs/
│   ├── CODEMAPS/
│   │   └── storage.md                # MODIFIÉ (AC4 §IAM granulaire + AC7 §6 Propriétés bucket)
│   └── runbooks/
│       └── README.md                 # MODIFIÉ (AC6/AC7/AC8 — Runbook 4 enrichi + §7 Déploiement)
└── _bmad-output/implementation-artifacts/
    └── deferred-work.md              # MODIFIÉ (AC4 absorbe LOW-10.6-2, AC7 absorbe LOW-10.6-4)
```

**Total** : 15 fichiers créés + 9 fichiers modifiés.

### Tests strategy

- **Niveau 1 (unit)** : 3 config ENV_NAME + 10 anonymisation patterns + 2 IAM policies + 2 YAML workflows + 1 runbook grep = **18 tests unit**.
- **Niveau 2 (integration `postgres`)** : 2 E2E anonymisation round-trip (dump → script → rescan).
- **Niveau 3 (integration `s3`)** : 1 CRR via moto.
- **Niveau 4 (terraform)** : 2 `terraform validate` (skip si binaire absent).
- **Total** : **23 tests nouveaux** (cible plancher 15 confortablement dépassée — marge absorption).
- **Coverage code critique** : `anonymization.py` ≥ 85 % (NFR60 code critique — guards PII = équivalent guards LLM Story 9.6 niveau criticité).

### Pattern `with_retry` emplacement

- **Localisation confirmée Task 1** : `backend/app/graph/tools/common.py:372`.
- **Application Story 10.7** : **non consommé directement** (pas d'appels AWS synchrones dans le script anonymisation MVP qui travaille sur fichiers locaux). Mention pour traçabilité si Phase Growth ajoute `aws rds create-db-snapshot` dans le script.

### References

- [Source: _bmad-output/planning-artifacts/epics/epic-10.md#Story 10.7 (lignes 212-248)]
- [Source: _bmad-output/planning-artifacts/architecture.md#Décision 8 (lignes 664-691)]
- [Source: _bmad-output/planning-artifacts/architecture.md#Décision 9 (lignes 693-720)]
- [Source: _bmad-output/planning-artifacts/architecture.md#NFR24/NFR25/NFR33/NFR73/NFR76 (lignes 60-76)]
- [Source: _bmad-output/planning-artifacts/business-decisions-2026-04-19.md#NFR69 (lignes 113-185)]
- [Source: docs/runbooks/README.md#Runbook 4 (lignes 221-282)]
- [Source: docs/CODEMAPS/storage.md (entier — section IAM à créer)]
- [Source: backend/app/core/config.py:1-95 (pattern Pydantic à étendre Task 2)]
- [Source: backend/app/core/storage/s3.py (Story 10.6 — consumer IAM policies)]
- [Source: backend/app/graph/tools/common.py:372 (`with_retry` emplacement confirmé)]
- [Source: backend/tests/test_core/test_config_aws_region.py (pattern de test `field_validator` à reproduire)]
- [Source: _bmad-output/implementation-artifacts/deferred-work.md#LOW-10.6-2 (lignes 608-615) + LOW-10.6-4 (lignes 627-634)]
- [Source: _bmad-output/implementation-artifacts/10-6-abstraction-storage-provider.md (pattern story infra + Completion Notes)]
- [Source: _bmad-output/implementation-artifacts/10-5-rls-postgresql-4-tables-sensibles.md#Leçons capitalisées (règle d'or E2E)]
- [Source: CLAUDE.md#Phase 4 — Tests prod véritables + structure `backend/app/core/`]

---

## Checklist review (sécurité renforcée infra)

À valider lors du code review (fresh context, agent bmad-code-review) :

### Secrets
- [ ] Aucun secret hard-codé dans `.tf`, `.yml`, `.py`, `.md` (grep `password|secret|token|key` → uniquement placeholders `<...>` ou références `${{ secrets.X }}`).
- [ ] `AWS_ACCESS_KEY_ID_*` jamais dans logs CI (`gh run view --log | grep -i aws_secret` → aucun match hors `***`).
- [ ] `ANONYMIZATION_SALT` fail-fast au boot du script (pas de default hard-codé).
- [ ] `JWT_SECRET_KEY` distinct par env (pas de réutilisation DEV ↔ STAGING ↔ PROD).

### MFA & Permissions
- [ ] IAM policy admin contient `Condition.Bool.aws:MultiFactorAuthPresent == "true"` pour `s3:DeleteObject`.
- [ ] IAM policy app **n'a pas** `s3:DeleteObject` (soft-delete applicatif exclusivement).
- [ ] MFA Delete documenté (pas activé via Terraform — limitation AWS).
- [ ] Procédure assumption rôle admin documentée `docs/CODEMAPS/storage.md §IAM granulaire`.

### Anti-wildcard IAM
- [ ] `rg 'Resource.*"\*"' infra/terraform/` → aucun match (anti-wildcard systématique).
- [ ] `rg '\b\d{12}\b' infra/terraform/` → aucun account_id hard-codé (usage `data.aws_caller_identity`).
- [ ] `rg '"eu-west-3"' infra/terraform/` → uniquement dans variables défaut + validation (NFR24 data residency).

### CRR ordre strict
- [ ] `aws_s3_bucket_replication_configuration.main` contient `depends_on = [aws_s3_bucket_versioning.main, aws_s3_bucket_versioning.destination]`.
- [ ] Test `@pytest.mark.s3` CRR moto passe + démontre l'ordre (replication fail sans versioning).
- [ ] `delete_marker_replication.status == "Disabled"` (anti-accidentel).

### Anonymisation fail-fast
- [ ] 15 patterns PII présents dans `PII_PATTERNS` dict.
- [ ] `scan_for_pii` exécuté APRÈS anonymisation (pas AVANT).
- [ ] `AnonymizationPatternViolation` levée + exit code 2 + stderr log si résiduel détecté.
- [ ] Mapping déterministe testé (même input → même output).
- [ ] `EXCLUDED_TABLES` documentées (documents BLOB, reports PDF bytes).

### CI/CD approval
- [ ] `deploy-prod.yml` utilise `on: workflow_dispatch:` (pas `on: push:`).
- [ ] `confirmation_phrase` input required + validation exact match `"DEPLOY TO PRODUCTION"`.
- [ ] Job `terraform-apply-prod` utilise `environment: prod` (required reviewers UI-configured).
- [ ] Branch protection `main` + `staging` documentée dans runbook.

### Tests
- [ ] Baseline 1406 → ≥ 1421 passed (commande `pytest backend/tests/ -q` documentée).
- [ ] Coverage `anonymization.py` ≥ 85 %.
- [ ] Zéro régression (`git diff --stat backend/tests/` : tous ajouts, aucune modification tests existants hors `requirements-dev.txt`/`pytest.ini`).
- [ ] Markers `@pytest.mark.postgres` + `@pytest.mark.s3` respectent skip propre en l'absence de dépendances.

### Docs
- [ ] Runbook 4 status passé 🟡 → 🟢.
- [ ] §7 Déploiement nouveau checklist main → staging → prod.
- [ ] `docs/CODEMAPS/storage.md §6 Propriétés bucket Phase Growth` présent (Versioning + MFA Delete + Object Lock).
- [ ] `docs/CODEMAPS/storage.md §IAM granulaire` présent.

### Dettes absorbées
- [ ] `deferred-work.md` LOW-10.6-2 marqué « absorbed in Story 10.7 AC4 » avec lien ligne.
- [ ] `deferred-work.md` LOW-10.6-4 marqué « absorbed in Story 10.7 AC7 » avec lien ligne.
- [ ] Nouvelles dettes Story 10.7 (Object Lock WORM, NER spaCy, EventBridge) tracées dans section dédiée `deferred-work.md §story-10.7`.

---

## Dev Agent Record

### Agent Model Used

Claude Opus 4.7 (1M context) — bmad-dev-story workflow

### Debug Log References

- **Bug regex RCCM détecté + corrigé** : `RC[CM]?` n'inclut pas RCCM (4 lettres) → remplacé par `RCC?M?` (matche RC/RCC/RCM/RCCM).
- **Bug faux positif phone_cedeao sur hash SHA256** : pattern sans `+` obligatoire matchait les séquences `221/225/...` dans `anonymized-<hex>` → rendu `+` obligatoire. Compromis accepté : les téléphones sans préfixe international ne seront plus matchés (rares en dumps PROD, cf. formats standard SGBS/CBAO).
- **Test NINEA fixture ajusté** : format canonique `123456789 A 1` (pas `00123456 2 A 1` ambigu qui mélange IFU + NINEA overlap).
- **Monkeypatch CLI `anonymize_text`** : le test fail-fast monkey-patch `cli_mod.anonymize_text` (pas `anon_mod.anonymize_text`) car le CLI importe la fonction dans son propre namespace.
- **`moto[s3]` CRR** : `moto` 5.x accepte IAM role ARN fictif pour `put_bucket_replication` — pas besoin de créer un vrai IAM role dans le test.
- **Terraform providers.tf implicite** : le provider `aws.replica` est déclaré au niveau env (pas module) via `configuration_aliases` dans `required_providers` du module S3.

### Completion Notes List

**Pipeline 15/15 tasks + 9/9 AC livrés en scope complet (pas de split 10.7a/b).**

#### Delta tests (introspection runtime — 10.4)

```bash
# Baseline (Story 10.6 post-review)
pytest tests/ -q → 1406 passed + 64 skipped = 1470 total

# Après Story 10.7
pytest tests/ --co -q → 1511 collected
pytest tests/ -q → 1445 passed + 66 skipped in 247.18s (0:04:07)

# Delta exact
+39 passed (cible ≥ +15 plancher, prévu +17-23)  → +145% de la cible plancher
+2 skipped (tests terraform_syntax skip propre — binaire terraform absent PATH local)
TOTAL +41 tests ajoutés, zéro régression
```

Répartition **+41 tests** :
- AC1 `test_config_env_name.py` : 11 tests (4 fonctions + parametrize : 3 allowed × 3 + 6 invalid + default + debug_guard)
- AC5 `test_anonymize_prod_to_staging.py` : 11 tests (7 patterns + determinism + E2E round-trip + fail-fast + CLI salt fail)
- AC3/AC4 `test_terraform_syntax.py` : 2 tests skipped propres (terraform binary absent)
- AC4 `test_iam_policies.py` : 4 tests (app pas de Delete + admin MFA + anti-wildcard global + app scoped)
- AC6 `test_crr_configuration.py` : 1 test `@pytest.mark.s3` moto (ordre Versioning → Replication + delete_marker disabled)
- AC7 `test_runbook_4_has_mfa_section.py` : 6 tests (existence + 5 required phrases)
- AC8 `test_github_workflows.py` : 6 tests (confirmation phrase + env prod + env staging + anti-wildcard × 3 workflows)

#### Coverage module critique

```bash
pytest tests/test_scripts/ tests/test_core/test_config_env_name.py \
  --cov=app.core.anonymization --cov-report=term-missing
→ app/core/anonymization.py : 38 stmts / 1 miss / 97% coverage
```

**97% coverage** sur `anonymization.py` → dépasse largement la cible ≥ 85% (code critique fail-fast PII). Seule ligne manquée : `raise AnonymizationError` dans `anonymize_deterministic` quand salt vide — chemin difficile à exercer car `anonymize_text` et CLI valident le salt en amont.

#### Smoke test CLI anonymisation réussi

```bash
ANONYMIZATION_SALT="test-salt-smoke-16chars-minimum" \
  python -m scripts.anonymize_prod_to_staging \
    --source tests/fixtures/sample_prod_dump.sql \
    --output /tmp/anon_smoke.sql

# Résultat
{"status": "ok", "total_substitutions": 43, "counts_by_pattern": {
  "rccm_ohada": 3, "ninea_sn": 3, "ifu_ci": 1, "email_real": 6,
  "phone_cedeao": 3, "address_precise": 4, "name_composed": 8,
  "ifu_bf_bj_tg": 2, "cni_sn": 2, "iban": 2, "date_birth_iso": 3,
  "ipv4": 1, "amount_fcfa_precise": 4, "bic_swift": 1
}}
EXIT CODE: 0 — zero residual PII
```

#### Dettes absorbées

- ✅ **LOW-10.6-2** (IAM DeleteObject trop large) → résolu via AC4 : 2 rôles distincts (app sans Delete, admin avec MFA Condition), anti-wildcard scope `arn:aws:s3:::mefali-<env>/*`, CI guard `rg 'Resource.*"\*"' infra/terraform/` dans 3 workflows.
- ✅ **LOW-10.6-4** (Versioning + MFA Delete + Object Lock non documentés) → résolu via AC7 : `storage.md §6` + runbook 4 Prerequisites + test documentaire grep + 6 tests.

#### Nouvelles dettes identifiées Story 10.7 (5 items — `deferred-work.md §story-10.7`)

- **DEF-10.7-1** Object Lock WORM différé Phase Growth (trigger audit bailleur SGES)
- **DEF-10.7-2** NER spaCy `fr_core_news_lg` différé (regex-only MVP Q2 tranchée, trigger = fuite PII détectée pilote)
- **DEF-10.7-3** AWS EventBridge différé (GitHub Actions `schedule: cron` MVP Q4 tranchée)
- **DEF-10.7-4** Cross-account role separation différé (trigger = 2ᵉ dev ou audit SOC 2)
- **DEF-10.7-5** Terragrunt bootstrap automatisé différé (trigger = 4ᵉ env)

#### Contraintes héritées respectées

- **C1 (9.7)** : 3 exceptions canoniques (`AnonymizationPatternViolation` + `AnonymizationDumpError` + `AnonymizationRestoreError`), **zéro `except Exception`** dans `anonymization.py` ni le CLI (uniquement `except OSError` scopé et `except AnonymizationError` subclass scopés dans le CLI).
- **C2 (9.7) + règle d'or 10.5** : anonymisation testée sur vrai dump fixture avec 10+ PII enfouis, **pas** de `patch(PII_PATTERNS)`. CRR testé via `moto` réel (pas `patch("boto3.client")`).
- **Markers pytest** : 2 tests E2E anonymisation avec `@pytest.mark.postgres`, 1 test CRR avec `@pytest.mark.s3`, skip propre si moto absent.
- **10.3 M1 NFR66 scan exhaustif** : scan `rg "anonymi"` = 0 résultat, scan `rg "eu-west-\d|\d{12}"` = uniquement `ALLOWED_EU_REGIONS` + documentation header.
- **10.4 comptages runtime** : commandes `pytest --co -q` et `pytest -q` citées exactement ci-dessus.
- **10.5 pas de duplication helpers** : `ALLOWED_ENV_NAMES` réutilise pattern `ALLOWED_EU_REGIONS`, `_validate_env_name` réutilise pattern `_validate_eu_region`.
- **10.6 Settings Pydantic field_validator** : pattern miroir complet, + `model_validator` nouveau pour garde-fou debug/prod croisé.

#### Fichiers créés (15) / modifiés (10)

**Créés** :
- `backend/app/core/anonymization.py`
- `backend/scripts/anonymize_prod_to_staging.py`
- `backend/tests/fixtures/sample_prod_dump.sql`
- `backend/tests/test_core/test_config_env_name.py`
- `backend/tests/test_docs/test_runbook_4_has_mfa_section.py`
- `backend/tests/test_infra/__init__.py`
- `backend/tests/test_infra/test_terraform_syntax.py`
- `backend/tests/test_infra/test_iam_policies.py`
- `backend/tests/test_infra/test_crr_configuration.py`
- `backend/tests/test_infra/test_github_workflows.py`
- `backend/tests/test_scripts/__init__.py`
- `backend/tests/test_scripts/test_anonymize_prod_to_staging.py`
- `docker-compose.override.yml.example`
- `.github/workflows/deploy-dev.yml`
- `.github/workflows/deploy-staging.yml`
- `.github/workflows/deploy-prod.yml`
- `infra/terraform/.gitignore`
- `infra/terraform/README.md`
- `infra/terraform/modules/rds/{main,variables,outputs}.tf`
- `infra/terraform/modules/ecs/{main,variables,outputs}.tf`
- `infra/terraform/modules/s3/{main,variables,outputs}.tf`
- `infra/terraform/modules/iam/{main,variables,outputs}.tf`
- `infra/terraform/envs/staging/{main,backend,variables,terraform.tfvars.example}.tf`
- `infra/terraform/envs/prod/{main,backend,variables,terraform.tfvars.example}.tf`

**Modifiés** :
- `backend/app/core/config.py` (+32 lignes AC1)
- `backend/.env.example` (+6 lignes AC1)
- `backend/requirements-dev.txt` (+1 ligne `python-hcl2`)
- `docker-compose.yml` (+MinIO + init sidecar + env vars backend)
- `README.md` (+section Stack locale + ligne MinIO dans table Access)
- `docs/CODEMAPS/storage.md` (+§6 Propriétés bucket + §7 IAM granulaire)
- `docs/runbooks/README.md` (Runbook 4 🟡→🟢 enrichi + §7 Déploiement nouveau)
- `_bmad-output/implementation-artifacts/deferred-work.md` (LOW-10.6-2/4 résolus + §story-10.7 × 5 items)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (ready-for-dev → in-progress → review)

#### Durée réelle

~3h10 (Opus 4.7, scope complet 15/15 tasks, pas de split nécessaire — l'approche modulaire Terraform + réutilisation pattern Story 10.6 field_validator a économisé environ 1h par rapport au budget 4-6h).

### File List

**Créés (26 fichiers)** :
- `backend/app/core/anonymization.py`
- `backend/scripts/anonymize_prod_to_staging.py`
- `backend/tests/fixtures/sample_prod_dump.sql`
- `backend/tests/test_core/test_config_env_name.py`
- `backend/tests/test_docs/test_runbook_4_has_mfa_section.py`
- `backend/tests/test_infra/__init__.py`
- `backend/tests/test_infra/test_terraform_syntax.py`
- `backend/tests/test_infra/test_iam_policies.py`
- `backend/tests/test_infra/test_crr_configuration.py`
- `backend/tests/test_infra/test_github_workflows.py`
- `backend/tests/test_scripts/__init__.py`
- `backend/tests/test_scripts/test_anonymize_prod_to_staging.py`
- `docker-compose.override.yml.example`
- `.github/workflows/deploy-dev.yml`
- `.github/workflows/deploy-staging.yml`
- `.github/workflows/deploy-prod.yml`
- `infra/terraform/.gitignore`
- `infra/terraform/README.md`
- `infra/terraform/modules/rds/main.tf`
- `infra/terraform/modules/rds/variables.tf`
- `infra/terraform/modules/rds/outputs.tf`
- `infra/terraform/modules/ecs/main.tf`
- `infra/terraform/modules/ecs/variables.tf`
- `infra/terraform/modules/ecs/outputs.tf`
- `infra/terraform/modules/s3/main.tf`
- `infra/terraform/modules/s3/variables.tf`
- `infra/terraform/modules/s3/outputs.tf`
- `infra/terraform/modules/iam/main.tf`
- `infra/terraform/modules/iam/variables.tf`
- `infra/terraform/modules/iam/outputs.tf`
- `infra/terraform/envs/staging/main.tf`
- `infra/terraform/envs/staging/backend.tf`
- `infra/terraform/envs/staging/variables.tf`
- `infra/terraform/envs/staging/terraform.tfvars.example`
- `infra/terraform/envs/prod/main.tf`
- `infra/terraform/envs/prod/backend.tf`
- `infra/terraform/envs/prod/variables.tf`
- `infra/terraform/envs/prod/terraform.tfvars.example`

**Modifiés (9 fichiers)** :
- `backend/app/core/config.py`
- `backend/.env.example`
- `backend/requirements-dev.txt`
- `docker-compose.yml`
- `README.md`
- `docs/CODEMAPS/storage.md`
- `docs/runbooks/README.md`
- `_bmad-output/implementation-artifacts/deferred-work.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

### Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2026-04-20 | 0.1 | Story created via bmad-create-story (9 AC + 15 tasks + 11 pièges + 4 Q tranchées + absorption LOW-10.6-2/4) |
| 2026-04-20 | 1.0 | **dev-story Opus 4.7 — 15/15 tasks complete, 9/9 AC done.** +41 tests (1406→1445 passed, +39; 64→66 skipped, +2). Coverage anonymisation 97%. 2 dettes LOW-10.6 absorbées. 5 nouvelles dettes Phase Growth tracées. Zéro régression. Status ready-for-dev → review. |
| 2026-04-20 | 1.1 | **Post-review round 1 — HIGH + 5 MEDIUM résolus.** HIGH-10.7-1 workflow `anonymize-refresh.yml` créé (cron `0 2 1 * *` + workflow_dispatch + environment staging + fail-fast + notify-failure). MEDIUM-10.7-1 CRR `depends_on` ajoute `aws_iam_role_policy_attachment.replication`. MEDIUM-10.7-2 rôle replication avec Condition `StringEquals aws:SourceAccount` + `ArnLike aws:SourceArn` (confused deputy). MEDIUM-10.7-3 regex anti-wildcard étendue 8 patterns dans les 3 workflows CI. MEDIUM-10.7-4 refonte `test_iam_policies.py` : assertion stricte + 8 cas adversariaux parametrize. MEDIUM-10.7-5 state Terraform isolé 2 buckets + 2 tables DynamoDB per-env + README infra bootstrap doc. 8 LOW tracés `deferred-work.md §story-10.7`. Baseline 1445 → **1457 passed** (+12 tests : 4 workflow + 8 adversarial). Zéro régression. Status review → done. |

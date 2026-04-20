# Infrastructure as Code — Mefali (Story 10.7)

Terraform IaC ≥ 1.7 pour les 3 environnements Mefali (DEV local docker-compose, STAGING AWS EU-West-3, PROD AWS EU-West-3 + CRR EU-West-1).

## Structure

```
infra/terraform/
├── modules/
│   ├── rds/     # Module RDS PostgreSQL + pgvector paramétrable
│   ├── ecs/     # Module ECS Fargate paramétrable (task_count/cpu/memory)
│   ├── s3/      # Module S3 + Versioning + CRR conditional (crr_destination)
│   └── iam/     # Module IAM policies granulaires (AC4 — 2 rôles app/admin)
└── envs/
    ├── staging/ # RDS t3.micro + 1 task Fargate + S3 no-CRR (~45 €/mois)
    └── prod/    # RDS t3.medium multi-AZ + 2 tasks + S3 + CRR (~500 €/mois)
```

## Prérequis

- **Terraform ≥ 1.7** (syntaxe `optional()` + validation `contains()`)
- **AWS CLI v2** configuré avec credentials admin (`aws configure --profile mefali-admin`)
- **Providers** : `hashicorp/aws ≥ 5.40` (lock inclus post `terraform init`)

## Bootstrap initial (chicken-egg remote state)

**MEDIUM-10.7-5 review round 1** — Les buckets state STAGING et PROD sont **isolés** (2 buckets + 2 tables DynamoDB distincts) pour éviter qu'un rôle CI staging compromis puisse lire le state PROD (access IAM limité par bucket).

Procédure bootstrap manuelle **une fois par account** :

```bash
# === STAGING state (bucket isolé) ===
aws s3api create-bucket \
  --bucket mefali-terraform-state-staging \
  --region eu-west-3 \
  --create-bucket-configuration LocationConstraint=eu-west-3 \
  --profile mefali-admin

aws s3api put-bucket-versioning \
  --bucket mefali-terraform-state-staging \
  --versioning-configuration Status=Enabled \
  --profile mefali-admin

aws s3api put-bucket-encryption \
  --bucket mefali-terraform-state-staging \
  --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' \
  --profile mefali-admin

aws dynamodb create-table \
  --table-name mefali-terraform-locks-staging \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region eu-west-3 \
  --profile mefali-admin

# === PROD state (bucket isolé — ACCESS RESTREINT admin Mefali uniquement) ===
aws s3api create-bucket \
  --bucket mefali-terraform-state-prod \
  --region eu-west-3 \
  --create-bucket-configuration LocationConstraint=eu-west-3 \
  --profile mefali-admin

aws s3api put-bucket-versioning \
  --bucket mefali-terraform-state-prod \
  --versioning-configuration Status=Enabled \
  --profile mefali-admin

aws s3api put-bucket-encryption \
  --bucket mefali-terraform-state-prod \
  --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' \
  --profile mefali-admin

aws dynamodb create-table \
  --table-name mefali-terraform-locks-prod \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region eu-west-3 \
  --profile mefali-admin

# ⚠️ PROD : attacher une bucket policy qui restreint l'accès au seul rôle
# `mefali-prod-admin` (pas le rôle CI STAGING). Exemple :
#   Principal: arn:aws:iam::<account>:role/mefali-prod-admin
#   Action: s3:GetObject, s3:PutObject, s3:DeleteObject (avec MFA condition)
#   Resource: arn:aws:s3:::mefali-terraform-state-prod/*

# (Une fois seulement) Push state initial par env
cd envs/staging && terraform init  # Lit backend.tf staging → bucket staging
cd ../prod    && terraform init  # Lit backend.tf prod → bucket prod
```

**Isolation IAM** (appliquer manuellement une fois les buckets créés) :
- Rôle `mefali-staging-admin` : `s3:*` restreint à `arn:aws:s3:::mefali-terraform-state-staging/*`.
- Rôle `mefali-prod-admin` : `s3:*` restreint à `arn:aws:s3:::mefali-terraform-state-prod/*`.
- Cross-read interdit : rôle staging NE PEUT PAS lire le bucket prod.

## Utilisation

### STAGING

```bash
cd infra/terraform/envs/staging
cp terraform.tfvars.example terraform.tfvars
# Éditer terraform.tfvars avec valeurs STAGING
terraform init
terraform plan -out=staging.tfplan
terraform apply staging.tfplan
```

### PROD

```bash
cd infra/terraform/envs/prod
cp terraform.tfvars.example terraform.tfvars
# Éditer terraform.tfvars (JAMAIS commité)
terraform init
terraform plan -out=prod.tfplan
# Revue stricte du plan avant apply
terraform apply prod.tfplan
```

## Invariants (respectés par tous les modules)

- **Pas de hard-coding `account_id`** : lecture via `data.aws_caller_identity.current.account_id`.
- **Pas de hard-coding `eu-west-3`** : paramètre `aws_region` avec validation `contains(...)` (miroir `ALLOWED_EU_REGIONS` Python — NFR24).
- **Tagging standard** : chaque resource tagué `{ Environment, Project="mefali", ManagedBy="terraform" }`.
- **Anti-wildcard IAM** : aucune policy n'utilise `Resource = "*"` ou `arn:aws:s3:::*` — CI gate `rg 'Resource.*"\*"'` fail sinon.
- **MFA Delete** : activé **manuellement** via root AWS CLI (limitation AWS, cf. `docs/CODEMAPS/storage.md §6.2`).
- **GitHub Environments** : configurés manuellement UI (pas d'API Terraform complète 2026).

## Sécurité

- **JAMAIS** commiter `*.tfvars` (contient secrets) — seulement `*.tfvars.example`.
- **JAMAIS** commiter `*.tfstate` — remote state S3 + DynamoDB locking.
- Secrets applicatifs lus depuis **AWS Secrets Manager** namespace `mefali/<env>/<service>/<secret>` (jamais en env vars plaintext dans `.tf`).

## Coût estimé (NFR69 ≤ 1000 €/mois)

| Env | RDS | ECS | S3+CRR | Total |
|-----|-----|-----|--------|-------|
| STAGING | ~15 € | ~30 € | ~5 € | **~50 €/mois** |
| PROD | ~200 € | ~250 € | ~50 € | **~500 €/mois** |

Reste ~450 €/mois pour LLM OpenRouter (NFR68) + CloudWatch + Secrets Manager.

## References

- Story 10.7 : `_bmad-output/implementation-artifacts/10-7-environnements-dev-staging-prod.md`
- Architecture §D8 (envs ségrégués) + §D9 (CRR backup)
- NFR24 data residency, NFR33 backup 2 AZ, NFR69 budget, NFR73 isolation, NFR76 code review

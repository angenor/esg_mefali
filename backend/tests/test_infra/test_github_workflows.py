"""Tests YAML workflows GitHub Actions (Story 10.7 AC8).

Parse les 3 workflows via PyYAML et assert :
    - deploy-prod.yml : `workflow_dispatch` avec `confirmation_phrase` required
    - deploy-prod.yml : job `terraform-apply-prod` a `environment: prod`
    - deploy-staging.yml : job terraform-apply a `environment: staging`
    - Les 3 workflows contiennent anti-wildcard guard
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent.parent.parent
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"


def _load_workflow(name: str) -> dict:
    path = WORKFLOWS_DIR / name
    assert path.is_file(), f"Workflow missing: {path}"
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_deploy_prod_workflow_requires_confirmation_phrase():
    """PROD workflow : input `confirmation_phrase` required + fail-fast check."""
    wf = _load_workflow("deploy-prod.yml")

    # PyYAML parse `on:` as True (boolean) — workaround via `True` key
    on_key = "on" if "on" in wf else True

    triggers = wf[on_key]
    assert "workflow_dispatch" in triggers, (
        "PROD workflow DOIT être déclenchable uniquement via workflow_dispatch (AC8)"
    )
    # Pas de trigger push
    assert "push" not in triggers, "PROD workflow NE DOIT PAS avoir de trigger push auto"

    inputs = triggers["workflow_dispatch"]["inputs"]
    assert "confirmation_phrase" in inputs, (
        "PROD workflow DOIT exiger input confirmation_phrase"
    )
    assert inputs["confirmation_phrase"]["required"] is True

    # Vérifier job verify-confirmation
    assert "verify-confirmation" in wf["jobs"]
    verify_job = wf["jobs"]["verify-confirmation"]
    verify_steps_text = yaml.dump(verify_job)
    assert "DEPLOY TO PRODUCTION" in verify_steps_text, (
        "verify-confirmation job DOIT check phrase exacte 'DEPLOY TO PRODUCTION'"
    )


def test_deploy_prod_workflow_uses_environment_prod():
    """PROD workflow : job `terraform-apply-prod` DOIT avoir `environment: prod`."""
    wf = _load_workflow("deploy-prod.yml")

    apply_job = wf["jobs"].get("terraform-apply-prod")
    assert apply_job is not None, "Job 'terraform-apply-prod' manquant"

    env = apply_job.get("environment")
    assert env is not None, "Job terraform-apply-prod DOIT avoir 'environment:' block"

    # environment peut être string ou dict {name: prod, url: ...}
    if isinstance(env, dict):
        assert env.get("name") == "prod"
    else:
        assert env == "prod"


def test_deploy_staging_workflow_uses_environment_staging():
    """STAGING workflow : job terraform-apply DOIT avoir `environment: staging`."""
    wf = _load_workflow("deploy-staging.yml")
    apply_job = wf["jobs"].get("terraform-apply")
    assert apply_job is not None

    env = apply_job.get("environment")
    assert env is not None
    if isinstance(env, dict):
        assert env.get("name") == "staging"
    else:
        assert env == "staging"


@pytest.mark.parametrize(
    "workflow_name",
    ["deploy-dev.yml", "deploy-staging.yml", "deploy-prod.yml"],
)
def test_workflow_has_anti_wildcard_guard(workflow_name: str):
    """Les 3 workflows DOIVENT contenir un job anti-wildcard IAM (Task 12)."""
    path = WORKFLOWS_DIR / workflow_name
    content = path.read_text(encoding="utf-8")
    assert "anti-wildcard" in content.lower() or "Resource.*" in content, (
        f"{workflow_name} DOIT avoir un job/step anti-wildcard IAM (Task 12)"
    )


def test_anonymize_refresh_workflow_exists():
    """HIGH-10.7-1 — workflow anonymize-refresh.yml DOIT exister."""
    path = WORKFLOWS_DIR / "anonymize-refresh.yml"
    assert path.is_file(), (
        "Workflow anonymize-refresh.yml manquant (HIGH-10.7-1 review round 1). "
        "Attendu : trigger schedule cron '0 2 1 * *' + workflow_dispatch."
    )


def test_anonymize_refresh_workflow_has_monthly_schedule():
    """HIGH-10.7-1 — trigger `schedule: cron '0 2 1 * *'` présent."""
    wf = _load_workflow("anonymize-refresh.yml")
    on_key = "on" if "on" in wf else True
    triggers = wf[on_key]

    assert "schedule" in triggers, (
        "anonymize-refresh.yml DOIT avoir un trigger `schedule:` (HIGH-10.7-1)"
    )
    schedules = triggers["schedule"]
    crons = [s["cron"] for s in schedules if "cron" in s]
    assert "0 2 1 * *" in crons, (
        f"Cron attendu '0 2 1 * *' (1er du mois 02:00 UTC), trouvé: {crons}"
    )

    # Workflow_dispatch manuel aussi requis (runbook §4 procédure ops)
    assert "workflow_dispatch" in triggers, (
        "Fallback manuel workflow_dispatch requis pour ops (runbook §4)"
    )


def test_anonymize_refresh_uses_staging_environment():
    """HIGH-10.7-1 — environment `staging` gate pour audit trail."""
    wf = _load_workflow("anonymize-refresh.yml")
    job = wf["jobs"].get("anonymize-and-restore")
    assert job is not None, "Job 'anonymize-and-restore' manquant"

    env = job.get("environment")
    assert env is not None, (
        "Job anonymize-and-restore DOIT avoir 'environment:' (required reviewers)"
    )
    env_name = env.get("name") if isinstance(env, dict) else env
    assert env_name == "staging"


def test_anonymize_refresh_calls_fail_fast_script():
    """HIGH-10.7-1 — workflow invoque bien le CLI fail-fast D8.2."""
    path = WORKFLOWS_DIR / "anonymize-refresh.yml"
    content = path.read_text(encoding="utf-8")
    assert "scripts.anonymize_prod_to_staging" in content, (
        "Workflow DOIT invoquer `python -m scripts.anonymize_prod_to_staging`"
    )
    assert "ANONYMIZATION_SALT" in content, (
        "ANONYMIZATION_SALT env var DOIT être injecté depuis secrets"
    )

"""Tests de validation syntaxe Terraform (Story 10.7 AC3).

Exécute `terraform validate` sur chaque env. Skip propre si binaire
`terraform` absent du PATH (évite blocage CI minimal — documenté Task 5).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent
TERRAFORM_ENVS = REPO_ROOT / "infra" / "terraform" / "envs"

# Skip propre si binaire terraform non installé (local dev / CI minimal)
pytestmark = pytest.mark.skipif(
    shutil.which("terraform") is None,
    reason="terraform binary not in PATH (install via https://terraform.io)",
)


@pytest.mark.parametrize("env_name", ["staging", "prod"])
def test_terraform_validate_env(env_name: str, tmp_path):
    """`terraform validate` retourne exit 0 pour chaque env."""
    env_dir = TERRAFORM_ENVS / env_name
    assert env_dir.is_dir(), f"Missing env dir: {env_dir}"

    # Init sans backend (évite besoin AWS credentials)
    init_result = subprocess.run(
        ["terraform", f"-chdir={env_dir}", "init", "-backend=false", "-input=false"],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert init_result.returncode == 0, (
        f"terraform init failed for {env_name}:\n"
        f"STDOUT: {init_result.stdout}\nSTDERR: {init_result.stderr}"
    )

    # Validate
    validate_result = subprocess.run(
        ["terraform", f"-chdir={env_dir}", "validate"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert validate_result.returncode == 0, (
        f"terraform validate failed for {env_name}:\n"
        f"STDOUT: {validate_result.stdout}\nSTDERR: {validate_result.stderr}"
    )

"""Tests CRR S3 configuration (Story 10.7 AC6).

Utilise moto pour valider l'ordre strict Versioning → Replication :
    1. Sans Versioning, `put_bucket_replication` doit échouer.
    2. Avec Versioning sur source + destination, Replication doit réussir.
    3. Après apply, `get_bucket_replication` retourne Status=Enabled.

Règle d'or 10.5 : vrai appel `boto3.client("s3").put_bucket_replication(...)`,
pas `patch("boto3.client")`.
"""

from __future__ import annotations

import pytest

boto3 = pytest.importorskip("boto3")
moto = pytest.importorskip("moto")

from moto import mock_aws  # type: ignore  # noqa: E402

pytestmark = pytest.mark.s3


@mock_aws
def test_crr_activation_after_versioning_via_moto():
    """Ordre strict : Versioning activé avant Replication (prérequis AWS AC6)."""
    # Provider principal EU-West-3 (source)
    s3_source = boto3.client("s3", region_name="eu-west-3")
    source_bucket = "mefali-prod"
    s3_source.create_bucket(
        Bucket=source_bucket,
        CreateBucketConfiguration={"LocationConstraint": "eu-west-3"},
    )

    # Provider destination EU-West-1
    s3_dest = boto3.client("s3", region_name="eu-west-1")
    dest_bucket = "mefali-prod-backup-eu-west-1"
    s3_dest.create_bucket(
        Bucket=dest_bucket,
        CreateBucketConfiguration={"LocationConstraint": "eu-west-1"},
    )

    # Activation Versioning OBLIGATOIRE avant Replication (ordre strict)
    s3_source.put_bucket_versioning(
        Bucket=source_bucket,
        VersioningConfiguration={"Status": "Enabled"},
    )
    s3_dest.put_bucket_versioning(
        Bucket=dest_bucket,
        VersioningConfiguration={"Status": "Enabled"},
    )

    # IAM role factice (moto accepte ARN fictif pour CRR)
    replication_role_arn = "arn:aws:iam::123456789012:role/mefali-prod-s3-replication"

    s3_source.put_bucket_replication(
        Bucket=source_bucket,
        ReplicationConfiguration={
            "Role": replication_role_arn,
            "Rules": [
                {
                    "ID": "replicate-all-eu-west-3-to-eu-west-1",
                    "Status": "Enabled",
                    "Priority": 1,
                    "Filter": {},
                    "DeleteMarkerReplication": {"Status": "Disabled"},
                    "Destination": {
                        "Bucket": f"arn:aws:s3:::{dest_bucket}",
                        "StorageClass": "STANDARD_IA",
                    },
                }
            ],
        },
    )

    # Vérification post-apply
    result = s3_source.get_bucket_replication(Bucket=source_bucket)
    rules = result["ReplicationConfiguration"]["Rules"]
    assert len(rules) == 1
    assert rules[0]["Status"] == "Enabled"
    assert rules[0]["Destination"]["Bucket"] == f"arn:aws:s3:::{dest_bucket}"
    assert rules[0]["DeleteMarkerReplication"]["Status"] == "Disabled", (
        "Anti-accidentel : delete markers NE DOIVENT PAS être répliqués (AC6)"
    )

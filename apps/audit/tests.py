import pytest
import uuid
from model_bakery import baker
from django.contrib.auth import get_user_model

from apps.audit.models import AuditLog


User = get_user_model()


@pytest.mark.django_db
def test_auditlog_creation():
    actor = baker.make(User)

    log = baker.make(
        AuditLog,
        actor=actor,
        action="KYC_CREATED",
        target_type="KYCVerification",
        target_id=uuid.uuid4(),
    )

    assert log.id is not None
    assert log.actor == actor
    assert log.action == "KYC_CREATED"
    assert log.target_type == "KYCVerification"


@pytest.mark.django_db
def test_actor_can_be_null():
    log = baker.make(
        AuditLog,
        actor=None,
    )

    assert log.actor is None


@pytest.mark.django_db
def test_string_representation():
    actor = baker.make(User, username="alice")

    log = baker.make(
        AuditLog,
        actor=actor,
        action="DOCUMENT_UPLOADED",
        target_type="KYCVerification",
    )

    result = str(log)

    assert "DOCUMENT_UPLOADED" in result
    assert "KYCVerification" in result

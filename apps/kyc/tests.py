import pytest
from django.core.exceptions import ValidationError
from model_bakery import baker

from apps.kyc.state_machine import transition_kyc
from apps.kyc.models import KYCVerification


@pytest.mark.django_db
def test_valid_transition_updates_status_and_version():
    kyc = baker.make(
        KYCVerification,
        status=KYCVerification.Status.INITIATED,
        version=1,
    )

    transition_kyc(kyc, KYCVerification.Status.DOCUMENT_SUBMITTED)

    kyc.refresh_from_db()

    assert kyc.status == KYCVerification.Status.DOCUMENT_SUBMITTED
    assert kyc.version == 2


@pytest.mark.django_db
def test_invalid_transition_raises_error():
    kyc = baker.make(
        KYCVerification,
        status=KYCVerification.Status.INITIATED,
        version=1,
    )

    with pytest.raises(ValidationError):
        transition_kyc(kyc, KYCVerification.Status.VERIFIED)


@pytest.mark.django_db
def test_verified_can_transition_to_signed():
    kyc = baker.make(
        KYCVerification,
        status=KYCVerification.Status.VERIFIED,
        version=3,
    )

    transition_kyc(kyc, KYCVerification.Status.SIGNED)

    kyc.refresh_from_db()

    assert kyc.status == KYCVerification.Status.SIGNED
    assert kyc.version == 4


@pytest.mark.django_db
def test_rejected_has_no_valid_transitions():
    kyc = baker.make(
        KYCVerification,
        status=KYCVerification.Status.REJECTED,
        version=1,
    )

    with pytest.raises(ValidationError):
        transition_kyc(kyc, KYCVerification.Status.SIGNED)

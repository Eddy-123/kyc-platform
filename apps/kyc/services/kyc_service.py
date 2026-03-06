from django.utils import timezone
from apps.kyc.state_machine import transition_kyc
from apps.kyc.models import KYCVerification
from apps.audit.models import AuditLog
from apps.audit.constants import DOCUMENT_SUBMITTED, KYC_VERIFIED, KYCVerificationConst


def submit_document(kyc, actor):
    transition_kyc(kyc, KYCVerification.Status.DOCUMENT_SUBMITTED)
    AuditLog.objects.create(
        actor=actor,
        action=DOCUMENT_SUBMITTED,
        target_type=KYCVerificationConst,
        target_id=kyc.id,
        metadata={"status": kyc.status},
    )


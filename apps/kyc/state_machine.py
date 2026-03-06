from apps.kyc.models import KYCVerification
from django.core.exceptions import ValidationError

ALLOWED_TRANSITIONS = {
    KYCVerification.Status.INITIATED: [KYCVerification.Status.DOCUMENT_SUBMITTED],
    KYCVerification.Status.DOCUMENT_SUBMITTED: [
        KYCVerification.Status.FACE_VERIFICATION_PENDING
    ],
    KYCVerification.Status.FACE_VERIFICATION_PENDING: [
        KYCVerification.Status.VERIFIED,
        KYCVerification.Status.REJECTED,
    ],
    KYCVerification.Status.VERIFIED: [KYCVerification.Status.SIGNED],
    KYCVerification.Status.REJECTED: [],
    KYCVerification.Status.SIGNED: [],
}


def transition_kyc(kyc, new_status):
    current_status = kyc.status
    if new_status not in ALLOWED_TRANSITIONS.get(current_status, []):
        raise ValidationError(
            f"Invalid transition from {current_status} to {new_status}"
        )
    kyc.status = new_status
    kyc.version += 1
    kyc.save(update_fields=["status", "version", "updated_at"])

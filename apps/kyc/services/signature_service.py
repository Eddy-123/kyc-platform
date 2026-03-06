from apps.kyc.crypto import sign_payload
from apps.kyc.models import ElectronicSignature
from apps.audit.models import AuditLog


def generate_signature(kyc, actor):
    document = kyc.documents.first()

    payload = {
        "kyc_id": str(kyc.id),
        "partner_id": str(kyc.partner_id),
        "client_id": str(kyc.client_id),
        "verified_at": str(kyc.verified_at),
        "document_checksum": document.checksum_sha256,
    }

    signature = sign_payload(payload)
    ElectronicSignature.objects.create(
        kyc=kyc, signature_value=signature, public_key_fingerprint="rsa-key-v1"
    )

    AuditLog.objects.create(
        actor=actor,
        action="KYC_SIGNED",
        target_type="KYCVerification",
        target_id=kyc.id,
        metadata={"signature": signature[:20]},
    )

    return signature

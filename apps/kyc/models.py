import uuid
from django.db import models
from django.conf import settings
import hashlib


def document_upload_path(instance, filename):
    return f"kyc/{instance.kyc.id}/{filename}"


class KYCVerification(models.Model):
    class Status(models.TextChoices):
        INITIATED = "initiated", "Initiated"
        DOCUMENT_SUBMITTED = "document_submitted", "Document Submitted"
        FACE_VERIFICATION_PENDING = (
            "face_verification_pending",
            "Face Verification Pending",
        )
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"
        SIGNED = "signed", "Signed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    partner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="partner_kycs"
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="client_kycs"
    )
    status = models.CharField(
        max_length=40, choices=Status.choices, default=Status.INITIATED
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    version = models.IntegerField(default=1)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["partner"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"KYCVerification(id={self.id}, partner={self.partner}, client={self.client}, status={self.status})"


class IdentityDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kyc = models.ForeignKey(
        KYCVerification, on_delete=models.CASCADE, related_name="documents"
    )
    file = models.FileField(upload_to=document_upload_path)
    checksum_sha256 = models.CharField(max_length=64)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def compute_checksum(self):
        sha256 = hashlib.sha256()
        for chunk in self.file.chunks():
            sha256.update(chunk)
        return sha256.hexdigest()


class FaceVerification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kyc = models.OneToOneField(
        KYCVerification, on_delete=models.CASCADE, related_name="face_verification"
    )
    result = models.CharField(max_length=20)
    confidence_score = models.FloatField()
    processed_at = models.DateTimeField(auto_now_add=True)


class ElectronicSignature(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kyc = models.OneToOneField(
        KYCVerification, on_delete=models.CASCADE, related_name="signature"
    )
    signature_value = models.TextField()
    public_key_fingerprint = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

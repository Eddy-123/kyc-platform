from rest_framework import serializers
from apps.kyc.models import KYCVerification, IdentityDocument, FaceVerification


class KYCCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCVerification
        fields = ["client"]


class KYCDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCVerification
        fields = "__all__"


class DocumentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentityDocument
        fields = ["file"]

    def validate_file(self, file):
        if file.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("File size exceeds 5MB limit.")

        if not file.content_type in ["image/jpeg", "image/png", "application/pdf"]:
            raise serializers.ValidationError(
                "Unsupported file type. Only JPEG, PNG, and PDF are allowed."
            )

        return file

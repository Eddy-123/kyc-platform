from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from apps.kyc.models import KYCVerification, FaceVerification
from apps.kyc.serializers import (
    KYCCreateSerializer,
    KYCDetailSerializer,
    DocumentUploadSerializer,
)
from apps.kyc.permissions import IsPartner, IsKYCParticipant, IsClient
from apps.kyc.services.kyc_service import submit_document
from apps.kyc.state_machine import transition_kyc
from apps.audit.models import AuditLog
from apps.audit.constants import FACE_VERIFICATION_PROCESSED, KYCVerificationConst
import random


class KYCCreateView(generics.CreateAPIView):
    serializer_class = KYCCreateSerializer
    permission_classes = [IsAuthenticated, IsPartner]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        kyc = serializer.save(partner=request.user)

        AuditLog.objects.create(
            actor=request.user,
            action="KYC_INITIATED",
            target_type="KYCVerification",
            target_id=kyc.id,
        )

        return Response({"kyc_id": kyc.id}, status=status.HTTP_201_CREATED)


class KYCDetailView(generics.RetrieveAPIView):
    queryset = KYCVerification.objects.all()
    serializer_class = KYCDetailSerializer
    permission_classes = [IsAuthenticated, IsKYCParticipant]


class DocumentUploadView(generics.CreateAPIView):
    serializer_class = DocumentUploadSerializer
    permission_classes = [IsAuthenticated, IsClient]

    def perform_create(self, serializer):
        kyc = get_object_or_404(KYCVerification, pk=self.kwargs["pk"])

        if kyc.status != KYCVerification.Status.INITIATED:
            return Response(
                {"detail": "Invalid state for document upload"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        document = serializer.save(kyc=kyc)
        document.checksum_sha256 = document.compute_checksum()
        document.save(update_fields=["checksum_sha256"])
        submit_document(kyc, self.request.user)


class FaceVerificationView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsClient]

    def post(self, request, pk):
        kyc = get_object_or_404(KYCVerification, pk=pk)

        if kyc.status != KYCVerification.Status.DOCUMENT_SUBMITTED:
            return Response(
                {"detail": "Invalid state for face verification"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        transition_kyc(kyc, KYCVerification.Status.FACE_VERIFICATION_PENDING)

        confidence = random.uniform(0.6, 0.99)

        if confidence > 0.8:
            result = "match"
            transition_kyc(kyc, KYCVerification.Status.VERIFIED)
        else:
            result = "no_match"
            transition_kyc(kyc, KYCVerification.Status.REJECTED)

        FaceVerification.objects.create(
            kyc=kyc,
            result=result,
            confidence_score=confidence,
        )

        AuditLog.objects.create(
            actor=request.user,
            action=FACE_VERIFICATION_PROCESSED,
            target_type=KYCVerificationConst,
            target_id=kyc.id,
            metadata={"result": result, "confidence": confidence},
        )

        return Response(
            {"result": result, "confidence": confidence},
            status=status.HTTP_200_OK,
        )

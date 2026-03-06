from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Count, Avg, Q


from apps.kyc.models import KYCVerification, FaceVerification
from apps.kyc.services.signature_service import generate_signature
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
from apps.kyc.crypto import verify_signature


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


class KYCSignatureView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        kyc = get_object_or_404(KYCVerification, pk=pk)

        if kyc.status != KYCVerification.Status.VERIFIED:
            return Response(
                {"detail": "Invalid state for signing"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        signature = generate_signature(kyc, request.user)
        transition_kyc(kyc, KYCVerification.Status.SIGNED)

        return Response(
            {"kyc_id": kyc.id, "signature": signature}, status=status.HTTP_200_OK
        )


class SignatureVerifyView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payload = request.data.get("payload")
        signature = request.data.get("signature")
        valid = verify_signature(payload, signature)

        return Response({"valid": valid}, status=status.HTTP_200_OK)


class PartnerKYCDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsPartner]

    def get(self, request):
        partner = request.user

        base_qs = KYCVerification.objects.filter(partner=partner)

        stats = base_qs.aggregate(
            total=Count("id"),
            initiated=Count("id", filter=Q(status="initiated")),
            document_submitted=Count("id", filter=Q(status="document_submitted")),
            face_verification_pending=Count(
                "id", filter=Q(status="face_verification_pending")
            ),
            verified=Count("id", filter=Q(status="verified")),
            rejected=Count("id", filter=Q(status="rejected")),
            signed=Count("id", filter=Q(status="signed")),
        )

        face_stats = FaceVerification.objects.filter(kyc__partner=partner).aggregate(
            avg_confidence=Avg("confidence_score")
        )

        recent_kyc = (
            base_qs.select_related("partner")
            .prefetch_related("documents", "face_verification")
            .order_by("-created_at")[:10]
        )

        return Response(
            {
                "stats": stats,
                "avg_face_confidence": face_stats["avg_confidence"],
                "recent_kyc": KYCDetailSerializer(recent_kyc, many=True).data,
            }
        )

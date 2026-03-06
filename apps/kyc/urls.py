from django.urls import path
from apps.kyc.views import (
    KYCCreateView,
    KYCDetailView,
    DocumentUploadView,
    FaceVerificationView,
    KYCSignatureView,
    SignatureVerifyView,
)

urlpatterns = [
    path("", KYCCreateView.as_view()),
    path("<uuid:pk>/", KYCDetailView.as_view()),
    path("<uuid:pk>/documents/", DocumentUploadView.as_view()),
    path("<uuid:pk>/face-verification/", FaceVerificationView.as_view()),
    path("<uuid:pk>/signature/", KYCSignatureView.as_view()),
    path("signature/verify/", SignatureVerifyView.as_view()),
]

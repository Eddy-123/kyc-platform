from django.contrib import admin
from apps.kyc.models import KYCVerification, IdentityDocument, FaceVerification

admin.site.register(KYCVerification)
admin.site.register(IdentityDocument)
admin.site.register(FaceVerification)

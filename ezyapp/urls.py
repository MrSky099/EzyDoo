from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'jobs', views.JobViewSet)
router.register(r'applications', views.JobApplicationViewSet)
router.register(r'reviews', views.ReviewViewSet)
router.register(r'wallets', views.WalletViewSet, basename='wallet')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'notifications', views.NotificationViewSet, basename='notification')
router.register(r'documents', views.HelperDocumentViewSet, basename='document')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
] 
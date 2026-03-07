from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import MeView, UserListCreate, UserDetail, ResetPasswordView

urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("users/me/", MeView.as_view(), name="me"),
    path("users/", UserListCreate.as_view(), name="user-list-create"),
    path("users/<int:pk>/", UserDetail.as_view(), name="user-detail"),
    path("users/<int:pk>/reset-password/", ResetPasswordView.as_view(), name="user-reset-password"),
]

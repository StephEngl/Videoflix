from django.urls import path
from .views import RegistrationView, ActivateAccountView, LoginView, LogoutView, CookieTokenRefreshView, TestEmailView

urlpatterns = [
    path('register/', RegistrationView.as_view(), name='register'),
    path('activate/<str:uidb64>/<str:token>/', ActivateAccountView.as_view(), name='activate'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('test-email/', TestEmailView.as_view(), name='test_email'),
]
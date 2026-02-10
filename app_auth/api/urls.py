"""URL configuration for authentication API endpoints.

This module defines URL patterns for user authentication, account management,
and password reset functionality.
"""

from django.urls import path
from .views import (
    RegistrationView, 
    ActivateAccountView, 
    LoginView, 
    LogoutView, 
    CookieTokenRefreshView, 
    PasswordResetView, 
    PasswordConfirmView,
)

urlpatterns = [
    # User registration and activation
    path('register/', RegistrationView.as_view(), name='register'),
    path('activate/<str:uidb64>/<str:token>/', ActivateAccountView.as_view(), name='activate'),
    
    # Authentication
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    
    # Password reset
    path('password_reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password_confirm/<str:uidb64>/<str:token>/', PasswordConfirmView.as_view(), name='password_confirm'),
]
from django.urls import path
from .views import (register_user, login_user, logout_user, verify_otp, google_signup, google_login, change_password,
                    upload_picture, forgot_password, reset_password, resend_otp)


urlpatterns = [
    path('register-user', register_user),
    path('credentials-login', login_user),

    path('google-signup', google_signup),
    path('google-login', google_login),

    path('logout', logout_user),
    path('verify-otp', verify_otp),
    path('resend-otp', resend_otp),
    path('change-password', change_password),
    path('forgot-password', forgot_password),
    path('reset-password', reset_password),
    path('upload-picture', upload_picture),

]

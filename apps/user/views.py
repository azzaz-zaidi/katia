import requests
import json
import base64

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import check_password
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from random import randint
from .models import OtpTemp
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.base_user import BaseUserManager
from django.core.mail import send_mail
from django.conf import settings


def generate_unique_otp():
    while True:
        otp = randint(1000, 9999)
        if not OtpTemp.objects.filter(otp=otp).exists():
            return otp


def verification_otp(user, verify_type):
    otp = generate_unique_otp()
    user_name = user.full_name or 'there'

    otp_record = OtpTemp.objects.get_or_create(user=user)[0]
    otp_record.otp = otp
    otp_record.verify_type = verify_type
    otp_record.expiry_time = timezone.now() + timedelta(minutes=10)
    otp_record.save()

    subject = 'Your Verification OTP'
    message = f"Hello {user_name},\n\nYour OTP for verification is {otp}. It will expire in 10 minutes.\n\nThank you!"
    recipient_list = [user.email]

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipient_list,
        # fail_silently=False,
    )

    return True


@api_view(['POST'])
def register_user(request):
    try:
        full_name = request.data.get('full_name', None)
        email = request.data.get('email')
        password = request.data.get('password')

        if not email:
            return Response({'success': False, 'message': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        if not password:
            return Response({'success': False, 'message': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email):
            return Response({'success': False, 'message': 'User already exist with this email'},
                            status=status.HTTP_409_CONFLICT)

        user = User(
            full_name=full_name,
            email=email,
        )
        user.set_password(password)
        user.save()
        verify_type = 1
        verification_otp(user, verify_type)
        return Response({'success': True, 'message': 'OTP send to your mail'},
                        status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'success': False, 'message': f'bad request {e}'}, status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login_user(request):
    try:
        email = request.data.get('email')
        password = request.data.get('password')

        if not email:
            Response({'success': False, 'message': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        if not password:
            Response({'success': False, 'message': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)

        if not User.objects.filter(email=email).exists():
            return Response({'success': False, 'message': 'User does not exist with this email.'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=email, password=password)
        if user is not None:
            verify_type = 2
            verification_otp(user, verify_type)
            return Response({'success': True, 'message': 'Login otp send to your mail'}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'message': 'Invalid email or password'},
                            status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'success': False, 'message': f'bad request {e}'}, status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def logout_user(request):
    logout(request)
    return Response({'message': 'User logout successfully'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@login_required()
def change_password(request):
    try:
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        user = request.user

        if not check_password(current_password, user.password):
            return Response({'error': 'Current password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

        if current_password == new_password:
            return Response({'error': 'New password cannot be the same as the current password.'},
                            status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        update_session_auth_hash(request, user)

        return Response({'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'success': False, 'message': f'bad request {e}'}, status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def verify_otp(request):
    try:
        otp = request.GET.get('otp', None)
        get_otp = OtpTemp.objects.get(otp=otp)
        current_time = timezone.now()
        verify_type = get_otp.verify_type
        user = User.objects.filter(id=get_otp.user_id).first()
        if user:
            if get_otp.expiry_time > current_time:
                if verify_type == '1':
                    user.email_verified = True
                    user.save()
                    login(request, user)
                    get_otp.delete()
                    image_data_url = None
                    return Response({'success': True, 'message': 'Email verified successfully', 'user_id': user.id,
                                     'user_name': user.full_name, 'user_email': user.email, 'auth_type':user.auth_type,
                                     'profile_picture': image_data_url},
                                    status=status.HTTP_200_OK)
                elif verify_type == '2':
                    login(request, user)
                    get_otp.delete()
                    if user.profile_picture:
                        profile_picture_base64 = base64.b64encode(user.profile_picture).decode('utf-8')
                        image_data_url = f"data:image/jpeg;base64,{profile_picture_base64}"
                    else:
                        image_data_url = None
                    return Response({'success': True, 'message': 'Email verified successfully', 'user_id': user.id,
                                     'user_name': user.full_name, 'user_email': user.email, 'auth_type':user.auth_type,
                                     'profile_picture': image_data_url},
                                    status=status.HTTP_200_OK)

                elif verify_type == '3':
                    if user.profile_picture:
                        profile_picture_base64 = base64.b64encode(user.profile_picture).decode('utf-8')
                        image_data_url = f"data:image/jpeg;base64,{profile_picture_base64}"
                    else:
                        image_data_url = None
                    get_otp.delete()
                    return Response({'success': True, 'message': 'OTP verified for reset password', 'user_id': user.id,
                                     'user_name': user.full_name, 'user_email': user.email, 'auth_type':user.auth_type,
                                     'profile_picture': image_data_url},
                                    status=status.HTTP_200_OK)
            else:
                return Response({'success': False, 'message': 'otp invalid/expired'},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'success': False, 'message': 'otp invalid/expired'}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:

        return Response({'success': False, 'message': f'bad request {e}'}, status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def google_signup(request):
    try:
        payload = {'access_token': request.data.get("token")}
        auth_request = requests.get('https://www.googleapis.com/oauth2/v1/userinfo', params=payload)
        data = json.loads(auth_request.text)
        if auth_request.status_code == 200:
            user = User.objects.filter(email=data['email']).first()
            if user:
                return Response({'success': False, 'message': 'User already exists'},
                                status=status.HTTP_409_CONFLICT)
            else:
                user_data = {
                    'email': data.get('email').lower(),
                    'full_name': data.get('name'),
                    'auth_type': 2
                }
                user = User.objects.create_user(**user_data)
                user.set_password(BaseUserManager().make_random_password())
                user.save()
                user.email_verified = True
                user.save()

                if user.profile_picture:
                    profile_picture_base64 = base64.b64encode(user.profile_picture).decode('utf-8')
                    image_data_url = f"data:image/jpeg;base64,{profile_picture_base64}"
                else:
                    image_data_url = None

                login(request, user)
                return Response({'success': True, 'message': 'User registered successfully', 'user_id': user.id,
                      'user_name': user.full_name, 'user_email': user.email,
                      'profile_picture': image_data_url},
                     status=status.HTTP_201_CREATED)

        else:
            return Response({'success': False, 'message': 'Access Token is expired or invalid'
                             }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'success': False, 'message': f'bad request {e}'}, status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def google_login(request):
    try:
        payload = {'access_token': request.data.get("token")}
        auth_request = requests.get('https://www.googleapis.com/oauth2/v1/userinfo', params=payload)
        data = json.loads(auth_request.text)
        if auth_request.status_code == 200:
            user = User.objects.filter(email=data['email']).first()
            if user:
                if user.email_verified is False:
                    user.email_verified = True
                    user.save()
                if user.profile_picture:
                    profile_picture_base64 = base64.b64encode(user.profile_picture).decode('utf-8')
                    image_data_url = f"data:image/jpeg;base64,{profile_picture_base64}"
                else:
                    image_data_url = None

                login(request, user)

                return Response({'success': True, 'message': 'User logged in successfully', 'user_id': user.id,
                          'user_name': user.full_name, 'user_email': user.email,
                          'profile_picture': image_data_url},
                         status=status.HTTP_200_OK)
            else:
                return Response({'success': False, 'message': 'User not found'},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'success': False, 'message': 'Access Token is expired or invalid'
                                }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'success': False, 'message': f'bad request {e}'}, status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@login_required()
def upload_picture(request):
    try:
        profile_picture = request.FILES.get('profile_picture')
        user = request.user
        if not profile_picture:
            return Response({'success': False, 'message': 'User profile picture is required'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not user:
            return Response({'success': False, 'message': 'User not found'},
                            status=status.HTTP_404_NOT_FOUND)
        user.profile_picture = profile_picture.read()
        user.save()
        profile_picture_base64 = base64.b64encode(user.profile_picture).decode('utf-8')
        image_data_url = f"data:image/jpeg;base64,{profile_picture_base64}"

        return Response({'success': True, 'message': 'Profile picture uploaded successfully',
                         'profile_picture': image_data_url},
                        status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'success': False, 'message': f'Bad request: {e}'},
                        status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def forgot_password(request):
    try:
        email = request.data.get('email')

        if not email:
            return Response({'success': False, 'message': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'success': False, 'message': 'User does not exist with this email.'},
                            status=status.HTTP_404_NOT_FOUND)
        verify_type = 3
        verification_otp(user, verify_type)

        return Response({'success': True, 'message': 'OTP sent to your email to reset password.'},
                        status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'success': False, 'message': f'Bad request: {e}'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def reset_password(request):
    try:
        user_id = request.data.get('user_id')
        new_password = request.data.get('new_password')

        if not user_id or not new_password:
            return Response({'success': False, 'message': 'User ID and new password are required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({'success': False, 'message': 'User not found.'},
                            status=status.HTTP_404_NOT_FOUND)

        user.set_password(new_password)
        user.save()

        return Response({'success': True, 'message': 'Password reset successfully.'},
                        status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'success': False, 'message': f'Bad request: {e}'},
                        status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def resend_otp(request):
    try:
        email = request.GET.get('email')
        if not email:
            return Response({'success': False, 'message': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(email=email).first()
        get_otp = OtpTemp.objects.filter(user=user.id)[0]
        if not get_otp:
            return Response({'success': False, 'message': 'Otp does not exist'}, status=status.HTTP_409_CONFLICT)
        otp = generate_unique_otp()
        get_otp.otp = otp
        get_otp.expiry_time = timezone.now() + timedelta(minutes=10)
        get_otp.save()

        user_name = user.full_name or 'there'
        subject = 'Your Verification OTP'
        message = f"Hello {user_name},\n\nYour OTP for verification is {otp}. It will expire in 10 minutes.\n\nThank you!"
        recipient_list = [user.email]

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            # fail_silently=False,
        )
        return Response({'success': True, 'message': 'Otp resend successfully'}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'success': False, 'message': f'bad request {e}'}, status=status.HTTP_400_BAD_REQUEST)

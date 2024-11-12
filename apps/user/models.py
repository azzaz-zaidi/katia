import uuid
from .enums import USER_AUTH_CHOICES, OTP_CHOICES
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    # def create_superuser(self, email, password, **extra_fields):
    #     """Create and save a SuperUser with the given email and password."""
    #     extra_fields.setdefault('is_staff', True)
    #     extra_fields.setdefault('is_superuser', True)
    #     extra_fields.setdefault('email_verified', True)
    #
    #     if extra_fields.get('is_staff') is not True:
    #         raise ValueError('Superuser must have is_staff=True.')
    #     if extra_fields.get('is_superuser') is not True:
    #         raise ValueError('Superuser must have is_superuser=True.')
    #
    #     return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    id = models.UUIDField(unique=True, default=uuid.uuid4, primary_key=True, editable=False, db_index=True)
    full_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(unique=True)
    auth_type = models.IntegerField(choices=USER_AUTH_CHOICES, default=1)
    email_verified = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    profile_picture = models.BinaryField(null=True, blank=True)
    first_login = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    # Removing inherited fields
    username = None
    groups = None
    user_permissions = None

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()


class OtpTemp(models.Model):
    id = models.UUIDField(unique=True, default=uuid.uuid4, primary_key=True, editable=False, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.IntegerField(default=0, null=True, blank=True)
    expiry_time = models.DateTimeField(null=True, blank=True)
    verify_type = models.CharField(choices=OTP_CHOICES, max_length=50, null=True, blank=True)

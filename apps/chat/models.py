import uuid
from django.db import models
from ..user.models import User
from .enums import ROLES


class Conversation(models.Model):
    conv_id = models.UUIDField(unique=True, default=uuid.uuid4, primary_key=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation {self.conv_id} for {self.user.email}"


class Message(models.Model):
    id = models.UUIDField(unique=True, default=uuid.uuid4, primary_key=True, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.IntegerField(choices=ROLES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # def __str__(self):
    #     return f"Message {self.uuid} - {self.get_role_display()} at {self.created_at}"

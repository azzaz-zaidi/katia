from django.urls import path
from .views import create_conversation, create_message, display_convo, delete_conversation


urlpatterns = [
    path('create-conversation', create_conversation),
    path('delete-conversation', delete_conversation),
    path('display-convo', display_convo),

    path('create-message', create_message)
]

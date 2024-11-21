from django.urls import path
from .views import create_message, display_conversation, delete_conversation


urlpatterns = [
    # path('create-conversation', create_conversation),
    path('delete-conversation', delete_conversation),
    path('display-convo', display_conversation),
    path('create-message', create_message)
]

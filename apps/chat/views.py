import os
import json
import socket

from pathlib import Path
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view



CONV_DIR = os.path.join(Path(__file__).resolve().parent.parent.parent, "KatiaIRC/Conv_Histories")


IRC_SOCKET_HOST = "localhost"
IRC_SOCKET_PORT = 1234

# @api_view(['POST'])
# def create_conversation(request):
#     try:
#         user = request.user
#         if not user:
#             return Response({'success': False, 'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
#
#         if not Conversation.objects.filter(user_id=request.user.id).exists():
#             conv_obj = Conversation.objects.create(user=user)
#         else:
#             conv_obj = Conversation.objects.filter(user=user).first()
#
#         return Response({'success': True, 'message': 'Conversation created successfully', 'conv_id': conv_obj.conv_id},
#                         status=status.HTTP_201_CREATED)
#     except Exception as e:
#         return Response({'success': False, 'message': f'bad request {e}'}, status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def create_message(request):
    """Endpoint to send a message to the bot and get a response."""
    if request.method == "GET":
        user_id = request.GET.get("user_id",)
        user_message = request.GET.get("message", "")
        is_delete = request.GET.get("is_delete", False)

        if not user_id:
            return Response({"error": "User id is required."}, status=400)

        data = {
            "user_id": user_id,
            "message": user_message,
            "is_delete": is_delete
        }
        try:
            # Connect to the IRC bot's socket server
            with socket.create_connection((IRC_SOCKET_HOST, IRC_SOCKET_PORT)) as sock:
                sock.sendall(json.dumps(data).encode("utf-8"))
                response = sock.recv(1024).decode("utf-8")
                return Response({"success": True,"response": response}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"success": False, "error": f"Failed to query bot: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"success": False, "error": "Invalid request method."}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def display_conversation(request):
    try:
        user_id = request.GET.get('user_id')
        user_file_path = os.path.join(CONV_DIR, f"{user_id}.txt")

        if os.path.exists(user_file_path):
            with open(user_file_path, "r", encoding="utf-8") as user_file:
                conversation_data = json.load(user_file)
                return Response({'success': True, 'message': conversation_data}, status=status.HTTP_200_OK)
        else:
            return Response({'success': True, 'message': f"No conversation history found for user {user_id}."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'success': False, 'message': f'bad request {e}'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_conversation(request):
    try:
        user_id = request.GET.get('user_id')

        user_file_path = os.path.join(CONV_DIR, f"{user_id}.txt")
        if os.path.exists(user_file_path):
            os.remove(user_file_path)
            return Response({'success': True, "message": f"Conversation history for user {user_id} has been deleted."},
                            status=status.HTTP_200_OK)
        else:
            return Response({'success': True, "message": f"No conversation history found for user {user_id} to delete."},
                            status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'success': False, 'message': f'bad request {e}'}, status=status.HTTP_400_BAD_REQUEST)

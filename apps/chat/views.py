import os
import json

from pathlib import Path
from openai import OpenAI
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

CONV_DIR = os.path.join(Path(__file__).resolve().parent.parent.parent, "KatiaIRC/Conv_Histories")


def get_bot_response(user_message, chat_history):
    """
    it will send your previous chat to
    llm for current question's response
    """

    system_message = f"""
    You are very professional chat bot and you will have previous
    chat discussions of two persons based on that give next response.
    Your name is "Katia". Other person name can be anyone. Keep the answer
    short and around the question only, do not give extra lengthy details etc.
    """

    prompts = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": chat_history},
        {"role": "user", "content": user_message},
    ]

    try:
        client = OpenAI(base_url=settings.BASE_URL, api_key=settings.API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini", messages=prompts, temperature=0, stream=False
        )
        data = response.to_dict()
        bot_answer = data["choices"][0]["message"]["content"]
        return bot_answer
    except Exception as e:
        return Response({"success": False, "error": f"Bad request: {str(e)}"})


def save_conversation(user_id, user_message, bot_response):
    """
    Save a conversation to a file for a specific user.
    """
    try:
        os.makedirs(CONV_DIR, exist_ok=True)
        user_file_path = os.path.join(CONV_DIR, f"{user_id}.txt")

        # with open(user_file_path, "a", encoding="utf-8") as user_file:
        #     user_file.write(f"User: {user_message}\n")
        #     user_file.write(f"Bot: {bot_response}\n\n")

        conversation = []
        if os.path.exists(user_file_path):
            with open(user_file_path, "r", encoding="utf-8") as user_file:
                try:
                    conversation = json.load(user_file)
                except json.JSONDecodeError:
                    pass

        conversation.append({"user": user_message, "assistant": bot_response})

        with open(user_file_path, "w", encoding="utf-8") as user_file:
            json.dump(conversation, user_file, indent=4)

    except Exception as e:
        return Response({"success": False, "error": f"Bad request: {str(e)}"})


def load_conversation(user_id):
    """
    Load a conversation from a file for a specific user.
    """
    try:
        user_file_path = os.path.join(CONV_DIR, f"{user_id}.txt")
        conversation_data = ""
        if os.path.exists(user_file_path):
            with open(user_file_path, "r", encoding="utf-8") as user_file:
                conversation_data = user_file.read()
            return conversation_data
        else:
            return conversation_data
    except Exception as e:
        print(f"An error occurred while loading the conversation: {str(e)}")


@api_view(['POST'])
def create_message(request):
    """Endpoint to send a message to the bot, get a response
     and save conversation history in text file"""
    user_id = request.data.get("user_id")
    user_message = request.data.get("message", "")
    if not user_id:
        return Response({"error": "User id is required."}, status=400)

    # data = {
    #     "user_id": user_id,
    #     "message": user_message,
    #     "is_delete": is_delete
    # }
    try:
        # Connect to the IRC bot's socket server
        # with socket.create_connection((IRC_SOCKET_HOST, IRC_SOCKET_PORT)) as sock:
        #     sock.sendall(json.dumps(data).encode("utf-8"))
        #     response = sock.recv(1024).decode("utf-8")

        chat_history = load_conversation(user_id)
        response = get_bot_response(user_message, chat_history)
        save_conversation(user_id, user_message, response)

        return Response({"success": True, "response": response}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"success": False, "error": f"Failed to query bot: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def display_conversation(request):
    """Endpoint to display conversation."""
    try:
        user_id = request.GET.get('user_id')
        user_file_path = os.path.join(CONV_DIR, f"{user_id}.txt")

        if os.path.exists(user_file_path):
            with open(user_file_path, "r", encoding="utf-8") as user_file:
                conversation_data = json.load(user_file)
                return Response({'success': True, 'message': conversation_data}, status=status.HTTP_200_OK)
        else:
            return Response({'success': True, 'message': f"No conversation found."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'success': False, 'message': f'bad request {e}'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_conversation(request):
    """Endpoint to delete conversation using user_id"""
    try:
        user_id = request.GET.get('user_id')

        user_file_path = os.path.join(CONV_DIR, f"{user_id}.txt")
        if os.path.exists(user_file_path):
            os.remove(user_file_path)
            return Response({'success': True, "message": f"Conversation history deleted."}, status=status.HTTP_200_OK)
        else:
            return Response({'success': True, "message": f"No conversation history found."},
                            status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'success': False, 'message': f'bad request {e}'}, status=status.HTTP_400_BAD_REQUEST)

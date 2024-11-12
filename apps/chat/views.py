from openai import OpenAI
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from ..user.models import User
from .models import Conversation, Message


@api_view(['POST'])
def create_conversation(request):
    try:
        user = request.user
        if not user:
            return Response({'success': False, 'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        if not Conversation.objects.filter(user_id=request.user.id).exists():
            conv_obj = Conversation.objects.create(user=user)
        else:
            conv_obj = Conversation.objects.filter(user=user).first()

        return Response({'success': True, 'message': 'Conversation created successfully', 'conv_id': conv_obj.conv_id},
                        status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'success': False, 'message': f'bad request {e}'}, status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def create_message(request):
    try:
        conv_id = request.data.get('conv_id')
        prompt = request.data.get('prompt')

        if not conv_id:
            return Response({'success': False, 'message': 'Conversation id is required'},
                            status=status.HTTP_400_BAD_REQUEST)

        conv_obj = Conversation.objects.filter(conv_id=conv_id).first()

        prompts = [
            {
                "content": "You are a helpful assistant.",
                "role": "system"
            }
        ]

        messages = conv_obj.messages.filter(role__in=[2, 3]).order_by('created_at')

        prompts.extend(
            {
                "content": message.content,
                "role": "user" if message.role == 2 else "assistant",
            }
            for message in messages
        )
        prompts.append(
            {
                "content": f'{prompt}',
                "role": "user"
            }
        )
        client = OpenAI(base_url=settings.BASE_URL,
                        api_key=settings.API_KEY)
        # Call ChatGPT API
        result = client.chat.completions.create(model="gpt-4o-mini", messages=prompts, temperature=0, stream=False)
        try:
            api_response = result.to_dict()
            content = api_response["choices"][0]["message"]["content"]

            Message.objects.create(
                conversation=conv_obj,
                role=2,
                content=prompt
            )

            Message.objects.create(
                conversation=conv_obj,
                role=3,
                content=content
            )
            return Response({'success': True, 'message': content}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'success': False, 'message': f'bad request {e}'}, status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({'success': False, 'message': f'bad request {e}'}, status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def display_convo(request):
    try:
        conv_obj = Conversation.objects.filter(user_id=request.user.id).first()
        if not conv_obj:
            return Response({'success': False, 'message': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

        messages = conv_obj.messages.filter(role__in=[2, 3]).order_by('created_at')

        messages_data = [
            {
                "role": "User" if message.role == 2 else "Assistant",
                "content": message.content,
                "created_at": message.created_at
            }
            for message in messages
        ]
        return Response({'success': True, 'message': messages_data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'success': False, 'message': f'bad request {e}'}, status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_conversation(request):
    try:
        conv_id = request.GET.get('conv_id')

        if not conv_id:
            return Response({"error": "Conversation ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        conversation = Conversation.objects.filter(conv_id=conv_id).first()

        if not conversation:
            return Response({"error": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)

        conversation.delete()

        return Response({"message": "Conversation and its messages were deleted successfully"},
                        status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'success': False, 'message': f'bad request {e}'}, status.HTTP_400_BAD_REQUEST)

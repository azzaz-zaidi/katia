import socket
from threading import Thread

import openai
from irc.bot import SingleServerIRCBot
from openai import OpenAI
import json
import os
from pathlib import Path


# BASE_PATH = "./KatiaIRC/Conv_Histories"
openai.api_key = "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"
IRC_BOT_NICKNAME = "Katia"
API_KEY = "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"
OPENAI_URL = "https://api.openai.com/v1/"
CONV_DIR = os.path.join(Path(__file__).resolve().parent, "KatiaIRC/Conv_Histories")

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
        print(f"An error occurred while saving the conversation: {str(e)}")
        raise



def load_conversation(user_id):
    """
    Load a conversation from a file for a specific user.

    Args:
        user_id (str): The unique identifier for the user.

    Returns:
        str: The conversation history as a string, or a message indicating no file found.
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



class IRCBot(SingleServerIRCBot):
    def __init__(self, server, port, nickname, channel, nickserv_password):
        super().__init__([(server, port)], nickname, nickname)
        self.channel = channel
        self.nickserv_password = nickserv_password

    def get_bot_response(self, user_message, chat_history):
        """
        it will send your previous chat to
        llm for current question's response
        """

        system_message = f"""
        You are very professional chat bot and you will have previous
        chat discussions of two persons based on that give next response.
        Your name is "{IRC_BOT_NICKNAME}". Other person name can be anyone. Keep the answer
        short and around the question only, do not give extra lengthy details etc.
        \n\n
        For example chat messages history will look like this.
        This is the format for chat messages of yours and a imaginary person (Petter).
        Petter: Hi, I need some information. Can you help me?
        {IRC_BOT_NICKNAME}: hello. Yes sure ask me about your information.
        Petter: what is the software engineering?
        """

        prompts = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": chat_history},
            {"role": "user", "content": user_message},
        ]

        try:
            client = OpenAI(base_url=OPENAI_URL, api_key=API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini", messages=prompts, temperature=0, stream=False
            )
            data = response.to_dict()
            bot_answer = data["choices"][0]["message"]["content"]
            return bot_answer
        except Exception as e:
            print("I'm sorry, I couldn't process your request due to an error.")

    def start_socket_listener(self):
        def listen():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.bind(("localhost", 1234))
                server_socket.listen(5)
                print("Socket listener started on port 1234...")
                while True:
                    conn, addr = server_socket.accept()
                    with conn:
                        data = conn.recv(1024).decode("utf-8")
                        if data:
                            parsed_data = json.loads(data)

                            user_id = parsed_data.get("user_id")
                            user_message = parsed_data.get("message")

                            chat_history = load_conversation(user_id)
                            response = self.get_bot_response(user_message, chat_history)
                            save_conversation(user_id, user_message, response)

                            conn.sendall(response.encode("utf-8"))

        thread = Thread(target=listen, daemon=True)
        thread.start()

    def start(self):
        """Override start method to include socket listener."""
        self.start_socket_listener()
        super().start(


# Configuration
SERVER = "irc.rizon.net"
PORT = 6667
NICKNAME = "Katia"
CHANNEL = "#Katia"
NICKSERV_PASSWORD = "g00df00d"

if __name__ == "__main__":
    bot = IRCBot(SERVER, PORT, NICKNAME, CHANNEL, NICKSERV_PASSWORD)
    bot.start()

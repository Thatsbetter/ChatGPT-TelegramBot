import json

import openai
from openai import OpenAI
import requests
import telebot
from telebot import apihelper

from person import Person


class ChatBot:
    def __init__(self, file_path='credentials.json'):
        self.publish_channel = None
        self.bot = None
        self.openApi_client = None
        self.file_path = file_path
        self.initialize_bot()
        self.chats = {}
        self.max_message_length = 4096
        self.current_model = "gpt-3.5-turbo"  # Default model

    def initialize_bot(self):
        credentials = self.load_credentials()
        openai.organization = credentials.get('openai_organisation')
        openai.api_key = credentials.get('openai_api_key')
        self.bot = telebot.TeleBot(credentials.get('telegram_api_key'))
        apihelper.SESSION_TIME_TO_LIVE = 5 * 60
        self.publish_channel = credentials.get('publish_channel')
        self.openApi_client = OpenAI(
            # defaults to os.environ.get("OPENAI_API_KEY")
            api_key=credentials.get('openai_api_key')
        )

    def load_credentials(self):
        with open(self.file_path, 'r') as file:
            return json.load(file)

    def check_credentials(self):
        if None in (openai.api_key, self.bot.token, self.publish_channel, openai.organization, self.publish_channel):
            raise Exception("Credentials not found")

    def generate_response(self, prompt):
        response = self.openApi_client.chat.completions.create(
            model=self.current_model,
            messages=prompt,
            n=1,
            temperature=0.5
        )
        return response.choices[0].message.content

    def generate_voice(self, text):
        response = self.openApi_client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        return response

    def get_voice(self, voice_file_id, chat_id):
        file_info = self.bot.get_file_url(voice_file_id)
        response = requests.get(file_info)
        voice_path = f'voice_message_{chat_id}.ogg'
        with open(voice_path, 'wb') as f:
            f.write(response.content)
        return voice_path

    def transcribe(self, voice_path):
        audio_file = open(voice_path, "rb")
        result = self.openApi_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        return result.text

    def set_model(self, new_model):
        # Validate that the new_model is allowed (add more models as needed)
        allowed_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-1106-preview"]  # Add more models as needed
        if new_model not in allowed_models:
            raise ValueError(f"Invalid model: {new_model}")

        self.current_model = new_model
        return f"Switched to model: {new_model}"

    def run_bot(self):
        @self.bot.message_handler(content_types=['voice'])
        def speak(message):
            try:
                person = self.chats.setdefault(message.chat.id, Person(message.chat.id))
                voice_path = self.get_voice(message.voice.file_id, person.chat_id)
                message_text = self.transcribe(voice_path)

                if person.is_sum_needed():
                    chat_summary = self.generate_response(
                        [{"role": "user", "content": f"make a summary of this:\n {person.make_list_to_text()}"}])
                    person.update_chat(chat_summary)

                person.messages.append({"role": "user", "content": message_text})
                response = self.generate_response(person.messages)
                person.messages.append({"role": "assistant", "content": response})
                voice = self.generate_voice(response)
                self.bot.send_audio(person.chat_id, voice)
                if len(person.messages) > self.max_message_length:
                    message_chunks = [response[i:i + self.max_message_length] for i in
                                      range(0, len(response), self.max_message_length)]
                    for chunk in message_chunks:
                        self.bot.send_message(self.publish_channel,
                                              f"{message.chat.first_name} \n {str(chunk)}")
                else:
                    self.bot.send_message(self.publish_channel, f"{message.chat.first_name} \n {str(person.messages)}")
            except Exception as e:
                self.bot.send_message(self.publish_channel, str(e))

        @self.bot.message_handler(func=lambda m: m.chat.type == "private" and m.content_type == 'text')
        def private(message):
            try:
                person = self.chats.setdefault(message.chat.id, Person(message.chat.id))

                if message.text == "/delete":
                    person.delete_chat()
                    return
                elif message.text == "/start":
                    self.bot.send_message(self.publish_channel, f"{message.chat.first_name} \n {str(person.messages)}")
                    return
                elif message.text.startswith("/use_model"):
                    new_model = message.text.split(" ")[1]
                    response = self.set_model(new_model)
                    self.bot.send_message(person.chat_id, response)
                    return
                elif message.text.startswith("#speak"):
                    tts = message.text.split("#speak")[1]
                    voice = self.generate_voice(tts)
                    self.bot.send_voice(person.chat_id, voice)
                    return
                elif message.text.startswith("#audio"):
                    tts = message.text.split("#audio")[1]
                    voice = self.generate_voice(tts)
                    self.bot.send_audio(person.chat_id, voice)
                    return

                if person.is_sum_needed():
                    chat_summary = self.generate_response(
                        [{"role": "user", "content": f"make a summary of this:\n {person.make_list_to_text()}"}])
                    person.update_chat(chat_summary)
                    self.bot.send_message(person.chat_id, "Das hier ist aber kein Spielzeug.\n LG \n Taha")

                person.messages.append({"role": "user", "content": message.text})
                response = self.generate_response(person.messages)
                person.messages.append({"role": "assistant", "content": response})
                if len(response) > self.max_message_length:
                    message_chunks = [response[i:i + self.max_message_length] for i in
                                      range(0, len(response), self.max_message_length)]
                    for chunk in message_chunks:
                        self.bot.send_message(person.chat_id, chunk)
                else:
                    self.bot.send_message(person.chat_id, response)
                    self.bot.send_message(self.publish_channel, f"{message.chat.first_name} \n {str(person.messages)}")

            except Exception as e:
                self.bot.send_message(self.publish_channel, str(e))

        self.bot.infinity_polling(interval=0)

import openai
import telebot
from telebot import apihelper
import json
from person import Person

class ChatBot:
    def __init__(self, file_path='credentials.json'):
        self.file_path = file_path
        self.initialize_bot()
        self.chats = {}

    def initialize_bot(self):
        credentials = self.load_credentials()
        openai.organization = credentials.get("openai_organisation")
        openai.api_key = credentials.get('openai_api_key')
        self.bot = telebot.TeleBot(credentials.get('telegram_api_key'))
        self.publish_channel = credentials.get("publish_channel")

        apihelper.SESSION_TIME_TO_LIVE = 5 * 60

    def load_credentials(self):
        with open(self.file_path, 'r') as file:
            return json.load(file)

    def check_credentials(self):
        if None in (openai.api_key, self.bot.token):
            raise Exception("Credentials not found")

    def generate_response(self, prompt):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=prompt,
            n=1,
            temperature=0.5
        )
        return response.choices[0].message.content


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

    def run_bot(self):
        @self.bot.message_handler(func=lambda m: m.chat.type == "private" and m.content_type == 'text')
        def private(message):
            try:
                if message.chat.id not in chats:
                    chats[message.chat.id] = Person(message.chat.id)
                    bot.send_message(message.from_user.id,
                                     "Welcome to Taha's Assistant bot.\n \nUse /delete to start new conversation or else it will use conversations History to answer. \n\nPlease note that this bot is for educational purposes only!\n\n Enjoy!")

                person = chats.get(message.chat.id)
                if message.text == "/delete":
                    person.delete_chat()
                    return
                if message.text == "/start":
                    return
                if person.is_sum_needed():
                    chat_summary = generate_response(
                        [{"role": "user", "content": f"make a summary of this:\n {person.make_list_to_text()}"}])
                    person.update_chat(chat_summary)
                    bot.send_message(message.from_user.id, "Das hier ist aber kein Spielzeug.\n LG \n Taha")

                person.messages.append({"role": "user", "content": message.text})
                response = generate_response(person.messages)
                bot.send_message(message.from_user.id, response)
                person.messages.append({"role": "assistant", "content": response})
                bot.send_message(self.publish_channel, f"{message.chat.first_name} \n {str(person.messages)}")
            except Exception as e:
                bot.send_message(self.publish_channel, str(e))

        self.bot.infinity_polling(interval=0)


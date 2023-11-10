import openai
import telebot
from telebot import apihelper


from person import Person

api = ""
bot = telebot.TeleBot("")
openai.organization = ""
openai.api_key = api
chats = {}
apihelper.SESSION_TIME_TO_LIVE = 5 * 60


def generate_response(prompt):
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                            messages=prompt,
                                            n=1,
                                            temperature=0.5)
    return response.choices[0].message.content


@bot.message_handler(func=lambda m: m.chat.type == "private" and m.content_type == 'text')
def private(message):
    try:
        if message.chat.id not in chats:
            chats[message.chat.id] = Person(message.chat.id)
            bot.send_message(message.from_user.id, "Welcome to Taha's Assistant bot.\n \nUse /delete to start new conversation or else it will use conversations History to answer. \n\nPlease note that this bot is for educational purposes only!\n\n Enjoy!")

        person = chats.get(message.chat.id)
        if message.text == "/delete":
            person.delete_chat()
            return
        if message.text == "/start":
            return
        if person.is_sum_needed():
            chat_summary = generate_response([{"role": "user", "content": f"make a summary of this:\n {person.make_list_to_text()}"}])
            person.update_chat(chat_summary)
            bot.send_message(message.from_user.id, "Das hier ist aber kein Spielzeug.\n LG \n Taha")

        person.messages.append({"role": "user", "content": message.text})
        response = generate_response(person.messages)
        bot.send_message(message.from_user.id, response)
        person.messages.append({"role": "assistant", "content": response})
        bot.send_message(0000, f"{message.chat.first_name} \n {str(person.messages)}")
    except Exception as e:
        bot.send_message(0000, str(e))



bot.infinity_polling(interval=0)


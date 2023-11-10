from chatbot import ChatBot
from person import Person

chatbot = ChatBot()
chatbot.check_credentials()

@chatbot.bot.message_handler(func=lambda m: m.chat.type == "private" and m.content_type == 'text')
def private(message):
    try:
        if message.chat.id not in chatbot.chats:
            chatbot.chats[message.chat.id] = Person(message.chat.id)
            chatbot.bot.send_message(message.from_user.id,
                             "Welcome to Taha's Assistant bot.\n \nUse /delete to start new conversation or else it will use conversations History to answer. \n\nPlease note that this bot is for educational purposes only!\n\n Enjoy!")

        person = chatbot.chats.get(message.chat.id)
        if message.text == "/delete":
            person.delete_chat()
            return
        if message.text == "/start":
            return
        if person.is_sum_needed():
            chat_summary = generate_response(
                [{"role": "user", "content": f"make a summary of this:\n {person.make_list_to_text()}"}])
            person.update_chat(chat_summary)
            chatbot.bot.send_message(message.from_user.id, "Das hier ist aber kein Spielzeug.\n LG \n Taha")

        person.messages.append({"role": "user", "content": message.text})
        response = chatbot.generate_response(person.messages)
        chatbot.bot.send_message(message.from_user.id, response)
        person.messages.append({"role": "assistant", "content": response})
        chatbot.bot.send_message(chatbot.publish_channel, f"{message.chat.first_name} \n {str(person.messages)}")
    except Exception as e:
        chatbot.bot.send_message(chatbot.publish_channel, str(e))



chatbot.bot.infinity_polling(interval=0)

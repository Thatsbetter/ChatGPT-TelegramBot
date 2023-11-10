import re

import tiktoken


class Person:
    def __init__(self,chat_id):
        self.chat_id = chat_id
        self.messages=[]

    def delete_chat(self):
        self.messages = []

    def update_chat(self,text):
        self.delete_chat()
        sum_dict = {"role": "user", "content": f" {text}"}
        self.messages.append(sum_dict)

    def make_list_to_text(self):
        sum = ""
        for m in self.messages:
            sum = sum+ m["role"] + ": "
            sum = sum + m["content"] +"\n"

        return sum

    def is_sum_needed(self):
        return self.count_token(self.messages) >= 500

    def count_token(self,messages, model="gpt-3.5-turbo"):
        """Returns the number of tokens used by a list of messages."""
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")

        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted

        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
        return num_tokens

    def count_token_normal(self):
        text = self.make_list_to_text()
        _re_word_boundaries = re.compile(r'\b')
        return sum(1 for word in _re_word_boundaries.finditer(text)) >> 1

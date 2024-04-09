import os
from tgbot.config import load_config
from openai import OpenAI
from datetime import datetime, date
import json
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class DatesAnswer:
    start_date: date
    end_date: date
    chat_id: int


@dataclass
class Message:
    datetime: datetime
    text: str
    user: str


def get_chat(chats_list, search) -> DatesAnswer:
    now = datetime.now().strftime("%Y-%m-%d")
    prompt = ("Пользователю надо выбрать чат, по примерному названию из списка, а также указать период дат сообщений в формате json, например:\n"
              '''{
                  "start_date": "2021-09-01",
                  "end_date": "2021-09-30",
                  "chat_id": 1
              }\n'''
              f"Дата сегодня: {now}\n"
              "Список чатов:\n")
    for chat in chats_list:
        prompt += f"ID: {chat['id']} - Название:{chat['name']}\n"
    prompt += f"Вот запрос пользователя: {search}"
    client = OpenAI(api_key=load_config().openai.token)
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "user", "content": prompt},
        ],
        model=load_config().openai.gpt_model
    )
    str_json = chat_completion.choices[0].message.content
    chat_data = json.loads(str_json)
    start_date = datetime.strptime(chat_data["start_date"], "%Y-%m-%d").date()
    end_date = datetime.strptime(chat_data["end_date"], "%Y-%m-%d").date()
    chat_id = chat_data["chat_id"]
    return DatesAnswer(
        start_date=start_date,
        end_date=end_date,
        chat_id=chat_id
        )


def explain_chat(messages: List[Message],
                 context: List[Dict[str, str]] = [],
                 request: str = "") -> str:
    prompt = "Пользователю надо объяснить и ответить на вопросы, по теме сообщений в чате, вот их список:\n"
    for message in messages:
        prompt += f"Дата: {message.datetime.strftime('%Y-%m-%d - %H:%M:%S')}, Текст: {message.text}, Пользователь: {message.user}\n"
    prompt += f"Запрос пользователя: {request}"
    client = OpenAI(api_key=load_config().openai.token)
    gpt_messages = context + [{"role": "user", "content": prompt}]
    chat_completion = client.chat.completions.create(
        messages=gpt_messages,
        model=load_config().openai.gpt_model
    )
    return chat_completion.choices[0].message.content


if __name__ == "__main__":
    get_chat([{"id": 1, "name": "Родители"},
                {"id": 3, "name": "Дети"}], "Детишки за последнюю неделю")
    explain_chat(
        messages=[
            Message(datetime=datetime(2021, 9, 1, 10, 0, 0), text="Hello", user="User1"),
            Message(datetime=datetime(2021, 9, 1, 11, 0, 0), text="How are you?", user="User2"),
            Message(datetime=datetime(2021, 9, 1, 12, 0, 0), text="I'm good, thanks!", user="User1"),
        ],
        request="А следующее сообщение?",
        context=[
            {"role": "user", "content": "Какое было первое сообщение?"},
            {"role": "assistant", "content": 'Это было: "How are you?" от пользователя "User2" в 10:00:00 2021-09-01'},
        ]
    )

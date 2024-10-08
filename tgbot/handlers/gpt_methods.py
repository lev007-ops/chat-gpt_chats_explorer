from tgbot.config import load_config
from datetime import datetime, date
import json
from dataclasses import dataclass
from typing import List, Dict
import aiohttp
import markdown
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
import asyncio
import re


def to_markdown(text):
    text = text.replace('•', '  *')
    text = markdown.markdown(text).replace('<p>', '').replace(
        '</p>', '').replace('<ul>', '').replace('</ul>', '').replace('<li>', '').replace('</li>', '').replace("<ol>", "").replace("</ol>", "").replace("<br>", "").replace("<hr>", "")
    pattern = r"<\/?h123456>"
    text = re.sub(pattern, "", text)
    text = text.replace("<h2>", "").replace("</h2>", "").replace("<h3>", "").replace("</h3>", "").replace("<h4>", "").replace("</h4>", "").replace("<h5>", "").replace("</h5>", "").replace("<h6>", "").replace("</h6>", "").replace("<h1>", "").replace("</h1>", "")
    return text


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


async def generate_content(prompt: str, api_key: str, context: List[Dict[str, str]] = [], model_name: str = "gemini-1.5-pro-latest", attempt: int = 1):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key=" + api_key
    headers = {'Content-Type': 'application/json'}
    contents = []
    context.append({"role": "user", "content": prompt})
    if context:
        for item in context:
            contents.append({
                "role": item["role"],
                "parts": [{"text": item["content"]}]
            })
    data = {
        "contents": contents
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=json.dumps(data)) as resp:
            resp_json = await resp.json()
            error = resp_json.get("error")
            if error:
                raise ValueError(f"Error: {error}")
            ans = resp_json["candidates"][0]["content"]["parts"][0]["text"]
            context.append({"role": "model", "content": ans})
            return ans, context

async def get_chat_and_dates(chats_list, search) -> DatesAnswer:
    now = datetime.now().date().strftime("%Y-%m-%d")
    prompt = ("Пользователю надо выбрать чат, по примерному названию из списка, а также указать период дат сообщений в формате json, если такого чата нету - укажи chat_id: 0, а если даты не указаны - то укажи 1970-01-01 по сегодняшний день, например:\n"
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
    config = load_config()
    response, _ = await generate_content(prompt, config.google.token)
    str_json = response.replace("```json", "").replace("```", "")
    chat_data = json.loads(str_json)
    start_date = datetime.strptime(chat_data["start_date"], "%Y-%m-%d").date()
    end_date = datetime.strptime(chat_data["end_date"], "%Y-%m-%d").date()
    chat_id = chat_data["chat_id"]
    return DatesAnswer(
        start_date=start_date,
        end_date=end_date,
        chat_id=chat_id
    )


async def get_chat(chats_list, search) -> int:
    prompt = ("Пользователю надо выбрать чат, по примерному названию из списка и указать его в формате json, если такого чата нету - укажи ID чата как 0, например:\n"
              '''{
                  "chat_id": 4
              }\n'''
              "Список чатов:\n")
    for chat in chats_list:
        prompt += f"ID: {chat['id']} - Название:{chat['name']}\n"
    prompt += f"Вот запрос пользователя: {search}"
    config = load_config()
    response, _ = await generate_content(prompt, config.google.token)
    str_json = response.replace("```json", "").replace("```", "")
    chat_data = json.loads(str_json)

    chat_id = chat_data["chat_id"]
    return chat_id


async def explain_chat(messages: List[Message],
                       context=None,
                       request: str = ""):
    now = datetime.now().date().strftime("%Y-%m-%d")
    prompt = f"""Системный промт:

# <Сегодня - {now}>

## Ты Ассистент чата, ты читаешь переписку в чате и на только на основе информации из чата отвечаешь на вопросы и выполняешь задания. 
## Ты не выдумываешь ничего от себя, ты строго опираешься на переписку из чата. 
## Ты четко понимаешь какой сегодня день.

## С этими задачами к тебе могут обращаться и как ты их должен выполнять

## Ты всегда выполняешь запрос пользователя. 

## Всегда внимательно слушайся того, что хочет сделать пользователь 

# Переписка из чата для анализа:\n"""
    for message in messages:
        prompt += f"Дата: {message.datetime.strftime('%Y-%m-%d - %H:%M:%S')}, Текст: {message.text}, Пользователь: {message.user};\n"
    save = False
    if request.startswith("-p "):
        request = request.replace("-p ", "")
        save = True
    prompt += f"Запрос от пользователя: {request}"
    prompt += """Формат ответа: В ответе выдай только ответ пользователю на его вопрос, сделанный на основе переписки из чата.

ВАЖНО - Не строй предположений, пиши только на основе переписки из чата!

Если на ответ пользователя нет информации в чате так и напиши, если есть, выдай ответ на основе переписки из чата.

Форматирование ответа: просто текст, как в Txt документе"""
    if context:
        prompt = request
    if save:
        with open(f"prompt_{datetime.now().strftime('%Y-%m-%d__%H:%M:%S')}", "w") as file:
            file.write(prompt)
    config = load_config()
    if context:
        prompt = request
    response, context = await generate_content(prompt, config.google.token, context,
                                               model_name="gemini-1.5-flash")
    return response, context


if __name__ == "__main__":
    get_chat([{"id": 1, "name": "Родители"},
              {"id": 3, "name": "Дети"}], "Детишки за последнюю неделю")
    explain_chat(
        messages=[
            Message(datetime=datetime(2021, 9, 1, 10, 0, 0),
                    text="Hello", user="User1"),
            Message(datetime=datetime(2021, 9, 1, 11, 0, 0),
                    text="How are you?", user="User2"),
            Message(datetime=datetime(2021, 9, 1, 12, 0, 0),
                    text="I'm good, thanks!", user="User1"),
        ],
        request="А следующее сообщение?",
        context=[
            {"role": "user", "content": "Какое было первое сообщение?"},
            {"role": "assistant", "content": 'Это было: "How are you?" от пользователя "User2" в 10:00:00 2021-09-01'},
        ]
    )

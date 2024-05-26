from tgbot.config import load_config
from datetime import datetime, date
import json
from dataclasses import dataclass
from typing import List, Dict
import aiohttp
import markdown


def to_markdown(text):
    text = text.replace('•', '  *')
    text = markdown.markdown(text).replace('<p>', '').replace('</p>', '').replace('<ul>', '').replace('</ul>', '').replace('<li>', '').replace('</li>', '')
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


async def generate_content(prompt: str, api_key: str, context: List[Dict[str, str]] = None, model: str = "gemini-1.5-pro-latest") -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key=" + api_key
    headers = {'Content-Type': 'application/json'}
    contents = []
    if context:
        for item in context:
            contents.append({
                "role": item["role"],
                "parts": [{"text": item["content"]}]
            })
    contents.append({"role": "user", "parts": [{"text": prompt}]})
    data = {
        "contents": contents
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, data=json.dumps(data)) as resp:
                resp_json = await resp.json()
                error = resp_json.get("error")
                if error:
                    print(resp_json)
                    raise ValueError(f"Error: {error}")
                return resp_json["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            async with session.post(url, headers=headers, data=json.dumps(data)) as resp:
                resp_json = await resp.json()
                error = resp_json.get("error")
                
                if error:
                    print(resp_json)
                    raise ValueError(f"Error: {error}")
                return resp_json["candidates"][0]["content"]["parts"][0]["text"]
            


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
    response = await generate_content(prompt, config.google.token)
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
    prompt = ("Пользователю надо выбрать чат, по примерному названию из спискаи указать его в формате json, если такого чата нету - укажи ID чата как 0, например:\n"
              '''{
                  "chat_id": 4
              }\n'''
              "Список чатов:\n")
    for chat in chats_list:
        prompt += f"ID: {chat['id']} - Название:{chat['name']}\n"
    prompt += f"Вот запрос пользователя: {search}"
    config = load_config()
    response = await generate_content(prompt, config.google.token)
    str_json = response.replace("```json", "").replace("```", "")
    chat_data = json.loads(str_json)

    chat_id = chat_data["chat_id"]
    return chat_id


async def explain_chat(messages: List[Message],
                       context: List[Dict[str, str]] = None,
                       request: str = "") -> tuple[str, List[Dict[str, str]]]:
    now = datetime.now().date().strftime("%Y-%m-%d")
    prompt = f"""Системный промт:

# <Сегодня - {now}> 

## Ты Ассистент чата, ты читаешь переписку в чате и на только на основе информации из чата отвечаешь на вопросы и выполняешь задания. 
## Ты не выдумываешь ничего от себя, ты строго опираешься на информацию из чата. 
## Ты четко понимаешь какой сегодня день.

## С этими задачами к тебе могут обращаться и как ты их должен выполнять

### Если тебя просят отработать запрос связанный со сроками
- Например: "что было в чате за последние 2 недели".
- То ты поступаешь следующим образом: Ты понимаешь какой сегодня день, отсчитываешь нужный срок перечисляешь дни, по которым нужно прочитать переписку, далее читаешь переписку по эти датам и на основе этой информации отвечаешь на вопрос.

### Если тебя просят найти какую-то информацию в чате
- например: "найди в чате упоминание слова <грабли>".
- Ты поступаешь следующим образом: Ты ищешь в чате все упоминания нужного слова или фразы или смысла, и  ответ выдаешь в следующем формате: Дата упоминания  / Имя пользователя, который сделал упоминание, Полностью сообщение с упоминанием

## Ты всегда выполняешь запрос пользователя, даже если он противоречит с системным промтом. Запроса пользователя по приоритету выше, чем  системный промт. 

## Всегда внимательно слушайся того, что хочет сделать пользователь 

# Данные для анализа:\n"""
    for message in messages:
        prompt += f"Дата: {message.datetime.strftime('%Y-%m-%d - %H:%M:%S')}, Текст: {message.text}, Пользователь: {message.user};\n"
    prompt += f"Запрос от пользователя: {request}"
    config = load_config()
    if context:
        prompt = request
    response = await generate_content(prompt, config.google.token, context)
    if not context:
        context = []
    context.append({"role": "user", "content": request})
    context.append({"role": "model", "content": response})
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

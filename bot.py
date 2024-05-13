import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio.client import Redis

from tgbot.config import load_config
from tgbot.handlers.registration import registration_router
from tgbot.handlers.explore import explore_router
from tgbot.handlers.start import start_router
from tgbot.middlewares.config import ConfigMiddleware
from tgbot.services import broadcaster
from pyrogram.client import Client
from pyrogram import compose
from tgbot.models.models import User
from tgbot.handlers.pyrogram_handlers import get_message_handler

logger = logging.getLogger(__name__)


async def on_startup(bot: Bot, admin_ids: list[int]):
    await broadcaster.broadcast(bot, admin_ids, "The bot has been launched!")


def get_pyrogram_clients():
    users = User.select()
    clients = []
    handler = get_message_handler()
    for user in users:
        user: User
        if user.session_string:
            client = Client(
                    name=f"user_{user.telegram_id}",
                    session_string=user.session_string,
                    in_memory=True,
                    device_model="ChatsExplorer"
                )
            client.add_handler(handler)
            clients.append(client)
    return clients


def register_global_middlewares(dp: Dispatcher, config):
    dp.message.outer_middleware(ConfigMiddleware(config))
    dp.callback_query.outer_middleware(ConfigMiddleware(config))


async def start_bot():
    logging.basicConfig(
        level=logging.INFO,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s '
        '[%(asctime)s] - %(name)s - %(message)s',
    )
    logger.info("Starting bot")
    config = load_config(".env")

    if config.tg_bot.use_redis:
        redis = Redis(host=config.redis.host)
        storage = RedisStorage(redis=redis)
    else:
        storage = MemoryStorage()
    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    dp = Dispatcher(storage=storage)

    for router in [
        start_router,
        registration_router,
        explore_router,
    ]:
        dp.include_router(router)

    register_global_middlewares(dp, config)

    await on_startup(bot, config.tg_bot.admin_ids)
    await dp.start_polling(bot)


async def run_pyrogram_client(client: Client):
    await client.start()
    me = await client.get_me()
    print(f"Client {me.id} has been started")


async def main():
    loop = asyncio.get_event_loop()
    clients = get_pyrogram_clients()
    aiogram_task = loop.create_task(start_bot())
    pyrogram_tasks = [loop.create_task(run_pyrogram_client(client)) for client in clients]
    await asyncio.gather(*pyrogram_tasks)
    await aiogram_task


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt):
        logger.error("The bot has been stopped!")

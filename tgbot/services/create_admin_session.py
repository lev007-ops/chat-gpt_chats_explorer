from pyrogram.client import Client
from tgbot.config import load_config
import asyncio


async def main():
    config = load_config()
    async with Client("admin_session", api_id=config.pyrogram.api_id,
                      api_hash=config.pyrogram.api_hash) as client:
        me = await client.get_me()
        print(me)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    print("Admin session created successfully!")

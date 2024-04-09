from tgbot.services.create_admin_session import main as create_admin_session
import asyncio


async def main():
    print("1) Creating admin session")
    select = int(input("Select: "))
    if select == 1:
        await create_admin_session()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
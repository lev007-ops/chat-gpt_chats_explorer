from dataclasses import dataclass

from environs import Env


@dataclass
class DbConfig:
    host: str
    password: str
    user: str
    database: str
    port: int


@dataclass
class TgBot:
    token: str
    admin_ids: list[int]
    use_redis: bool


@dataclass
class OpenAI:
    token: str
    gpt_model: str


@dataclass
class PyrogramConfig:
    api_id: int
    api_hash: str


@dataclass
class Redis:
    host: str
    port: int


@dataclass
class Miscellaneous:
    other_params = None


@dataclass
class Config:
    tg_bot: TgBot
    db: DbConfig
    misc: Miscellaneous
    redis: Redis
    pyrogram: PyrogramConfig
    openai: OpenAI


def load_config(path: str = None):
    env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBot(
            token=env.str("BOT_TOKEN"),
            admin_ids=list(map(int, env.list("ADMINS"))),
            use_redis=env.bool("USE_REDIS")
        ),
        db=DbConfig(
            host=env.str('DB_HOST'),
            password=env.str('DB_PASS'),
            user=env.str('DB_USER'),
            database=env.str('DB_NAME'),
            port=env.int('DB_ONLINE_PORT')
        ),
        redis=Redis(
            host=env.str("REDIS_HOST"),
            port=env.int("REDIS_PORT")
        ),
        misc=Miscellaneous(),
        pyrogram=PyrogramConfig(
            api_id=env.int("API_ID"),
            api_hash=env.str("API_HASH")
        ),
        openai=OpenAI(
            token=env.str("CHAT_GPT_KEY"),
            gpt_model=env.str("GPT_MODEL")
        )
    )

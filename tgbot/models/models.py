import peewee as pw
from tgbot.config import load_config

config = load_config()

db = pw.PostgresqlDatabase(config.db.database,
                           user=config.db.user,
                           password=config.db.password,
                           host=config.db.host,
                           autorollback=True
                           )

# Peewee models


class BaseModel(pw.Model):
    """A base model that will use our Postgresql database"""
    class Meta:
        database = db


class ActivationCode(BaseModel):
    code = pw.CharField(max_length=200, unique=True)
    created_at = pw.DateTimeField(constraints=[pw.SQL('DEFAULT now()')])
    is_used = pw.BooleanField(default=False)


class User(BaseModel):
    telegram_id = pw.BigIntegerField(unique=True)
    phone = pw.CharField(max_length=20, unique=True)
    session_string = pw.CharField(max_length=500, null=True)


class Chat(BaseModel):
    chat_id = pw.BigIntegerField()
    user = pw.ForeignKeyField(User)
    title = pw.CharField(max_length=500)


class TelegramMessage(BaseModel):
    chat = pw.ForeignKeyField(Chat)
    user_parse = pw.ForeignKeyField(User)
    from_user_id = pw.BigIntegerField(null=True)
    username = pw.CharField(max_length=200)
    datetime = pw.DateTimeField("%Y-%m-%d")
    text = pw.TextField(null=True)
    message_id = pw.IntegerField()

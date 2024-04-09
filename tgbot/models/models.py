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
    telegram_id = pw.IntegerField(unique=True)
    phone = pw.CharField(max_length=20, unique=True)
    session_string = pw.CharField(max_length=500, null=True)

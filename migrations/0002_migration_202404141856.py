# auto-generated snapshot
from peewee import *
import datetime
import peewee


snapshot = Snapshot()


@snapshot.append
class ActivationCode(peewee.Model):
    code = CharField(max_length=200, unique=True)
    created_at = DateTimeField(constraints=[SQL('DEFAULT now()')])
    is_used = BooleanField(default=False)
    class Meta:
        table_name = "activationcode"


@snapshot.append
class User(peewee.Model):
    telegram_id = IntegerField(unique=True)
    phone = CharField(max_length=20, unique=True)
    session_string = CharField(max_length=500, null=True)
    class Meta:
        table_name = "user"


@snapshot.append
class TelegramMessage(peewee.Model):
    chat_id = IntegerField()
    user_parse = snapshot.ForeignKeyField(index=True, model='user')
    from_user_id = IntegerField(null=True)
    username = CharField(max_length=200)
    datetime = DateTimeField(formats='%Y-%m-%d')
    class Meta:
        table_name = "telegrammessage"



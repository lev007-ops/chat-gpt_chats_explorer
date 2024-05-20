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
    telegram_id = BigIntegerField(unique=True)
    phone = CharField(max_length=20, unique=True)
    session_string = CharField(max_length=500, null=True)
    class Meta:
        table_name = "user"


@snapshot.append
class Chat(peewee.Model):
    chat_id = BigIntegerField()
    user = snapshot.ForeignKeyField(index=True, model='user')
    title = CharField(max_length=500)
    class Meta:
        table_name = "chat"


@snapshot.append
class TelegramMessage(peewee.Model):
    chat = snapshot.ForeignKeyField(index=True, model='chat')
    user_parse = snapshot.ForeignKeyField(index=True, model='user')
    from_user_id = BigIntegerField(null=True)
    username = CharField(max_length=200)
    datetime = DateTimeField(formats='%Y-%m-%d')
    text = TextField(null=True)
    message_id = IntegerField()
    class Meta:
        table_name = "telegrammessage"


def forward(old_orm, new_orm):
    chat = new_orm['chat']
    return [
        # Apply default value '' to the field chat.title,
        chat.update({chat.title: ''}).where(chat.title.is_null(True)),
    ]

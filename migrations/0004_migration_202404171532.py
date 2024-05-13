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
class Chat(peewee.Model):
    chat_id = IntegerField()
    user = snapshot.ForeignKeyField(index=True, model='user')
    class Meta:
        table_name = "chat"


@snapshot.append
class TelegramMessage(peewee.Model):
    chat = snapshot.ForeignKeyField(index=True, model='chat')
    user_parse = snapshot.ForeignKeyField(index=True, model='user')
    from_user_id = IntegerField(null=True)
    username = CharField(max_length=200)
    datetime = DateTimeField(formats='%Y-%m-%d')
    text = TextField(null=True)
    message_id = IntegerField()
    class Meta:
        table_name = "telegrammessage"


def forward(old_orm, new_orm):
    telegrammessage = new_orm['telegrammessage']
    return [
        # Apply default value 0 to the field telegrammessage.message_id,
        telegrammessage.update({telegrammessage.message_id: 0}).where(telegrammessage.message_id.is_null(True)),
    ]

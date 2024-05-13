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
    old_user = old_orm['user']
    user = new_orm['user']
    old_chat = old_orm['chat']
    chat = new_orm['chat']
    old_telegrammessage = old_orm['telegrammessage']
    telegrammessage = new_orm['telegrammessage']
    return [
        # Convert datatype of the field user.telegram_id: INT -> BIGINT,
        user.update({user.telegram_id: old_user.telegram_id.cast('INTEGER')}).where(old_user.telegram_id.is_null(False)),
        # Convert datatype of the field chat.chat_id: INT -> BIGINT,
        chat.update({chat.chat_id: old_chat.chat_id.cast('INTEGER')}).where(old_chat.chat_id.is_null(False)),
        # Convert datatype of the field telegrammessage.from_user_id: INT -> BIGINT,
        telegrammessage.update({telegrammessage.from_user_id: old_telegrammessage.from_user_id.cast('INTEGER')}).where(old_telegrammessage.from_user_id.is_null(False)),
    ]


def backward(old_orm, new_orm):
    old_user = old_orm['user']
    user = new_orm['user']
    old_chat = old_orm['chat']
    chat = new_orm['chat']
    old_telegrammessage = old_orm['telegrammessage']
    telegrammessage = new_orm['telegrammessage']
    return [
        # Convert datatype of the field user.telegram_id: BIGINT -> INT,
        user.update({user.telegram_id: old_user.telegram_id.cast('INTEGER')}).where(old_user.telegram_id.is_null(False)),
        # Convert datatype of the field chat.chat_id: BIGINT -> INT,
        chat.update({chat.chat_id: old_chat.chat_id.cast('INTEGER')}).where(old_chat.chat_id.is_null(False)),
        # Convert datatype of the field telegrammessage.from_user_id: BIGINT -> INT,
        telegrammessage.update({telegrammessage.from_user_id: old_telegrammessage.from_user_id.cast('INTEGER')}).where(old_telegrammessage.from_user_id.is_null(False)),
    ]

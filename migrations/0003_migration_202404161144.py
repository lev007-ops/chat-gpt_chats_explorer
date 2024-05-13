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
    class Meta:
        table_name = "telegrammessage"


def forward(old_orm, new_orm):
    telegrammessage = new_orm['telegrammessage']
    return [
        # Check the field `telegrammessage.chat` does not contain null values,
    ]


def migrate_forward(op, old_orm, new_orm):
    op.create_table(new_orm.chat)
    op.add_column(new_orm.telegrammessage.chat)
    op.add_column(new_orm.telegrammessage.text)
    op.drop_column(old_orm.telegrammessage.chat_id)
    op.run_data_migration()
    op.add_not_null(new_orm.telegrammessage.chat)
    op.add_foreign_key_constraint(new_orm.telegrammessage.chat)


def backward(old_orm, new_orm):
    telegrammessage = new_orm['telegrammessage']
    return [
        # Apply default value 0 to the field telegrammessage.chat_id,
        telegrammessage.update({telegrammessage.chat_id: 0}).where(telegrammessage.chat_id.is_null(True)),
    ]


def migrate_backward(op, old_orm, new_orm):
    op.drop_foreign_key_constraint(old_orm.telegrammessage.chat)
    op.add_column(new_orm.telegrammessage.chat_id)
    op.run_data_migration()
    op.drop_column(old_orm.telegrammessage.chat)
    op.drop_column(old_orm.telegrammessage.text)
    op.add_not_null(new_orm.telegrammessage.chat_id)
    op.drop_table(old_orm.chat)

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

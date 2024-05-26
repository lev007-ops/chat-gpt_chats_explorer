from tgbot.models.models import db, User, Chat, TelegramMessage, ActivationCode


def main():
    db.create_tables([User, Chat, TelegramMessage, ActivationCode])


if __name__ == '__main__':
    main()

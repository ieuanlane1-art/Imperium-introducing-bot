import logging

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN
from database import setup_database
from handlers import (
    start_command,
    help_command,
    chatid_command,
    stats_command,
    welcome_new_member,
    button_handler,
)


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is missing. Add it in Railway Variables.")

    setup_database()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("chatid", chatid_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(
        MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            welcome_new_member
        )
    )

    app.add_handler(CallbackQueryHandler(button_handler))

    print("Imperium Welcome Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()

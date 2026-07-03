import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

GROUP_NAME = "Imperium"

WELCOME_DELETE_TIME = 600

REMINDER_TIME = 300

DASHBOARD_MESSAGE_ID = int(os.getenv("DASHBOARD_MESSAGE_ID", "0"))

IB_NOTIFY_CHAT_ID = -1003997830047
IB_NOTIFY_TOPIC_ID = 11638
PROMO_TARGET_CHAT_ID = -1004420905654

IBS = [
    {"name": "Ieuan", "username": "IeuanFX_ITA"},
    {"name": "Luke", "username": "lturrell"},
    {"name": "Mitch", "username": "Uuvs0ap"},
    {"name": "Tommy FX", "username": "tommyyyyfx"},
    {"name": "Bevs", "username": "ImperiumTradingGroupLTD"},
    {"name": "Alex", "username": "Fxwithalexf1"},
    {"name": "Shaun", "username": "Shaunb1996"},
    {"name": "Harley", "username": "harleyd10"},
    {"name": "Tommy Voice", "username": "tommyvoice"},
    {"name": "Lewis", "username": "Lew6FX"},
    {"name": "Iestyn", "username": "iestynjohns"},
    {"name": "Jack", "username": "JACK_ITAA"},
    {"name": "Cody", "username": "cst071"},
    {"name": "Brandan", "username": "Brandan32"}
]

PREFILLED_MESSAGE = (
    "Hi! I've just joined Imperium and I'd like to get started with copy trading."
)

ADMIN_USER_IDS = [
    8690177711,  # you
]
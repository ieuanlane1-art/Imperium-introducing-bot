from urllib.parse import quote

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import PREFILLED_MESSAGE


def start_journey_keyboard(lead_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🚀 Start Your Journey",
                callback_data=f"start:{lead_id}"
            )
        ]
    ])


def open_ib_chat_keyboard(ib_username):
    message = quote(PREFILLED_MESSAGE)
    url = f"https://t.me/{ib_username}?text={message}"

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💬 Open Chat",
                url=url
            )
        ]
    ])
    
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def admin_panel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📣 Post Get Started", callback_data="admin_promo")],
        [InlineKeyboardButton("📊 Dashboard", callback_data="admin_dashboard")],
        [InlineKeyboardButton("👥 List IBs", callback_data="listibs")],
        [InlineKeyboardButton("Add IB", callback_data="admin_addib")],
        [InlineKeyboardButton("Remove IB", callback_data="admin_removeib")],
    ])
    
def promo_start_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🚀 Get Started",
                callback_data="promo_start"
            )
        ]
    ])
    
def remove_ib_keyboard(ibs):
    buttons = []

    for ib in ibs:
        buttons.append([
            InlineKeyboardButton(
                f"❌ {ib['name']} — @{ib['username']}",
                callback_data=f"remove_ib:{ib['username']}"
            )
        ])

    buttons.append([
        InlineKeyboardButton("⬅️ Back to Panel", callback_data="admin_back")
    ])

    return InlineKeyboardMarkup(buttons)

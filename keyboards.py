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
        [InlineKeyboardButton("📈 Stats", callback_data="admin_stats")]
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

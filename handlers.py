import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import (
    GROUP_NAME,
    WELCOME_DELETE_TIME,
    REMINDER_TIME,
    IB_NOTIFY_CHAT_ID,
    IB_NOTIFY_TOPIC_ID,
)
from database import (
    create_lead,
    get_lead,
    mark_clicked,
    mark_reminder_sent,
    get_total_leads,
    get_leads_by_ib,
    get_clicked_leads,
    get_dashboard_stats,
    set_setting,
    get_setting,
)
from keyboards import start_journey_keyboard, open_ib_chat_keyboard
from lead_manager import assign_next_ib

logger = logging.getLogger(__name__)


async def delete_message(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.data["chat_id"]
    message_id = job.data["message_id"]

    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        logger.info(f"Could not delete message: {e}")


async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    lead_id = job.data["lead_id"]
    chat_id = job.data["chat_id"]

    lead = get_lead(lead_id)

    if not lead:
        return

    clicked = lead[7]
    reminder_sent = lead[8]

    if clicked == 1 or reminder_sent == 1:
        return

    username = lead[2]
    first_name = lead[3]
    mention = f"@{username}" if username else first_name

    message = await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"👋 {mention}\n\n"
            "Looks like you haven't started your setup yet.\n\n"
            "Tap below whenever you're ready to get connected with your account manager."
        ),
        reply_markup=start_journey_keyboard(lead_id),
    )

    mark_reminder_sent(lead_id)

    context.job_queue.run_once(
        delete_message,
        WELCOME_DELETE_TIME,
        data={"chat_id": chat_id, "message_id": message.message_id},
    )


async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.new_chat_members:
        return

    for member in update.message.new_chat_members:
        if member.is_bot:
            continue

        ib = assign_next_ib()

        lead_id = create_lead(
            telegram_id=member.id,
            username=member.username,
            first_name=member.first_name,
            assigned_ib=ib["name"],
            assigned_ib_username=ib["username"],
        )

        mention = f"@{member.username}" if member.username else member.first_name

        message = await update.message.reply_text(
            text=(
                f"👋 Welcome {mention} to {GROUP_NAME}!\n\n"
                "You're one click away from getting connected with your dedicated account manager.\n\n"
                "Tap below to begin."
            ),
            reply_markup=start_journey_keyboard(lead_id),
        )

        context.job_queue.run_once(
            delete_message,
            WELCOME_DELETE_TIME,
            data={"chat_id": update.effective_chat.id, "message_id": message.message_id},
        )

        context.job_queue.run_once(
            send_reminder,
            REMINDER_TIME,
            data={"lead_id": lead_id, "chat_id": update.effective_chat.id},
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if not data.startswith("start:"):
        return

    lead_id = int(data.split(":")[1])
    lead = get_lead(lead_id)

    if not lead:
        await query.edit_message_text("Sorry, I couldn't find your setup details.")
        return

    assigned_ib = lead[4]
    assigned_ib_username = lead[5]

    mark_clicked(lead_id)

    await query.edit_message_text(
        text=(
            "✅ You're all set!\n\n"
            "Your dedicated account manager is:\n\n"
            f"@{assigned_ib_username}\n\n"
            "Tap below to begin your setup."
        ),
        reply_markup=open_ib_chat_keyboard(assigned_ib_username),
    )

    try:
        client_name = lead[3] or lead[2] or "New client"
        client_username = lead[2]

        if client_username:
            client_link = f"https://t.me/{client_username}"
            username_text = f"@{client_username}"
        else:
            client_link = f"tg://user?id={lead[1]}"
            username_text = "No username"

        await context.bot.send_message(
            chat_id=IB_NOTIFY_CHAT_ID,
            message_thread_id=IB_NOTIFY_TOPIC_ID,
            text=(
                "🚨 NEW IMPERIUM LEAD\n\n"
                f"👤 Client: {client_name}\n"
                f"📱 Username: {username_text}\n\n"
                f"👔 Assigned IB: @{assigned_ib_username}\n\n"
                "Tap below to message your client."
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "💬 Message Client",
                            url=client_link,
                        )
                    ]
                ]
            ),
        )
    except Exception as e:
        logger.info(f"Could not notify IB: {e}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👑 Imperium Welcome Bot is online.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Commands:\n/start\n/help")
    
async def chatid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    topic_id = update.message.message_thread_id

    await update.message.reply_text(
        f"Chat ID:\n{chat_id}\n\nTopic ID:\n{topic_id}"
    )
    
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = get_dashboard_stats()

    total = stats["total"]
    clicked = stats["clicked"]

    conversion = 0
    if total > 0:
        conversion = round((clicked / total) * 100, 1)

    message = (
        "📊 IMPERIUM DASHBOARD\n\n"
        f"📅 Today's Leads: {stats['today']}\n"
        f"📆 This Week: {stats['week']}\n"
        f"🗓️ This Month: {stats['month']}\n\n"
        f"🚀 Started Setup: {clicked}/{total}\n"
        f"📈 Conversion Rate: {conversion}%"
    )

    await update.message.reply_text(message)
    
def build_dashboard_text():
    stats = get_dashboard_stats()

    total = stats["total"]
    clicked = stats["clicked"]

    conversion = 0
    if total > 0:
        conversion = round((clicked / total) * 100, 1)

    return (
        "📊 LIVE IMPERIUM DASHBOARD\n\n"
        f"📅 Today's Leads: {stats['today']}\n"
        f"📆 This Week: {stats['week']}\n"
        f"🗓️ This Month: {stats['month']}\n\n"
        f"🚀 Started Setup: {clicked}/{total}\n"
        f"📈 Conversion Rate: {conversion}%"
    )


async def dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = await update.message.reply_text(build_dashboard_text())

    set_setting("dashboard_chat_id", update.effective_chat.id)
    set_setting("dashboard_message_id", message.message_id)

    if update.message.message_thread_id:
        set_setting("dashboard_topic_id", update.message.message_thread_id)

    try:
        await context.bot.pin_chat_message(
            chat_id=update.effective_chat.id,
            message_id=message.message_id,
            disable_notification=True,
        )
    except Exception as e:
        logger.info(f"Could not pin dashboard: {e}")
        
async def update_live_dashboard(context):
    chat_id = get_setting("dashboard_chat_id")
    message_id = get_setting("dashboard_message_id")

    if not chat_id or not message_id:
        return

    try:
        await context.bot.edit_message_text(
            chat_id=int(chat_id),
            message_id=int(message_id),
            text=build_dashboard_text()
        )
    except Exception as e:
        logger.info(f"Dashboard update failed: {e}")
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import (
    GROUP_NAME,
    WELCOME_DELETE_TIME,
    REMINDER_TIME,
    IB_NOTIFY_CHAT_ID,
    IB_NOTIFY_TOPIC_ID,
    PROMO_TARGET_CHAT_ID,
    FREE_GROUP_CHAT_ID,
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
    get_latest_lead_by_telegram_id,
    set_setting,
    get_setting,
    get_active_ibs,
    add_ib,
    remove_ib,
    set_admin_state,
    get_admin_state,
)
from keyboards import (
    start_journey_keyboard,
    open_ib_chat_keyboard,
    admin_panel_keyboard,
    promo_start_keyboard,
    remove_ib_keyboard
)
from lead_manager import assign_next_ib

logger = logging.getLogger(__name__)

# Imperium branding - emoji-safe Unicode
TRIDENT = "\U0001F531"   # 🔱
CHECK = "\u2705"         # ✅
SIREN = "\U0001F6A8"     # 🚨
PERSON = "\U0001F464"    # 👤
PHONE = "\U0001F4F1"     # 📱
TIE = "\U0001F454"       # 👔
CHAT = "\U0001F4AC"      # 💬
ROCKET = "\U0001F680"    # 🚀
CHART = "\U0001F4CA"     # 📊
WAVE = "\U0001F44B"      # 👋


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
            f"{WAVE} {mention}\n\n"
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
    if update.effective_chat.id != FREE_GROUP_CHAT_ID:
        return
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
                f"{TRIDENT} Welcome {mention} to {GROUP_NAME}!\n\n"
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

    data = query.data
    await query.answer()

    if data == "admin_promo":
        await context.bot.send_message(
            chat_id=PROMO_TARGET_CHAT_ID,
            text=(
                f"{TRIDENT} Ready to start your journey with Imperium?\n\n"
                "If you haven't started yet, tap below and we'll assign you "
                "a dedicated account manager instantly."
            ),
            reply_markup=promo_start_keyboard(),
        )

        await query.answer(f"Promo posted successfully {CHECK}")
        return
    if data == "listibs":
        ibs = get_active_ibs()
    
        if not ibs:
            await query.edit_message_text(
                "No active IBs found.",
                reply_markup=admin_panel_keyboard(),
            )
            return

        message = f"{TRIDENT} Active IB Rotation\n\n"
    
        for index, ib in enumerate(ibs, start=1):
            message += f"{index}. {ib['name']} - @{ib['username']}\n"
    
        await query.edit_message_text(
            message,
            reply_markup=admin_panel_keyboard(),
        )
        return
    
    if data == "admin_addib":
        set_admin_state(query.from_user.id, "awaiting_ib_name", "")
    
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(
                f"{TRIDENT} Add New IB\n\n"
                "Send me the IB's display name.\n\n"
                "Example:\n"
                "Alex"
            ),
        )
        return
             

    if data == "admin_removeib":
        ibs = get_active_ibs()

        if not ibs:
            await query.edit_message_text(
                "No active IBs found.",
                reply_markup=admin_panel_keyboard(),
            )
            return

        await query.edit_message_text(
            f"{TRIDENT} Select an IB to remove:",
            reply_markup=remove_ib_keyboard(ibs),
        )
        return

    if data.startswith("remove_ib:"):
        username = data.split(":", 1)[1]

        remove_ib(username)

        await query.edit_message_text(
            f"{CHECK} Removed IB:\n\n@{username}",
            reply_markup=admin_panel_keyboard(),
        )
        return

    if data == "admin_back":
        await query.edit_message_text(
            f"{TRIDENT} Imperium Admin Panel\n\nChoose an option below:",
            reply_markup=admin_panel_keyboard(),
        )
        return
        message = f"{TRIDENT} Active IB Rotation\n\n"

        for index, ib in enumerate(ibs, start=1):
            message += f"{index}. {ib['name']} - @{ib['username']}\n"

        await query.edit_message_text(message)
        return
        
    if data == "admin_dashboard":
        await query.edit_message_text(
            build_dashboard_text(),
            reply_markup=admin_panel_keyboard(),
        )
        return
    if data == "promo_start":
        user = query.from_user

        existing_lead = get_latest_lead_by_telegram_id(user.id)

        if existing_lead:
            assigned_ib_username = existing_lead[5]

            await query.edit_message_text(
                text=(
                    f"{CHECK} You're already assigned!\n\n"
                    "Your dedicated account manager is:\n\n"
                    f"@{assigned_ib_username}\n\n"
                    "Tap below to continue your setup."
                ),
                reply_markup=open_ib_chat_keyboard(assigned_ib_username),
            )
            return

        ib = assign_next_ib()

        lead_id = create_lead(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            assigned_ib=ib["name"],
            assigned_ib_username=ib["username"],
        )

        mark_clicked(lead_id)
        await update_live_dashboard(context)

        client_name = user.first_name or user.username or "New client"
        client_username = user.username

        if client_username:
            client_link = f"https://t.me/{client_username}"
            username_text = f"@{client_username}"
            mention = f"@{client_username}"
        else:
            client_link = f"tg://user?id={user.id}"
            username_text = "No username"
            mention = client_name

        await context.bot.send_message(
            chat_id=IB_NOTIFY_CHAT_ID,
            message_thread_id=IB_NOTIFY_TOPIC_ID,
            text=(
                f"{SIREN} NEW IMPERIUM LEAD\n\n"
                f"{PERSON} Client: {client_name}\n"
                f"{PHONE} Username: {username_text}\n\n"
                f"{TIE} Assigned IB: @{ib['username']}\n\n"
                "Tap below to message your client."
            ),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(f"{CHAT} Message Client", url=client_link)]]
            ),
        )

        target_chat_id = query.message.chat_id if query.message else PROMO_TARGET_CHAT_ID

        response_message = await context.bot.send_message(
            chat_id=target_chat_id,
            text=(
                f"{CHECK} {mention}, you're all set!\n\n"
                "Your dedicated account manager is:\n\n"
                f"@{ib['username']}\n\n"
                "Tap below to begin your setup."
            ),
            reply_markup=open_ib_chat_keyboard(ib["username"]),
        )

        context.job_queue.run_once(
            delete_message,
            WELCOME_DELETE_TIME,
            data={"chat_id": target_chat_id, "message_id": response_message.message_id},
        )

        await query.answer(f"Assigned to @{ib['username']} {CHECK}")
        return

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
    await update_live_dashboard(context)

    await query.edit_message_text(
        text=(
            f"{CHECK} You're all set!\n\n"
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
                f"{SIREN} NEW IMPERIUM LEAD\n\n"
                f"{PERSON} Client: {client_name}\n"
                f"{PHONE} Username: {username_text}\n\n"
                f"{TIE} Assigned IB: @{assigned_ib_username}\n\n"
                "Tap below to message your client."
            ),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(f"{CHAT} Message Client", url=client_link)]]
            ),
        )
    except Exception as e:
        logger.info(f"Could not notify IB: {e}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"{TRIDENT} Imperium Welcome Bot is online.")


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
        f"{CHART} IMPERIUM DASHBOARD\n\n"
        f"Today's Leads: {stats['today']}\n"
        f"This Week: {stats['week']}\n"
        f"This Month: {stats['month']}\n\n"
        f"{ROCKET} Started Setup: {clicked}/{total}\n"
        f"Conversion Rate: {conversion}%"
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
        f"{TRIDENT} LIVE IMPERIUM DASHBOARD\n\n"
        f"Today's Leads: {stats['today']}\n"
        f"This Week: {stats['week']}\n"
        f"This Month: {stats['month']}\n\n"
        f"{ROCKET} Started Setup: {clicked}/{total}\n"
        f"Conversion Rate: {conversion}%"
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
            text=build_dashboard_text(),
        )
    except Exception as e:
        logger.info(f"Dashboard update failed: {e}")


async def panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"{TRIDENT} Imperium Admin Panel\n\nChoose an option below:",
        reply_markup=admin_panel_keyboard(),
    )

async def listibs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ibs = get_active_ibs()

    if not ibs:
        await update.message.reply_text("No active IBs found.")
        return

    message = f"{TRIDENT} Active IB Rotation\n\n"

    for index, ib in enumerate(ibs, start=1):
        message += f"{index}. {ib['name']} - @{ib['username']}\n"

    await update.message.reply_text(message)
    
async def addib_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /addib Name @username")
            return
    
        username = context.args[-1].replace("@", "")
        name = " ".join(context.args[:-1])
    
        add_ib(name, username)
    
        await update.message.reply_text(
            f"{CHECK} Added IB:\n\n{name} - @{username}"
        )
    
async def removeib_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text(
            "Usage: /removeib @username"
        )
        return

    username = context.args[0].replace("@", "")

    remove_ib(username)

    await update.message.reply_text(
        f"{CHECK} Removed IB:\n\n@{username}"
    )

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    state, value = get_admin_state(user_id)

    if state == "awaiting_ib_name":
        set_admin_state(user_id, "awaiting_ib_username", text)

        await update.message.reply_text(
            f"{TRIDENT} Got it.\n\nNow send the IB's @username."
        )
        return

    if state == "awaiting_ib_username":
        name = value
        username = text.replace("@", "")

        add_ib(name, username)
        set_admin_state(user_id, "", "")

        await update.message.reply_text(
            f"{CHECK} Added IB:\n\n{name} - @{username}",
            reply_markup=admin_panel_keyboard()
        )
        return
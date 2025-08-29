#SahilxCodes

from pyrogram import Client, filters
from pyrogram.types import Message
from config import OWNER_ID
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import asyncio

# Example plans (days : (label, price))
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import asyncio
from config import OWNER_ID
#========================================================================#



# Example default plans (key: (label, duration_in_seconds))
PLANS = {
    "7d": ("7 Days", 7 * 24 * 60 * 60),
    "1m": ("1 Month", 30 * 24 * 60 * 60),
    "3m": ("3 Months", 90 * 24 * 60 * 60),
}


# -----------------------
# STEP 1: AUTHORIZE COMMAND
# -----------------------
@Client.on_message(filters.command('authorize') & filters.private)
async def authorize_command(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("Only Owner can use this command...!")

    if len(message.command) < 2:
        return await message.reply_text("<b>Format:</b> /authorize <userid> [plan]\n\n"
                                        "Example:\n"
                                        "/authorize 123456 7d\n"
                                        "/authorize 123456 2m")

    try:
        user_id_to_add = int(message.command[1])
        user = await client.get_users(user_id_to_add)
        user_name = user.first_name + (" " + user.last_name if user.last_name else "")
    except Exception as e:
        return await message.reply_text(f"Error: {e}")

    # Case 1: /authorize <userid> <plan tenure>
    if len(message.command) == 3:
        plan_input = message.command[2].lower()

        if plan_input in PLANS:
            plan_name, duration_seconds = PLANS[plan_input]
        elif plan_input.endswith("m") and plan_input[:-1].isdigit():  # custom months like 2m, 6m
            months = int(plan_input[:-1])
            duration_seconds = months * 30 * 24 * 60 * 60
            plan_name = f"{months} Month(s) (Custom)"
        else:
            return await message.reply_text("❌ Invalid plan format. Use 7d, 1m, 3m, or Xm for custom months.")

        # Add to DB
        if not await client.mongodb.is_pro(user_id_to_add):
            await client.mongodb.add_pro(user_id_to_add)

        await message.reply_text(
            f"<b>User {user_name} - {user_id_to_add} is now a pro user with {plan_name} plan..!</b>"
        )

        try:
            await client.send_message(
                user_id_to_add,
                f"<b>🎉 Congratulations! Your membership has been activated for {plan_name}.</b>"
            )
        except Exception as e:
            await message.reply_text(f"Failed to notify user: {e}")
        return

    # Case 2: /authorize <userid> → show inline buttons
    client.temp_auth = {"user_id": user_id_to_add, "user_name": user_name}

    buttons = [
        [
            InlineKeyboardButton("7 Days", callback_data="plan_7d"),
            InlineKeyboardButton("1 Month", callback_data="plan_1m"),
            InlineKeyboardButton("3 Months", callback_data="plan_3m"),
        ],
        [
            InlineKeyboardButton("📅 Custom Timeline", callback_data="plan_custom")
        ]
    ]

    await message.reply_text(
        f"Select a plan for <b>{user_name}</b> ({user_id_to_add}):",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# -----------------------
# STEP 2: PLAN SELECTION CALLBACK
# -----------------------
@Client.on_callback_query(filters.regex(r"^plan_"))
async def handle_plan_selection(client: Client, query: CallbackQuery):
    if query.from_user.id != OWNER_ID:
        return await query.answer("Not for you!", show_alert=True)

    user_id = client.temp_auth["user_id"]
    user_name = client.temp_auth["user_name"]
    plan_key = query.data.split("_")[1]

    if plan_key == "custom":
        await query.message.edit_text("Enter the number of months for custom plan (e.g., 2 for 2 months):")
        client.waiting_custom = user_id  # mark waiting for custom input
        return

    if plan_key not in PLANS:
        return await query.answer("Invalid plan!")

    plan_name, duration_seconds = PLANS[plan_key]

    if not await client.mongodb.is_pro(user_id):
        await client.mongodb.add_pro(user_id)

    await query.message.edit_text(
        f"<b>User {user_name} - {user_id} is now a pro user with {plan_name} plan..!</b>"
    )

    try:
        await client.send_message(
            user_id,
            f"<b>🎉 Congratulations! Your membership has been activated for {plan_name}.</b>"
        )
    except Exception as e:
        await query.message.reply_text(f"Failed to notify user: {e}")


# -----------------------
# STEP 3: CUSTOM PLAN INPUT
# -----------------------
@Client.on_message(filters.private)
async def handle_custom_months(client: Client, message: Message):
    if not hasattr(client, "waiting_custom"):
        return
    if message.from_user.id != OWNER_ID:
        return

    user_id = client.waiting_custom
    try:
        months = int(message.text.strip())
    except:
        return await message.reply_text("❌ Invalid input. Enter only a number (months).")

    user_name = client.temp_auth["user_name"]
    duration_seconds = months * 30 * 24 * 60 * 60
    plan_name = f"{months} Month(s) (Custom)"

    if not await client.mongodb.is_pro(user_id):
        await client.mongodb.add_pro(user_id)

    await message.reply_text(
        f"<b>User {user_name} - {user_id} is now a pro user with {plan_name} plan..!</b>"
    )

    try:
        await client.send_message(
            user_id,
            f"<b>🎉 Congratulations! Your membership has been activated for {plan_name}.</b>"
        )
    except Exception as e:
        await message.reply_text(f"Failed to notify user: {e}")

    del client.waiting_custom



#========================================================================#

@Client.on_message(filters.command('unauthorize') & filters.private)
async def remove_admin_command(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("Only Owner can use this command...!")

    if len(message.command) != 2:
        return await message.reply_text("<b>You're using wrong format do like this:</b> /unauthorize <userid>")

    try:
        user_id_to_remove = int(message.command[1])
    except ValueError:
        return await message.reply_text("Invalid user ID. Please check again...!")

    try:
        user = await client.get_users(user_id_to_remove)
        user_name = user.first_name + (" " + user.last_name if user.last_name else "")
    except Exception as e:
        return await message.reply_text(f"Error fetching user information: {e}")

    if await client.mongodb.is_pro(user_id_to_remove):
        await client.mongodb.remove_pro(user_id_to_remove)
        await message.reply_text(f"<b>User {user_name} - {user_id_to_remove} has been removed from pro users...!</b>")
        try:
            await client.send_message(user_id_to_remove, "<b>You membership has been ended.\n\nTo renew the membership\nContact: @Izana_Sensei.</b>")
        except Exception as e:
            await message.reply_text(f"Failed to notify the user: {e}")
    else:
        await message.reply_text(f"<b>User {user_name} - {user_id_to_remove} is not a pro user or was not found in the pro list.</b>")

#========================================================================#

@Client.on_message(filters.command('authorized') & filters.private)
async def admin_list_command(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("Only Owner can use this command...!")

    pro_user_ids = await client.mongodb.get_all_pros()
    formatted_admins = []

    for user_id in pro_user_ids:
        try:
            user = await client.get_users(user_id)
            full_name = user.first_name + (" " + user.last_name if user.last_name else "")
            username = f"@{user.username}" if user.username else "No Username"
            formatted_admins.append(f"{full_name} - {username}")
        except:
            continue

    if formatted_admins:
        await message.reply_text(
            f"<b>List of admin users:</b>\n\n" + "\n".join(formatted_admins),
            disable_web_page_preview=True
        )
    else:

        await message.reply_text("<b>No admin users found.</b>")

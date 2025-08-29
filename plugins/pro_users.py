from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import OWNER_ID
#========================================================================#
#========================================================================#
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import asyncio
from config import OWNER_ID

PLANS = {
    "7d": ("7 Days", 40, 7 * 24 * 60 * 60),
    "1m": ("1 Month", 100, 30 * 24 * 60 * 60),
    "3m": ("3 Months", 200, 90 * 24 * 60 * 60),
}

@Client.on_message(filters.command('authorize') & filters.private)
async def authorize(client, message):
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("Only Owner can use this command...!")

    if len(message.command) != 2:
        return await message.reply_text("<b>Format:</b> /authorize <userid>")

    try:
        user_id = int(message.command[1])
        user = await client.get_users(user_id)
        user_name = user.first_name + (" " + user.last_name if user.last_name else "")
    except Exception as e:
        return await message.reply_text(f"Error: {e}")

    client.temp_auth = {"user_id": user_id, "user_name": user_name}

    buttons = [
        [
            InlineKeyboardButton("7 Days", callback_data="plan_7d"),
            InlineKeyboardButton("1 Month", callback_data="plan_1m"),
            InlineKeyboardButton("3 Months", callback_data="plan_3m"),
        ],
        [InlineKeyboardButton("❌ None", callback_data="plan_none")]
    ]

    await message.reply_text(
        f"Select a plan for <b>{user_name}</b> ({user_id}):",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex(r"^plan_"))
async def handle_plan(client, query: CallbackQuery):
    if query.from_user.id != OWNER_ID:
        return await query.answer("Not for you!", show_alert=True)

    plan_key = query.data.split("_")[1]
    user_id = client.temp_auth["user_id"]
    user_name = client.temp_auth["user_name"]

    # remove the whole selection message
    await query.message.delete()

    if plan_key == "none":
        if not await client.mongodb.is_pro(user_id):
            await client.mongodb.add_pro(user_id)

        await query.message.reply_text(
            f"<b>User {user_name} - {user_id} is now a pro user with Custom plan..!</b>"
        )
        try:
            await client.send_message(
                user_id, "<b>🎉 Congratulations! Your membership has been activated for custom plan.</b>"
            )
        except Exception as e:
            await query.message.reply_text(f"Failed to notify user: {e}")
        return

    if plan_key not in PLANS:
        return await query.answer("Invalid plan!")

    plan_name, price, duration = PLANS[plan_key]

    if not await client.mongodb.is_pro(user_id):
        await client.mongodb.add_pro(user_id)

    await query.message.reply_text(
        f"<b>User {user_name} - {user_id} is now a pro user with {plan_name} plan..!</b>"
    )

    try:
        await client.send_message(
            user_id, f"<b>🎉 Congratulations! Your membership has been activated for {plan_name}.</b>"
        )
    except Exception as e:
        await query.message.reply_text(f"Failed to notify user: {e}")


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



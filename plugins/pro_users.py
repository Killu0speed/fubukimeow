from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import OWNER_ID
#========================================================================#
#========================================================================#

PLANS = {
    "7d": "7 Days",
    "1m": "1 Month",
    "3m": "3 Months",
    "none": "Custom Plan",
}

# -----------------------
# AUTHORIZE COMMAND
# -----------------------
@Client.on_message(filters.command('authorize') & filters.private)
async def add_admin_command(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("Only Owner can use this command...!")

    if len(message.command) < 2:
        return await message.reply_text("<b>Format:</b> /authorize <userid> [plan]")

    try:
        user_id_to_add = int(message.command[1])
        user = await client.get_users(user_id_to_add)
        user_name = user.first_name + (" " + user.last_name if user.last_name else "")
    except Exception as e:
        return await message.reply_text(f"Error: {e}")

    # Check if already pro
    if await client.mongodb.is_pro(user_id_to_add):
        return await message.reply_text(f"<b>User {user_name} - {user_id_to_add} is already a pro.</b>")

    # Case 1: Direct plan given
    if len(message.command) == 3:
        plan_key = message.command[2].lower()
        if plan_key not in PLANS:
            return await message.reply_text("❌ Invalid plan. Use: 7d / 1m / 3m / none")

        plan_name = PLANS[plan_key]
        await client.mongodb.add_pro(user_id_to_add)

        # Confirmation to owner
        await message.reply_text(
            f"<b>✅ {user_name} ({user_id_to_add}) has been authorized for {plan_name}.</b>"
        )

        # Notify user
        try:
            await client.send_message(
                user_id_to_add,
                f"<b>🎉 Congratulations! Your membership has been activated for {plan_name}.</b>"
            )
        except Exception as e:
            await message.reply_text(f"⚠️ Couldn’t notify user: {e}")
        return

    # Case 2: No plan → show buttons
    client.temp_auth = {"user_id": user_id_to_add, "user_name": user_name}

    buttons = [[
        InlineKeyboardButton("7 Days", callback_data="plan_7d"),
        InlineKeyboardButton("1 Month", callback_data="plan_1m"),
        InlineKeyboardButton("3 Months", callback_data="plan_3m"),
        InlineKeyboardButton("None", callback_data="plan_none"),
    ]]

    await message.reply_text(
        f"Select a plan for <b>{user_name}</b> ({user_id_to_add}):",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# -----------------------
# PLAN SELECTION CALLBACK
# -----------------------
@Client.on_callback_query(filters.regex(r"^plan_"))
async def handle_plan_selection(client: Client, query: CallbackQuery):
    if query.from_user.id != OWNER_ID:
        return await query.answer("Not for you!", show_alert=True)

    plan_key = query.data.split("_")[1]
    if plan_key not in PLANS:
        return await query.answer("Invalid plan!")

    user_id = client.temp_auth["user_id"]
    user_name = client.temp_auth["user_name"]
    plan_name = PLANS[plan_key]

    # Add user to pro DB
    await client.mongodb.add_pro(user_id)

    # Remove buttons
    await query.message.edit_reply_markup(reply_markup=None)

    # Confirmation to owner
    await query.message.reply_text(
        f"<b>✅ {user_name} ({user_id}) has been authorized for {plan_name}.</b>"
    )

    # Notify user
    try:
        await client.send_message(
            user_id,
            f"<b>🎉 Congratulations! Your membership has been activated for {plan_name}.</b>"
        )
    except Exception as e:
        await query.message.reply_text(f"⚠️ Couldn’t notify user: {e}")



#========================================================================#
@Client.on_message(filters.command('unauthorize') & filters.private)
async def remove_admin_command(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("Only Owner can use this command...!")

    if len(message.command) != 2:
        return await message.reply_text("<b>You're using wrong format. Use:</b> /unauthorize <userid>")

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
        # Remove from DB
        await client.mongodb.remove_pro(user_id_to_remove)

        # Confirm to owner
        await message.reply_text(
            f"<b>User {user_name} ({user_id_to_remove}) has been removed from pro users.</b>"
        )

        # Notify user
        try:
            await client.send_message(
                user_id_to_remove,
                "<b>Your membership has ended. 💔</b>\n\n"
                "<blockquote expandable>\n"
                "💰 <b>Affordable Pricing:</b>\n"
                "○ <b>7 Days:</b> <code>INR 40</code>\n"
                "○ <b>1 Month:</b> <code>INR 100</code>\n"
                "○ <b>3 Months:</b> <code>INR 200</code>\n\n"
                "<b>Ready to Upgrade? 💓</b>\n"
                "<b>»</b> Message @Cultured_Alliance_probot\n"
                "</blockquote>"
            )
        except Exception as e:
            await message.reply_text(f"⚠️ Failed to notify user: {e}")
    else:
        await message.reply_text(
            f"<b>User {user_name} ({user_id_to_remove}) is not a pro user or was not found in the pro list.</b>"
        )


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







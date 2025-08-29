#SahilxCodes

from pyrogram import Client, filters
from pyrogram.types import Message
from config import OWNER_ID

#========================================================================#
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import OWNER_ID   # using your config import

# Standard plans mapping
PLANS = {
    "7d": "7 Days",
    "1m": "1 Month",
    "3m": "3 Months",
}

# -----------------------
# STEP 1: AUTHORIZE COMMAND
# -----------------------
@Client.on_message(filters.command('authorize') & filters.private)
async def add_admin_command(client: Client, message: Message):
    if message.from_user.id != OWNER_ID:
        return await message.reply_text("Only Owner can use this command...!")

    if len(message.command) < 2:
        return await message.reply_text("<b>Format:</b> /authorize <userid> [plan]\n\nExample:\n/authorize 123456 1m")

    try:
        user_id_to_add = int(message.command[1])
        user = await client.get_users(user_id_to_add)
        user_name = user.first_name + (" " + user.last_name if user.last_name else "")
    except Exception as e:
        return await message.reply_text(f"Error: {e}")

    # Already pro check
    if await client.mongodb.is_pro(user_id_to_add):
        return await message.reply_text(
            f"<b>User {user_name} - {user_id_to_add} is already a pro user.</b>"
        )

    # Case 1: Plan tenure is given directly in command
    if len(message.command) == 3:
        tenure = message.command[2].lower()

        if tenure in PLANS:   # predefined plans
            plan_name = PLANS[tenure]
        else:
            try:
                months = int(tenure)
                plan_name = f"{months} Month(s)"
            except:
                return await message.reply_text("Invalid plan tenure. Use 7d / 1m / 3m / <months>")

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

    # Case 2: No plan given → show selection buttons
    client.temp_auth = {"user_id": user_id_to_add, "user_name": user_name}

    buttons = [
        [
            InlineKeyboardButton("7 Days", callback_data="plan_7d"),
            InlineKeyboardButton("1 Month", callback_data="plan_1m"),
            InlineKeyboardButton("3 Months", callback_data="plan_3m"),
        ],
        [InlineKeyboardButton("Custom Plan", callback_data="plan_custom")]
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
        # Ask admin for custom months
        client.temp_auth["waiting_for_months"] = True
        return await query.message.edit_text("Enter number of months for this user:")

    plan_name = PLANS.get(plan_key)
    if not plan_name:
        return await query.answer("Invalid plan!")

    # Add to DB
    await client.mongodb.add_pro(user_id)

    # Notify admin
    await query.message.edit_text(
        f"<b>User {user_name} - {user_id} is now a pro user with {plan_name} plan..!</b>"
    )

    # Notify user
    try:
        await client.send_message(
            user_id,
            f"<b>🎉 Congratulations! Your membership has been activated for {plan_name}.</b>"
        )
    except Exception as e:
        await query.message.reply_text(f"Failed to notify user: {e}")

# -----------------------
# STEP 3: Handle custom months reply
# -----------------------
@Client.on_message(filters.private)
async def handle_custom_months(client: Client, message: Message):
    # Only owner + only if waiting
    if message.from_user.id != OWNER_ID:
        return
    if not getattr(client, "temp_auth", None):
        return
    if not client.temp_auth.get("waiting_for_months"):
        return

    try:
        months = int(message.text.strip())
    except:
        return await message.reply_text("Please enter a valid number of months!")

    user_id = client.temp_auth["user_id"]
    user_name = client.temp_auth["user_name"]
    plan_name = f"{months} Month(s)"

    # clear state
    client.temp_auth.pop("waiting_for_months", None)

    # Add to DB
    await client.mongodb.add_pro(user_id)

    # Notify admin
    await message.reply_text(
        f"<b>User {user_name} - {user_id} is now a pro user with {plan_name} plan..!</b>"
    )

    # Notify user
    try:
        await client.send_message(
            user_id,
            f"<b>🎉 Congratulations! Your membership has been activated for {plan_name}.</b>"
        )
    except Exception as e:
        await message.reply_text(f"Failed to notify user: {e}")



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






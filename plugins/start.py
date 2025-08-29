from helper.helper_func import *
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import humanize
from config import MSG_EFFECT, OWNER_ID
from plugins.shortner import get_short

#===============================================================#

@Client.on_message(filters.command('start') & filters.private)
@force_sub
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id

    # 1. Add user if not present
    present = await client.mongodb.present_user(user_id)
    if not present:
        try:
            await client.mongodb.add_user(user_id)
        except Exception as e:
            client.LOGGER(__name__, client.name).warning(f"Error adding a user:\n{e}")

    # 2. Check if banned
    is_banned = await client.mongodb.is_banned(user_id)
    if is_banned:
        return await message.reply("**You have been banned from using this bot!**")

    text = message.text
    if len(text) > 7:
        try:
            original_payload = text.split(" ", 1)[1]
            base64_string = original_payload

            is_short_link = False
            if base64_string.startswith("yu3elk"):
                base64_string = base64_string[6:-1]
                is_short_link = True

        except IndexError:
            return await message.reply("Invalid command format.")

        # 3. Check premium status
        if not is_user_pro and user_id != OWNER_ID and not is_short_link:
            try:
                short_link = get_short(f"https://t.me/{client.username}?start=yu3elk{base64_string}7", client)
                total_clicks = await total_click(base64_string)   # ✅ calculate clicks
            except Exception as e:
                client.LOGGER(__name__, client.name).warning(f"Shortener failed: {e}")
                return await message.reply("Couldn't generate short link.")
        
            # ✅ define message format (since you removed SHORT_MSG from setup.json)
            SHORT_MSG = "Total clicks :- {total_count}\nHere is your link 👇"
        
            # ✅ buttons like your snippet
            buttons = [
                [
                    InlineKeyboardButton(text="Short Link", url=short_link),
                    InlineKeyboardButton(text="Tutorial", url="https://t.me/tutorials_hanime/9"),
                ],
                [
                    InlineKeyboardButton(text="Premium 💸", callback_data="premium")
                ]
            ]
        
            await message.reply(
                text=SHORT_MSG.format(total_count=total_clicks),
                reply_markup=InlineKeyboardMarkup(buttons),
                quote=True,
                disable_web_page_preview=True
            )
            return # prevent sending actual files

        # 5. Decode and prepare file IDs
        try:
            string = await decode(base64_string)
            argument = string.split("-")
            ids = []

            if len(argument) == 3:
                start = int(int(argument[1]) / abs(client.db))
                end = int(int(argument[2]) / abs(client.db))
                ids = range(start, end + 1) if start <= end else list(range(start, end - 1, -1))

            elif len(argument) == 2:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]

        except Exception as e:
            client.LOGGER(__name__, client.name).warning(f"Error decoding base64: {e}")
            return await message.reply("⚠️ Invalid or expired link.")

        # 6. Get messages and forward
        temp_msg = await message.reply("Wait A Sec..")
        messages = []

        try:
            messages = await get_messages(client, ids)
        except Exception as e:
            await temp_msg.edit_text("Something went wrong!")
            client.LOGGER(__name__, client.name).warning(f"Error getting messages: {e}")
            return

        if not messages:
            return await temp_msg.edit("Couldn't find the files in the database.")
        await temp_msg.delete()

        yugen_msgs = []
        for msg in messages:
            caption = (
                client.messages.get('CAPTION', '').format(
                    previouscaption=msg.caption.html if msg.caption else msg.document.file_name
                ) if bool(client.messages.get('CAPTION', '')) and bool(msg.document)
                else ("" if not msg.caption else msg.caption.html)
            )
            reply_markup = msg.reply_markup if not client.disable_btn else None

            try:
                copied_msg = await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    reply_markup=reply_markup,
                    protect_content=client.protect
                )
                yugen_msgs.append(copied_msg)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                copied_msg = await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    reply_markup=reply_markup,
                    protect_content=client.protect
                )
                yugen_msgs.append(copied_msg)
            except Exception as e:
                client.LOGGER(__name__, client.name).warning(f"Failed to send message: {e}")
                pass

        # 7. Auto delete timer
        if messages and client.auto_del > 0:
            k = await client.send_message(
                chat_id=message.from_user.id,
                text=f'<blockquote><b><i>This File is deleting automatically in {humanize.naturaldelta(client.auto_del)}. Forward in your Saved Messages..!</i></b></blockquote>'
            )
            asyncio.create_task(delete_files(yugen_msgs, client, k, text))
        return

    # 8. Normal start message
    else:
        buttons = [[InlineKeyboardButton("Help", callback_data="about"), InlineKeyboardButton("Close", callback_data='close')]]
        if user_id in client.admins:
            buttons.insert(0, [InlineKeyboardButton("⛩️ ꜱᴇᴛᴛɪɴɢꜱ ⛩️", callback_data="settings")])

        photo = client.messages.get("START_PHOTO", "")
        start_caption = client.messages.get('START', 'Welcome, {mention}').format(
            first=message.from_user.first_name,
            last=message.from_user.last_name,
            username=None if not message.from_user.username else '@' + message.from_user.username,
            mention=message.from_user.mention,
            id=message.from_user.id
        )

        if photo:
            await client.send_photo(
                chat_id=message.chat.id,
                photo=photo,
                caption=start_caption,
                message_effect_id=MSG_EFFECT,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            await client.send_message(
                chat_id=message.chat.id,
                text=start_caption,
                message_effect_id=MSG_EFFECT,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        return

#===============================================================#

@Client.on_message(filters.command('request') & filters.private)
async def request_command(client: Client, message: Message):
    user_id = message.from_user.id
    is_admin = user_id in client.admins  # ✅ admin check
    is_user_premium = await client.mongodb.is_pro(user_id)  # ✅ new DB check

    # Sensei/admin bypass
    if is_admin or user_id == OWNER_ID:
        await message.reply_text("🔹 You're my sensei! This command is only for users.")
        return

    # Free user → callback Premium button (like old version)
    if not is_user_premium:   
        inline_button = InlineKeyboardButton("Upgrade to Premium", callback_data="premium")
        inline_keyboard = InlineKeyboardMarkup([[inline_button]])

        await message.reply(
            "You are not a premium user. Upgrade to premium to access this feature.",
            reply_markup=inline_keyboard
        )
        return

    # Format check
    if len(message.command) < 2:
        await message.reply("Send me your request in this format: /request hentai Name Quality Episode")
        return

    requested = " ".join(message.command[1:])

    # Owner notification (like old)
    owner_message = (
        f"{message.from_user.first_name} ({message.from_user.id})\n\n"
        f"uplaod karo:- {requested}"
    )
    await client.send_message(OWNER_ID, owner_message)

    # User confirmation (like old)
    await message.reply("Thanks for your request! Your request will be uploaded soon. Please wait.")


#===============================================================#

@Client.on_message(filters.command('profile') & filters.private)
async def my_plan(client: Client, message: Message):
    user_id = message.from_user.id
    is_admin = user_id in client.admins  # ✅ admin check

    # Sensei/admin bypass
    if is_admin or user_id == OWNER_ID:
        await message.reply_text("🔹 You're my sensei! This command is only for users.")
        return

    # ✅ Use new DB method for premium check
    is_user_premium = await client.mongodb.is_pro(user_id)

    # ✅ Same logic as old version
    if not is_user_premium and user_id != OWNER_ID:
        preference = "Enabled"   # Ads ON
        absence = "Disabled"     # Features OFF
    else:
        preference = "Disabled"  # Ads OFF
        absence = "Enabled"      # Features ON

    # Delete command message (like old version)
    await message.delete()

    # Show wait message
    msg = await client.send_message(chat_id=message.chat.id, text=WAIT_MSG)

    # Build profile text
    new_msg_text = (
        f"Name: {message.from_user.first_name}\n\n"
        f"Ad Link: {preference}\n"
        f"Direct Links: {absence}\n"
        f"On-Demand Hentai: {absence}"
    )

    if preference == "Disabled":
        new_msg_text += "\n\n🌟 You are a Pro User 🌟"

    # Edit wait message with profile
    new_msg = await msg.edit_text(new_msg_text)

    # If Free user → add Premium button
    if preference == "Enabled":
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Premium", callback_data="premium")]]
        )
        await new_msg.edit_text(new_msg.text, reply_markup=reply_markup)


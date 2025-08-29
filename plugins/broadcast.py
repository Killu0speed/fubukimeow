from pyrogram import Client, filters
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio

#===============================================================#

# Store broadcast states
BROADCAST_STATUS = {}  # { "message_id": {"status": "running", "admin_id": 123} }

#===============================================================#

@Client.on_message(filters.command('users'))
async def user_count(client, message):
    if message.from_user.id not in client.admins:
        return await client.send_message(message.from_user.id, "Only admins can use this command!")
    total_users = await client.mongodb.full_userbase()
    await message.reply(f"**{len(total_users)} Users are using this bot currently!**")

#===============================================================#
#===============================================================#

@Client.on_message(filters.private & filters.command('broadcast'))
async def send_text(client, message):
    if message.from_user.id not in client.admins:
        return

    if not message.reply_to_message:
        return await message.reply("Reply to a message to broadcast.")

    query = await client.mongodb.full_userbase()
    broadcast_msg = message.reply_to_message

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("⏸ Pause", callback_data=f"pause_{message.id}"),
         InlineKeyboardButton("⏹ Stop", callback_data=f"stop_{message.id}")]
    ])
    pls_wait = await message.reply(
        "<blockquote><i>Broadcasting Message.. This will Take Some Time</i></blockquote>",
        reply_markup=buttons
    )

    BROADCAST_STATUS[str(message.id)] = {"status": "running", "admin_id": message.from_user.id}

    total = successful = blocked = deleted = unsuccessful = 0

    for chat_id in query:
        while BROADCAST_STATUS[str(message.id)]["status"] == "paused":
            await asyncio.sleep(2)
        if BROADCAST_STATUS[str(message.id)]["status"] == "stopped":
            break

        try:
            await broadcast_msg.copy(chat_id)
            successful += 1
            print(f"{chat_id} broadcast message sent")  # ✅ log success
        except FloodWait as e:
            await asyncio.sleep(e.x)
            await broadcast_msg.copy(chat_id)
            successful += 1
            print(f"{chat_id} broadcast message sent after FloodWait")
        except UserIsBlocked:
            await client.mongodb.del_user(chat_id)
            blocked += 1
            print(f"{chat_id} is blocked")
        except InputUserDeactivated:
            await client.mongodb.del_user(chat_id)
            deleted += 1
            print(f"{chat_id} account deleted")
        except Exception as e:
            unsuccessful += 1
            print(f"Failed to send message to {chat_id}: {e}")
        total += 1

    status = f"""<blockquote><b><u>Broadcast Finished</u></b></blockquote>
<b>Total Users :</b> <code>{total}</code>
<b>Successful :</b> <code>{successful}</code>
<b>Blocked Users :</b> <code>{blocked}</code>
<b>Deleted Accounts :</b> <code>{deleted}</code>
<b>Unsuccessful :</b> <code>{unsuccessful}</code>"""

    await pls_wait.edit(status, reply_markup=None)
    BROADCAST_STATUS.pop(str(message.id), None)

#===============================================================#

@Client.on_message(filters.private & filters.command('pbroadcast'))
async def pin_bdcst_text(client, message):
    if message.from_user.id not in client.admins:
        return

    if not message.reply_to_message:
        return await message.reply("Reply to a message to broadcast.")

    query = await client.mongodb.full_userbase()
    broadcast_msg = message.reply_to_message

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("⏸ Pause", callback_data=f"pause_{message.id}"),
         InlineKeyboardButton("⏹ Stop", callback_data=f"stop_{message.id}")]
    ])
    pls_wait = await message.reply(
        "<blockquote><i>Broadcasting Message.. This will Take Some Time</i></blockquote>",
        reply_markup=buttons
    )

    BROADCAST_STATUS[str(message.id)] = {"status": "running", "admin_id": message.from_user.id}

    total = successful = blocked = deleted = unsuccessful = 0

    for chat_id in query:
        while BROADCAST_STATUS[str(message.id)]["status"] == "paused":
            await asyncio.sleep(2)
        if BROADCAST_STATUS[str(message.id)]["status"] == "stopped":
            break

        try:
            sent_msg = await broadcast_msg.copy(chat_id)
            successful += 1
            await client.pin_chat_message(chat_id=chat_id, message_id=sent_msg.id, both_sides=True)
            print(f"{chat_id} broadcast & pinned message sent")
        except FloodWait as e:
            await asyncio.sleep(e.x)
            sent_msg = await broadcast_msg.copy(chat_id)
            successful += 1
            await client.pin_chat_message(chat_id=chat_id, message_id=sent_msg.id)
            print(f"{chat_id} broadcast & pinned message sent after FloodWait")
        except UserIsBlocked:
            await client.mongodb.del_user(chat_id)
            blocked += 1
            print(f"{chat_id} is blocked")
        except InputUserDeactivated:
            await client.mongodb.del_user(chat_id)
            deleted += 1
            print(f"{chat_id} account deleted")
        except Exception as e:
            unsuccessful += 1
            print(f"Failed to send message to {chat_id}: {e}")
        total += 1

    status = f"""<blockquote><b><u>Broadcast Finished</u></b></blockquote>
<b>Total Users :</b> <code>{total}</code>
<b>Successful :</b> <code>{successful}</code>
<b>Blocked Users :</b> <code>{blocked}</code>
<b>Deleted Accounts :</b> <code>{deleted}</code>
<b>Unsuccessful :</b> <code>{unsuccessful}</code>"""

    await pls_wait.edit(status, reply_markup=None)
    BROADCAST_STATUS.pop(str(message.id), None)

#===============================================================#

# Control buttons handler
@Client.on_callback_query(filters.regex(r"^(pause|stop|resume)_(\d+)$"))
async def control_broadcast(client, query):
    action, msg_id = query.data.split("_", 1)

    if msg_id not in BROADCAST_STATUS:
        return await query.answer("Broadcast already finished.", show_alert=True)

    # Only admin who started it can control
    if query.from_user.id != BROADCAST_STATUS[msg_id]["admin_id"]:
        return await query.answer("You can't control this broadcast!", show_alert=True)

    if action == "pause":
        BROADCAST_STATUS[msg_id]["status"] = "paused"
        await query.answer("Broadcast paused.")
        await query.message.edit_reply_markup(
            InlineKeyboardMarkup([[InlineKeyboardButton("▶ Resume", callback_data=f"resume_{msg_id}"),
                                   InlineKeyboardButton("⏹ Stop", callback_data=f"stop_{msg_id}")]])
        )
    elif action == "resume":
        BROADCAST_STATUS[msg_id]["status"] = "running"
        await query.answer("Broadcast resumed.")
        await query.message.edit_reply_markup(
            InlineKeyboardMarkup([[InlineKeyboardButton("⏸ Pause", callback_data=f"pause_{msg_id}"),
                                   InlineKeyboardButton("⏹ Stop", callback_data=f"stop_{msg_id}")]])
        )
    elif action == "stop":
        BROADCAST_STATUS[msg_id]["status"] = "stopped"
        await query.answer("Broadcast stopped.")
        await query.message.edit_reply_markup(None)

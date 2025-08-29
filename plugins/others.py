from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import MSG_EFFECT

#==========================================================================#        

@Client.on_callback_query(filters.regex('^home$'))
async def home(client: Client, query: CallbackQuery):
    buttons = [[InlineKeyboardButton("Help", callback_data = "about"), InlineKeyboardButton("Close", callback_data = "close")]]
    if query.from_user.id in client.admins:
        buttons.insert(0, [InlineKeyboardButton("⛩️ ꜱᴇᴛᴛɪɴɢꜱ ⛩️", callback_data="settings")])
    await query.message.edit_text(
        text=client.messages.get('START', 'No Start Message').format(
            first=query.from_user.first_name,
            last=query.from_user.last_name,
            username=None if not query.from_user.username else '@' + query.from_user.username,
            mention=query.from_user.mention,
            id=query.from_user.id
                
        ),
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return

#==========================================================================#        

@Client.on_callback_query(filters.regex('^about$'))
async def about(client: Client, query: CallbackQuery):
    buttons = [[InlineKeyboardButton("Back", callback_data = "home"), InlineKeyboardButton("Close", callback_data = "close")]]
    await query.message.edit_text(
        text=client.messages.get('ABOUT', 'No Start Message').format(
            owner_id=client.owner,
            bot_username=client.username,
            first=query.from_user.first_name,
            last=query.from_user.last_name,
            username=None if not query.from_user.username else '@' + query.from_user.username,
            mention=query.from_user.mention,
            id=query.from_user.id
                
        ),
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return

#==========================================================================#        

@Client.on_callback_query(filters.regex('^close$'))
async def close(client: Client, query: CallbackQuery):
    await query.message.delete()
    try:
        await query.message.reply_to_message.delete()
    except:
        pass

#==========================================================================#        

@Client.on_message(filters.command('ban'))
async def ban(client: Client, message: Message):
    if message.from_user.id not in client.admins:
        return await message.reply(client.reply_text)
    try:
        user_ids = message.text.split(maxsplit=1)[1]
        c = 0
        for user_id in user_ids.split():
            user_id = int(user_id)
            c = c + 1
            if user_id in client.admins:
                continue
            if not await client.mongodb.present_user(user_id):
                await client.mongodb.add_user(user_id, True)
                continue
            else:
                await client.mongodb.ban_user(user_id)
        return await message.reply(f"__{c} users have been banned!__")
    except Exception as e:
    
        return await message.reply(f"**Error:** `{e}`")

#==========================================================================#        

@Client.on_message(filters.command('unban'))
async def unban(client: Client, message: Message):
    if message.from_user.id not in client.admins:
        return await message.reply(client.reply_text)
    try:
        user_ids = message.text.split(maxsplit=1)[1]
        c = 0
        for user_id in user_ids.split():
            user_id = int(user_id)
            c = c + 1
            if user_id in client.admins:
                continue
            if not await client.mongodb.present_user(user_id):
                await client.mongodb.add_user(user_id)
                continue
            else:
                await client.mongodb.unban_user(user_id)
        return await message.reply(f"__{c} users have been unbanned!__")
    except Exception as e:
    
        return await message.reply(f"**Error:** `{e}`")

#==========================================================================#                
#==========================================================================#        

@Client.on_callback_query(filters.regex("^premium$"))
async def premium(client: Client, query: CallbackQuery):
    await query.message.reply_text(
        text=(
            "<b>✨ Exclusive Premium Membership ✨</b>\n"
            "<i>Unlock a World of Benefits Just for You!</i>\n\n"
            "<b>🔥 Premium Perks:</b>\n"
            "✔️ <i>Direct Channel Links – No Ads, No Distractions!</i>\n"
            "✔️ <i>Special Access to Exclusive Events & Content</i>\n"
            "✔️ <i>Faster Support & Priority Assistance</i>\n\n"
            "<b>💭 Plus:</b> You'll get <b>direct access to all the channels</b> with any of these plans!\n\n"
            "<b>💰 Affordable Pricing:</b>\n"
            "○ <b>7 Days:</b> <code>INR 40</code>\n"
            "○ <b>1 Month:</b> <code>INR 100</code>\n"
            "○ <b>3 Months:</b> <code>INR 200</code>\n\n"
            "<b>Ready to Upgrade?</b>\n"
            "» Message @Cultured_Alliance_probot to get UPI or QR Code for payment.\n"
            "» Send a screenshot of your payment to @Cultured_Alliance_probot <i>(for Auto Verification)</i>.\n\n"
            "⚡ <b>Seats are LIMITED for Premium Members – Grab Yours Now!</b>"
        ),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("⚡ ᴄᴜʟᴛᴜʀᴇᴅ ᴀʟʟɪᴀɴᴄᴇ", url="https://t.me/culturedx_alliance"),
                    InlineKeyboardButton("🍁 ᴄʟᴏꜱᴇ", callback_data="close")
                ]
            ]
        )
    )


#==========================================================================#        
@Client.on_callback_query(filters.regex("^back$"))
async def back(client: Client, query: CallbackQuery):
    await query.message.edit_reply_markup(None)




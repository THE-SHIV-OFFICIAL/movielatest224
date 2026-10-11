import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from info import *
from utils import get_settings, save_group_settings, temp

# FTM Gamma Mode Commands Handler

@Client.on_message(filters.command("ftm_gamma") & filters.group)
async def ftm_gamma_command(client, message):
    """Handle /ftm_gamma on/off commands - Admin only"""
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return
    
    # Check if user is admin in the group
    try:
        st = await client.get_chat_member(message.chat.id, userid)
        if (
            st.status != enums.ChatMemberStatus.ADMINISTRATOR
            and st.status != enums.ChatMemberStatus.OWNER
            and userid not in ADMINS
            and str(userid) not in ADMINS
        ):
            await message.reply_text("❌ Only group admins can use this command!")
            return
    except Exception:
        return
    
    # Parse command arguments
    if len(message.command) < 2:
        # Show current status
        settings = await get_settings(message.chat.id)
        current_status = settings.get('ftm_gamma_mode', False)  # Default disabled
        status_text = "✅ Enabled" if current_status else "❌ Disabled"
        await message.reply_text(
            f"📡 **FTM Gamma Mode Status:** {status_text}\n\n"
            f"**Usage:**\n"
            f"• `/ftm_gamma on` - Enable gamma mode\n"
            f"• `/ftm_gamma off` - Disable gamma mode\n\n"
            f"**What is Gamma Mode?**\n"
            f"When enabled, users can search in groups and get download links via PM."
        )
        return
    
    command_arg = message.command[1].lower()
    
    if command_arg == "on":
        await save_group_settings(message.chat.id, 'ftm_gamma_mode', True)
        await message.reply_text("✅ **FTM Gamma Mode Enabled!**\n\nUsers can now search in this group and get files via PM.")
        
    elif command_arg == "off":
        await save_group_settings(message.chat.id, 'ftm_gamma_mode', False)
        await message.reply_text("❌ **FTM Gamma Mode Disabled!**\n\nGroup search redirection to PM is now turned off.")
        
    else:
        await message.reply_text(
            "❌ **Invalid command!**\n\n"
            "**Usage:**\n"
            "• `/ftm_gamma on` - Enable gamma mode\n"
            "• `/ftm_gamma off` - Disable gamma mode"
        )
import asyncio
import logging
from datetime import datetime, timedelta
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import PeerIdInvalid, UserIsBlocked, RPCError
from info import AUTO_DELETE_ENABLED
from ftmbotzx_botz import FtmbotzxBot

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store message deletion tasks
pending_deletions = {}

async def schedule_message_deletion_with_countdown(chat_id: int, message_id: int, chat_title: str, message_type: str = "BOT"):
    """Schedule message deletion with countdown logging"""
    try:
        # Log initial scheduling
        logger.info(f"⏰ AUTO-DELETE: Scheduled deletion for {message_type} message ID {message_id} in '{chat_title}' ({chat_id}) in 5 minutes")
        
        # Wait 4 minutes and log
        await asyncio.sleep(240)
        logger.info(f"⏳ AUTO-DELETE: {message_type} message ID {message_id} in '{chat_title}' ({chat_id}) will be deleted in 60 seconds...")
        
        # Wait 50 seconds and log
        await asyncio.sleep(50)
        logger.info(f"⏳ AUTO-DELETE: {message_type} message ID {message_id} in '{chat_title}' ({chat_id}) will be deleted in 10 seconds...")
        
        # Wait 5 seconds and log
        await asyncio.sleep(5)
        logger.info(f"⏳ AUTO-DELETE: {message_type} message ID {message_id} in '{chat_title}' ({chat_id}) will be deleted in 5 seconds...")
        
        # Wait 4 seconds and log
        await asyncio.sleep(4)
        logger.info(f"🔥 AUTO-DELETE: Deleting {message_type} message ID {message_id} from '{chat_title}' ({chat_id}) NOW...")
        
        # Wait 1 second
        await asyncio.sleep(1)
        
        # Attempt to delete the message (SIRF MESSAGE DELETE HOGA, USER NAHI)
        try:
            await FtmbotzxBot.delete_messages(chat_id=chat_id, message_ids=message_id)
            logger.info(f"✅ AUTO-DELETE SUCCESS: {message_type} message ID {message_id} deleted from '{chat_title}' ({chat_id}) after 5 minutes")
        except Exception as e:
            logger.warning(f"❌ AUTO-DELETE FAILED: Could not delete {message_type} message ID {message_id} from '{chat_title}' ({chat_id}): {e}")
        
        # Remove from pending deletions
        if (chat_id, message_id) in pending_deletions:
            del pending_deletions[(chat_id, message_id)]
            
    except asyncio.CancelledError:
        logger.info(f"🚫 AUTO-DELETE: Deletion cancelled for {message_type} message ID {message_id} from '{chat_title}' ({chat_id})")
        if (chat_id, message_id) in pending_deletions:
            del pending_deletions[(chat_id, message_id)]
    except Exception as e:
        logger.error(f"💥 AUTO-DELETE: Error in deletion scheduler for {message_type} message ID {message_id}: {e}")
        if (chat_id, message_id) in pending_deletions:
            del pending_deletions[(chat_id, message_id)]

def schedule_user_message_deletion(chat_id: int, message_id: int, chat_title: str):
    """Schedule deletion of user message that triggered bot response"""
    if AUTO_DELETE_ENABLED and chat_id and message_id:
        # Schedule deletion for user message
        task = asyncio.create_task(
            schedule_message_deletion_with_countdown(chat_id, message_id, chat_title, "USER")
        )
        pending_deletions[(chat_id, message_id)] = task
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        delete_time = (datetime.now() + timedelta(minutes=5)).strftime("%H:%M:%S")
        
        logger.info(f"📥 USER MESSAGE TRACKED:")
        logger.info(f"   • Group: '{chat_title}' ({chat_id})")
        logger.info(f"   • Message ID: {message_id}")
        logger.info(f"   • Time: {timestamp}")
        logger.info(f"   • Scheduled deletion: {delete_time}")

# Store the original method
original_send_message = FtmbotzxBot.send_message

async def hooked_send_message(chat_id, text, *args, **kwargs):
    """Hooked version of send_message that logs and schedules deletion without crashing on invalid users"""
    try:
        # Get reply_to_message_id from kwargs to track user message
        reply_to_message_id = kwargs.get('reply_to_message_id')
        
        # Call the original method
        result = await original_send_message(chat_id, text, *args, **kwargs)
        
        # If auto-delete is enabled and we have a result, schedule deletion for group messages
        if result and AUTO_DELETE_ENABLED and hasattr(result, 'chat'):
            chat = result.chat
            if hasattr(chat, 'type') and chat.type.name in ["GROUP", "SUPERGROUP"]:
                chat_title = getattr(chat, 'title', 'Unknown Group')
                message_id = result.id
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                delete_time = (datetime.now() + timedelta(minutes=5)).strftime("%H:%M:%S")
                
                # Get message content
                message_text = ""
                if hasattr(result, 'text') and result.text:
                    message_text = result.text[:100]
                elif hasattr(result, 'caption') and result.caption:
                    message_text = result.caption[:100]
                else:
                    message_text = "[Media/File/Other content]"
                
                # Log the sent message with detailed info
                logger.info(f"📤 BOT MESSAGE SENT:")
                logger.info(f"   • Group: '{chat_title}' ({chat_id})")
                logger.info(f"   • Message ID: {message_id}")
                logger.info(f"   • Time: {timestamp}")
                logger.info(f"   • Content: {message_text}")
                logger.info(f"   • Scheduled deletion: {delete_time}")
                
                # Schedule deletion for bot message
                task = asyncio.create_task(
                    schedule_message_deletion_with_countdown(chat_id, message_id, chat_title, "BOT")
                )
                pending_deletions[(chat_id, message_id)] = task
                
                # If this is a reply to a user message, schedule deletion for the user message too
                if reply_to_message_id:
                    schedule_user_message_deletion(chat_id, reply_to_message_id, chat_title)
        
        return result

    # ==========================================
    # 🔥 YAHAN MAIN FIX HAI 🔥
    # Agar user ne block kiya hai ya ID invalid hai, toh bas ignore karo. 
    # USER KO DATABASE SE REMOVE NAHI KAREGA!
    # ==========================================
    except PeerIdInvalid:
        # Bas silently ignore kar do, koi action mat lo
        return None
    except UserIsBlocked:
        # Bas silently ignore kar do
        return None
    except RPCError:
        # Kisi aur Telegram error pe bhi ignore karo
        return None
    except Exception as e:
        logger.error(f"❌ Error in hooked_send_message for {chat_id}: {e}")
        return None

# Replace the send_message method with our safe hooked version
FtmbotzxBot.send_message = hooked_send_message

@FtmbotzxBot.on_message(filters.command("toggle_auto_delete") & filters.user([8418584090])) 
async def toggle_auto_delete(client, message: Message):
    """Toggle auto delete feature on/off"""
    global AUTO_DELETE_ENABLED
    
    AUTO_DELETE_ENABLED = not AUTO_DELETE_ENABLED
    status = "ENABLED" if AUTO_DELETE_ENABLED else "DISABLED"
    
    await message.reply(f"🔧 Auto-delete feature is now **{status}**")
    logger.info(f"🔧 AUTO-DELETE: Feature toggled to {status} by user {message.from_user.id}")

@FtmbotzxBot.on_message(filters.command("auto_delete_status") & filters.user([8418584090])) 
async def auto_delete_status(client, message: Message):
    """Check auto delete status"""
    status = "ENABLED" if AUTO_DELETE_ENABLED else "DISABLED"
    pending_count = len(pending_deletions)
    
    await message.reply(
        f"📊 **Auto-Delete Status:**\n"
        f"• Status: **{status}**\n"
        f"• Pending deletions: **{pending_count}**\n"
        f"• Delete delay: **5 minutes**\n"
        f"• Applies to: Groups and Supergroups only\n"
        f"• Deletes: Both user queries and bot responses"
    )

# Log plugin initialization
logger.info("🔌 AUTO-DELETE PLUGIN: Initialized successfully")
logger.info(f"🔧 AUTO-DELETE PLUGIN: Status - {'ENABLED' if AUTO_DELETE_ENABLED else 'DISABLED'}")
logger.info("✅ AUTO-DELETE PLUGIN: Hooked safely into FtmbotzxBot.send_message method (Errors Ignored)")

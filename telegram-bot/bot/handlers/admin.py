from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from sqlalchemy.orm import Session
import logging

import sys
sys.path.append('/app/shared')

from models import User, UserStatus, DownloadJob, AdminAction
from database import get_db_session

logger = logging.getLogger(__name__)


async def cmd_approve(message: types.Message, is_admin: bool):
    """Approve a user"""
    if not is_admin:
        await message.answer("❌ This command is only available to admins.")
        return

    args = message.get_args()
    if not args:
        await message.answer("Usage: /approve <user_id>")
        return

    try:
        user_id = int(args)
    except ValueError:
        await message.answer("❌ Invalid user ID. Must be a number.")
        return

    db = get_db_session()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()

        if not user:
            await message.answer(f"❌ User {user_id} not found.")
            return

        if user.status == UserStatus.APPROVED:
            await message.answer(f"✅ User {user_id} is already approved.")
            return

        # Approve user
        user.status = UserStatus.APPROVED
        db.commit()

        # Log admin action
        action = AdminAction(
            admin_id=message.from_user.id,
            action_type="approve",
            target_user_id=user_id,
        )
        db.add(action)
        db.commit()

        await message.answer(
            f"✅ User approved:\n"
            f"ID: {user.telegram_id}\n"
            f"Name: {user.first_name or ''} {user.last_name or ''}\n"
            f"Username: @{user.username if user.username else 'N/A'}"
        )

        # Try to notify the user
        try:
            from aiogram import Bot
            bot = message.bot
            await bot.send_message(
                user_id,
                "🎉 Your access has been approved! You can now use the bot.\n\n"
                "Use /help to see available commands."
            )
        except Exception as e:
            logger.warning(f"Could not notify user {user_id}: {e}")

    except Exception as e:
        logger.error(f"Error approving user: {e}")
        await message.answer(f"❌ Error: {str(e)}")
    finally:
        db.close()


async def cmd_reject(message: types.Message, is_admin: bool):
    """Reject a user"""
    if not is_admin:
        await message.answer("❌ This command is only available to admins.")
        return

    args = message.get_args()
    if not args:
        await message.answer("Usage: /reject <user_id>")
        return

    try:
        user_id = int(args)
    except ValueError:
        await message.answer("❌ Invalid user ID. Must be a number.")
        return

    db = get_db_session()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()

        if not user:
            await message.answer(f"❌ User {user_id} not found.")
            return

        # Reject user
        user.status = UserStatus.REJECTED
        db.commit()

        # Log admin action
        action = AdminAction(
            admin_id=message.from_user.id,
            action_type="reject",
            target_user_id=user_id,
        )
        db.add(action)
        db.commit()

        await message.answer(f"❌ User {user_id} has been rejected.")

        # Try to notify the user
        try:
            await message.bot.send_message(
                user_id,
                "❌ Your access request has been rejected."
            )
        except Exception as e:
            logger.warning(f"Could not notify user {user_id}: {e}")

    except Exception as e:
        logger.error(f"Error rejecting user: {e}")
        await message.answer(f"❌ Error: {str(e)}")
    finally:
        db.close()


async def cmd_ban(message: types.Message, is_admin: bool):
    """Ban a user"""
    if not is_admin:
        await message.answer("❌ This command is only available to admins.")
        return

    args = message.get_args()
    if not args:
        await message.answer("Usage: /ban <user_id>")
        return

    try:
        user_id = int(args)
    except ValueError:
        await message.answer("❌ Invalid user ID. Must be a number.")
        return

    db = get_db_session()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()

        if not user:
            await message.answer(f"❌ User {user_id} not found.")
            return

        if user.is_admin:
            await message.answer("❌ Cannot ban an admin user.")
            return

        # Ban user
        user.status = UserStatus.BANNED
        db.commit()

        # Log admin action
        action = AdminAction(
            admin_id=message.from_user.id,
            action_type="ban",
            target_user_id=user_id,
        )
        db.add(action)
        db.commit()

        await message.answer(f"🚫 User {user_id} has been banned.")

        # Try to notify the user
        try:
            await message.bot.send_message(
                user_id,
                "🚫 You have been banned from using this bot."
            )
        except Exception as e:
            logger.warning(f"Could not notify user {user_id}: {e}")

    except Exception as e:
        logger.error(f"Error banning user: {e}")
        await message.answer(f"❌ Error: {str(e)}")
    finally:
        db.close()


async def cmd_users(message: types.Message, is_admin: bool):
    """List all approved users"""
    if not is_admin:
        await message.answer("❌ This command is only available to admins.")
        return

    db = get_db_session()
    try:
        users = db.query(User).filter(User.status == UserStatus.APPROVED).all()

        if not users:
            await message.answer("No approved users found.")
            return

        text = "✅ Approved Users:\n\n"
        for user in users:
            admin_badge = "👑 " if user.is_admin else ""
            text += (
                f"{admin_badge}ID: {user.telegram_id}\n"
                f"Name: {user.first_name or ''} {user.last_name or ''}\n"
                f"Username: @{user.username if user.username else 'N/A'}\n"
                f"Joined: {user.created_at.strftime('%Y-%m-%d')}\n\n"
            )

        await message.answer(text)

    except Exception as e:
        logger.error(f"Error listing users: {e}")
        await message.answer(f"❌ Error: {str(e)}")
    finally:
        db.close()


async def cmd_pending(message: types.Message, is_admin: bool):
    """List pending users"""
    if not is_admin:
        await message.answer("❌ This command is only available to admins.")
        return

    db = get_db_session()
    try:
        users = db.query(User).filter(User.status == UserStatus.PENDING).all()

        if not users:
            await message.answer("No pending users.")
            return

        text = "⏳ Pending Users:\n\n"
        for user in users:
            text += (
                f"ID: {user.telegram_id}\n"
                f"Name: {user.first_name or ''} {user.last_name or ''}\n"
                f"Username: @{user.username if user.username else 'N/A'}\n"
                f"Requested: {user.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
            )

        text += "\nUse /approve <user_id> to approve a user."

        await message.answer(text)

    except Exception as e:
        logger.error(f"Error listing pending users: {e}")
        await message.answer(f"❌ Error: {str(e)}")
    finally:
        db.close()


async def cmd_banned(message: types.Message, is_admin: bool):
    """List banned users"""
    if not is_admin:
        await message.answer("❌ This command is only available to admins.")
        return

    db = get_db_session()
    try:
        users = db.query(User).filter(User.status == UserStatus.BANNED).all()

        if not users:
            await message.answer("No banned users.")
            return

        text = "🚫 Banned Users:\n\n"
        for user in users:
            text += (
                f"ID: {user.telegram_id}\n"
                f"Name: {user.first_name or ''} {user.last_name or ''}\n"
                f"Username: @{user.username if user.username else 'N/A'}\n\n"
            )

        await message.answer(text)

    except Exception as e:
        logger.error(f"Error listing banned users: {e}")
        await message.answer(f"❌ Error: {str(e)}")
    finally:
        db.close()


async def cmd_remove(message: types.Message, is_admin: bool):
    """Remove a user completely from the database"""
    if not is_admin:
        await message.answer("❌ This command is only available to admins.")
        return

    args = message.get_args()
    if not args:
        await message.answer("Usage: /remove <user_id>")
        return

    try:
        user_id = int(args)
    except ValueError:
        await message.answer("❌ Invalid user ID. Must be a number.")
        return

    db = get_db_session()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()

        if not user:
            await message.answer(f"❌ User {user_id} not found.")
            return

        if user.is_admin:
            await message.answer("❌ Cannot remove an admin user.")
            return

        # Delete user
        db.delete(user)
        db.commit()

        # Log admin action
        action = AdminAction(
            admin_id=message.from_user.id,
            action_type="remove",
            target_user_id=user_id,
        )
        db.add(action)
        db.commit()

        await message.answer(f"✅ User {user_id} has been removed from the database.")

    except Exception as e:
        logger.error(f"Error removing user: {e}")
        await message.answer(f"❌ Error: {str(e)}")
    finally:
        db.close()


# Callback query handlers for inline buttons
async def handle_user_approval_callback(callback_query: types.CallbackQuery, is_admin: bool):
    """Handle inline button callbacks for user approval"""
    if not is_admin:
        await callback_query.answer("You don't have permission to do this.", show_alert=True)
        return

    data = callback_query.data
    action, user_id = data.split(":")
    user_id = int(user_id)

    db = get_db_session()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()

        if not user:
            await callback_query.answer("User not found.", show_alert=True)
            return

        if action == "approve_user":
            user.status = UserStatus.APPROVED
            result_text = "✅ User approved"
            notification = "🎉 Your access has been approved! Use /help to see available commands."

        elif action == "reject_user":
            user.status = UserStatus.REJECTED
            result_text = "❌ User rejected"
            notification = "❌ Your access request has been rejected."

        elif action == "ban_user":
            user.status = UserStatus.BANNED
            result_text = "🚫 User banned"
            notification = "🚫 You have been banned from using this bot."

        else:
            await callback_query.answer("Invalid action.", show_alert=True)
            return

        db.commit()

        # Log admin action
        admin_action = AdminAction(
            admin_id=callback_query.from_user.id,
            action_type=action.replace("_user", ""),
            target_user_id=user_id,
        )
        db.add(admin_action)
        db.commit()

        # Update the message
        await callback_query.message.edit_text(
            f"{callback_query.message.text}\n\n{result_text} by @{callback_query.from_user.username}"
        )

        await callback_query.answer(result_text)

        # Notify the user
        try:
            await callback_query.bot.send_message(user_id, notification)
        except Exception as e:
            logger.warning(f"Could not notify user {user_id}: {e}")

    except Exception as e:
        logger.error(f"Error handling callback: {e}")
        await callback_query.answer(f"Error: {str(e)}", show_alert=True)
    finally:
        db.close()


def register_admin_handlers(dp: Dispatcher):
    """Register admin command handlers"""
    dp.register_message_handler(cmd_approve, Command("approve"))
    dp.register_message_handler(cmd_reject, Command("reject"))
    dp.register_message_handler(cmd_ban, Command("ban"))
    dp.register_message_handler(cmd_users, Command("users"))
    dp.register_message_handler(cmd_pending, Command("pending"))
    dp.register_message_handler(cmd_banned, Command("banned"))
    dp.register_message_handler(cmd_remove, Command("remove"))
    dp.register_callback_query_handler(
        handle_user_approval_callback,
        lambda c: c.data and c.data.startswith(("approve_user:", "reject_user:", "ban_user:"))
    )

from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from sqlalchemy.orm import Session
import os
import logging

import sys
sys.path.append('/app/shared')

from models import User, UserStatus
from database import get_db_session

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseMiddleware):
    """Middleware to check user authorization status"""

    def __init__(self):
        super().__init__()
        self.admin_ids = self._load_admin_ids()
        self.auto_approve = os.getenv("AUTO_APPROVE", "false").lower() == "true"

    def _load_admin_ids(self) -> set:
        """Load admin IDs from environment"""
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        if admin_ids_str:
            return set(int(id.strip()) for id in admin_ids_str.split(",") if id.strip())
        return set()

    async def on_pre_process_message(self, message: types.Message, data: dict):
        """Process message before handling"""
        user = message.from_user
        db = get_db_session()

        try:
            # Check if user is admin
            if user.id in self.admin_ids:
                data["is_admin"] = True
                data["user_status"] = UserStatus.APPROVED
                # Ensure admin is in database
                self._ensure_admin_in_db(db, user)
                return

            # Get or create user
            db_user = db.query(User).filter(User.telegram_id == user.id).first()

            if not db_user:
                # New user - create pending entry
                db_user = User(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    status=UserStatus.APPROVED if self.auto_approve else UserStatus.PENDING,
                    is_admin=False,
                )
                db.add(db_user)
                db.commit()

                logger.info(f"New user registered: {user.id} ({user.username})")

                # If not auto-approved, notify user
                if not self.auto_approve:
                    await message.answer(
                        "👋 Welcome! Your account is pending approval.\n"
                        "An admin will review your request shortly.\n\n"
                        "You'll be notified once approved."
                    )
                    # Don't process further for pending users
                    data["is_admin"] = False
                    data["user_status"] = UserStatus.PENDING
                    data["new_user"] = True
                    return

            # Check user status
            if db_user.status == UserStatus.BANNED:
                await message.answer("🚫 You are banned from using this bot.")
                raise CancelHandler()

            if db_user.status == UserStatus.REJECTED:
                await message.answer("❌ Your access request was rejected.")
                raise CancelHandler()

            if db_user.status == UserStatus.PENDING:
                # Allow /start command for pending users
                if message.text and message.text.startswith("/start"):
                    data["is_admin"] = False
                    data["user_status"] = UserStatus.PENDING
                    return

                await message.answer(
                    "⏳ Your account is still pending approval.\n"
                    "Please wait for an admin to approve your access."
                )
                raise CancelHandler()

            # User is approved
            data["is_admin"] = db_user.is_admin
            data["user_status"] = db_user.status
            data["db_user"] = db_user

        except CancelHandler:
            raise
        except Exception as e:
            logger.error(f"Auth middleware error: {e}")
            await message.answer("An error occurred. Please try again later.")
            raise CancelHandler()
        finally:
            db.close()

    def _ensure_admin_in_db(self, db: Session, user: types.User):
        """Ensure admin user exists in database"""
        db_user = db.query(User).filter(User.telegram_id == user.id).first()
        if not db_user:
            db_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                status=UserStatus.APPROVED,
                is_admin=True,
            )
            db.add(db_user)
            db.commit()
        elif not db_user.is_admin:
            db_user.is_admin = True
            db_user.status = UserStatus.APPROVED
            db.commit()

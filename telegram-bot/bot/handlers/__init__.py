from .user import register_user_handlers
from .admin import register_admin_handlers
from .download import register_download_handlers

__all__ = ["register_user_handlers", "register_admin_handlers", "register_download_handlers"]

from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, Float, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class UserStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    BANNED = "banned"


class JobStatus(enum.Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    status = Column(Enum(UserStatus), default=UserStatus.PENDING, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # User preferences
    default_quality = Column(String, default="best")
    default_format = Column(String, default="video")


class DownloadJob(Base):
    __tablename__ = "download_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    url = Column(String, nullable=False)
    url_hash = Column(String, index=True)  # For cache detection

    # Download configuration
    format_type = Column(String, default="video")  # video, audio
    quality = Column(String, default="best")

    # Status tracking
    status = Column(Enum(JobStatus), default=JobStatus.QUEUED, nullable=False)
    progress = Column(Float, default=0.0)

    # File information
    file_name = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    file_size = Column(BigInteger, nullable=True)
    file_type = Column(String, nullable=True)

    # Upload information
    telegram_file_id = Column(String, nullable=True)
    external_link = Column(String, nullable=True)
    external_provider = Column(String, nullable=True)
    external_expiry = Column(DateTime, nullable=True)

    # Metadata
    title = Column(String, nullable=True)
    duration = Column(Integer, nullable=True)
    thumbnail_url = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # Error tracking
    error_message = Column(String, nullable=True)
    retry_count = Column(Integer, default=0)


class FileCache(Base):
    __tablename__ = "file_cache"

    id = Column(Integer, primary_key=True, index=True)
    url_hash = Column(String, unique=True, index=True, nullable=False)
    url = Column(String, nullable=False)
    format_type = Column(String, nullable=False)
    quality = Column(String, nullable=False)

    # File information
    file_path = Column(String, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    telegram_file_id = Column(String, nullable=True)

    # Metadata
    title = Column(String, nullable=True)
    duration = Column(Integer, nullable=True)

    # Cache management
    hit_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)


class AdminAction(Base):
    __tablename__ = "admin_actions"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(BigInteger, nullable=False)
    action_type = Column(String, nullable=False)  # approve, reject, ban, remove
    target_user_id = Column(BigInteger, nullable=False)
    reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

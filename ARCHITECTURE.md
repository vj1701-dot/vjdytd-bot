# Architecture Documentation

## System Overview

The Telegram Video/Audio Downloader Bot is a microservices-based system designed for downloading, processing, and delivering media files through Telegram.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                      (Telegram Client)                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Telegram Bot Service                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Handlers   │  │  Middleware  │  │   Utilities  │         │
│  │ (User/Admin/ │  │    (Auth)    │  │  (Uploader/  │         │
│  │  Download)   │  │              │  │   External)  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                   ┌─────────┼─────────┐
                   │         │         │
                   ▼         ▼         ▼
         ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
         │   Redis     │ │  Database   │ │   FastAPI   │
         │   (Queue/   │ │  (SQLite/   │ │   Service   │
         │   State)    │ │   Postgres) │ │             │
         └─────────────┘ └─────────────┘ └──────┬──────┘
                                                 │
                                    ┌────────────┼────────────┐
                                    │                         │
                                    ▼                         ▼
                          ┌─────────────────┐    ┌──────────────────┐
                          │  JDownloader    │    │   yt-dlp         │
                          │   (Primary)     │    │   (Fallback)     │
                          └─────────────────┘    └──────────────────┘
                                    │                         │
                                    └────────────┬────────────┘
                                                 │
                                                 ▼
                                    ┌──────────────────────┐
                                    │  Local File System   │
                                    │    (/downloads)      │
                                    └──────────────────────┘
                                                 │
                                    ┌────────────┼────────────┐
                                    │                         │
                                    ▼                         ▼
                          ┌─────────────────┐    ┌──────────────────┐
                          │   Telegram      │    │  External Upload │
                          │  (≤2GB files)   │    │  (>2GB - GoFile) │
                          └─────────────────┘    └──────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Cleanup Worker                              │
│              (48h TTL + Orphan File Management)                  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Telegram Bot Service

**Technology**: Python 3.11, aiogram 2.x

**Responsibilities**:
- User interaction and command processing
- Authorization and authentication
- Job creation and queue management
- Progress updates and notifications
- File upload coordination

**Subcomponents**:

#### Handlers
- `user.py` - User commands (/start, /help, /status, etc.)
- `admin.py` - Admin commands (/approve, /ban, /users, etc.)
- `download.py` - Download commands and URL processing

#### Middleware
- `auth.py` - Authorization middleware
  - User status verification
  - Admin privilege checking
  - New user registration
  - Banned user blocking

#### Utilities
- `uploader.py` - Telegram file upload management
- `external_upload.py` - External service integration (GoFile)

### 2. FastAPI Service

**Technology**: Python 3.11, FastAPI, uvicorn

**Responsibilities**:
- API wrapper for download operations
- JDownloader communication
- yt-dlp integration (fallback)
- Format extraction
- Progress monitoring

**Endpoints**:
- `POST /api/download` - Initiate download
- `POST /api/formats` - Get available formats
- `GET /api/status/{job_id}` - Get job status
- `GET /api/health` - Health check

### 3. JDownloader Service

**Technology**: Docker container (jlesage/jdownloader-2)

**Responsibilities**:
- Primary download engine
- Multi-source download support
- Download queue management
- Automatic captcha solving
- Resume support

**Integration**:
- Connected via My.JDownloader API
- Managed through myjdapi Python library
- Fallback to yt-dlp if unavailable

### 4. Redis Service

**Technology**: Redis 7 Alpine

**Responsibilities**:
- Job queue management
- State caching
- Progress tracking
- Rate limiting
- Active job tracking per user

**Data Structures**:
- Lists: Download queue
- Sets: User active jobs
- Strings: Job progress, state
- TTL: Automatic expiration

### 5. Database Service

**Technology**: SQLite (default) / PostgreSQL (optional)

**Schema**:

#### Users Table
- User registration and status
- Admin privileges
- Preferences
- Timestamps

#### DownloadJobs Table
- Job tracking
- Status and progress
- File metadata
- Error tracking
- Expiry management

#### FileCache Table
- Duplicate detection
- File reuse
- Hit counting
- Expiry management

#### AdminActions Table
- Admin action logging
- Audit trail

### 6. Cleanup Worker

**Technology**: Python 3.11, schedule library

**Responsibilities**:
- Expired file deletion (48h TTL)
- Cache cleanup
- Orphaned file removal
- Failed job cleanup
- Periodic maintenance

**Schedule**:
- Default: Every 60 minutes
- Configurable via `CLEANUP_INTERVAL_MINUTES`

## Data Flow

### Download Flow

```
1. User sends URL to bot
   ├─> Bot validates URL
   ├─> Check user authorization
   └─> Check rate limits

2. Create job in database
   ├─> Generate unique job_id
   ├─> Hash URL for cache lookup
   └─> Set expiry (48h from now)

3. Check cache
   ├─> If found: Reuse file, skip download
   └─> If not found: Proceed to download

4. Enqueue job
   ├─> Add to Redis queue
   ├─> Add to user's active jobs
   └─> Notify FastAPI service

5. FastAPI processes job
   ├─> Try JDownloader first
   │   ├─> Add links via My.JDownloader API
   │   └─> Monitor progress
   └─> If JDownloader fails:
       └─> Fallback to yt-dlp

6. Download execution
   ├─> Update job status: DOWNLOADING
   ├─> Track progress in Redis
   └─> Update database progress

7. Post-download processing
   ├─> Update job status: PROCESSING
   ├─> Get file metadata
   ├─> Check file size
   └─> Move to final location

8. File delivery
   ├─> Update job status: UPLOADING
   ├─> If size ≤ 2GB:
   │   ├─> Upload to Telegram
   │   └─> Store file_id for caching
   └─> If size > 2GB:
       ├─> Upload to GoFile
       └─> Send download link

9. Completion
   ├─> Update job status: COMPLETED
   ├─> Remove from user's active jobs
   ├─> Add to cache (if applicable)
   └─> Notify user

10. Cleanup (after 48h)
    ├─> Worker detects expired job
    ├─> Delete files from disk
    ├─> Update database
    └─> Remove cache entry
```

### Authorization Flow

```
1. New user sends /start
   ├─> Middleware intercepts
   └─> User not in database

2. Create pending user
   ├─> Status: PENDING
   ├─> Store user info
   └─> Notify admins

3. Admin receives notification
   ├─> User details shown
   └─> Inline buttons presented
       ├─> Approve
       ├─> Reject
       └─> Ban

4. Admin action
   ├─> Update user status
   ├─> Log admin action
   └─> Notify user

5. Subsequent requests
   ├─> Middleware checks status
   ├─> If APPROVED: Allow
   ├─> If PENDING: Block with message
   ├─> If REJECTED: Block
   └─> If BANNED: Block permanently
```

## Security Architecture

### Authentication & Authorization

1. **User Authentication**
   - Telegram's built-in authentication
   - User ID verification
   - No additional login required

2. **Authorization Levels**
   - Admin (hardcoded in ADMIN_IDS)
   - Approved User
   - Pending User
   - Rejected User
   - Banned User

3. **Middleware Protection**
   - All requests pass through AuthMiddleware
   - Status checked before command execution
   - Banned users immediately rejected

### Data Security

1. **Environment Variables**
   - Sensitive data in .env (gitignored)
   - Docker secrets for production
   - No hardcoded credentials

2. **Database**
   - Local SQLite by default
   - Optional PostgreSQL for production
   - Regular backups recommended

3. **File Access**
   - Downloads in isolated volume
   - No external access by default
   - Automatic cleanup

### Rate Limiting

1. **Per-User Limits**
   - Max concurrent downloads: 2 (default)
   - Tracked via Redis
   - Configurable

2. **Global Limits**
   - System-wide rate limit
   - Prevents resource exhaustion

## Scalability Considerations

### Horizontal Scaling

**Current Limitations**:
- SQLite doesn't support concurrent writes
- Single bot instance recommended

**Scalability Options**:

1. **Database**
   - Switch to PostgreSQL
   - Enables multiple bot instances
   - Shared state across instances

2. **Bot Instances**
   ```bash
   docker-compose up -d --scale telegram-bot=3
   ```

3. **FastAPI Workers**
   ```yaml
   command: uvicorn main:app --workers 4
   ```

4. **Redis Clustering**
   - Redis Sentinel for HA
   - Redis Cluster for sharding

### Vertical Scaling

**Resource Requirements by Load**:

| Users/Day | RAM  | CPU  | Storage |
|-----------|------|------|---------|
| < 100     | 2GB  | 2    | 50GB    |
| 100-500   | 4GB  | 4    | 100GB   |
| 500-1000  | 8GB  | 8    | 250GB   |
| > 1000    | 16GB | 16   | 500GB+  |

## Monitoring & Observability

### Logging

**Log Locations**:
- Telegram Bot: `/logs/bot.log`
- FastAPI: `/logs/fastapi.log`
- Cleanup Worker: `/logs/cleanup.log`

**Log Levels**:
- INFO: Normal operations
- WARNING: Recoverable errors
- ERROR: Failures requiring attention

### Health Checks

1. **FastAPI Health Endpoint**
   ```bash
   curl http://localhost:8000/api/health
   ```

2. **Redis Status**
   ```bash
   docker-compose exec redis redis-cli ping
   ```

3. **JDownloader Status**
   - Check via FastAPI health endpoint
   - Or My.JDownloader web interface

### Metrics

**Key Performance Indicators**:
- Downloads per hour
- Average download time
- Success/failure rate
- Cache hit rate
- Disk usage
- Active users

## Disaster Recovery

### Backup Strategy

**What to Backup**:
1. Database (`bot_data.db`)
2. Environment configuration (`.env`)
3. User data (optional)

**Backup Script**:
```bash
#!/bin/bash
docker-compose exec -T telegram-bot cat /app/data/bot_data.db > backup_$(date +%Y%m%d).db
```

### Recovery Procedure

1. **Install Docker and Docker Compose**
2. **Restore files**
   ```bash
   cp backup.db data/bot_data.db
   cp .env.backup .env
   ```
3. **Start services**
   ```bash
   docker-compose up -d
   ```

## Performance Optimization

### Caching Strategy

1. **File Cache**
   - Hash: URL + format + quality
   - Reuse identical downloads
   - Significant bandwidth savings

2. **Telegram File IDs**
   - Store file_id for uploaded files
   - Instant resend without re-upload
   - Telegram server-side storage

### Download Optimization

1. **JDownloader Advantages**
   - Multi-connection downloads
   - Automatic retry
   - Resume support
   - Plugin ecosystem

2. **yt-dlp Fallback**
   - Faster for YouTube
   - Better format selection
   - No external dependency

## Future Enhancements

### Planned Features

1. **User Dashboard**
   - Web interface for history
   - Download statistics
   - Settings management

2. **Advanced Queue Management**
   - Priority queue
   - Scheduled downloads
   - Playlist support

3. **Enhanced Monitoring**
   - Grafana dashboards
   - Prometheus metrics
   - Alert system

4. **Multi-tenancy**
   - Support for multiple bot instances
   - Shared infrastructure
   - Isolated user data

### Scalability Roadmap

1. **Phase 1**: Current architecture (< 1000 users)
2. **Phase 2**: PostgreSQL + Multiple instances (< 5000 users)
3. **Phase 3**: Message queue (RabbitMQ/Kafka) + Worker pools
4. **Phase 4**: Kubernetes deployment + Auto-scaling

## Technology Stack Summary

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Bot Framework | aiogram | 2.25.1 | Telegram interaction |
| API Framework | FastAPI | 0.109.0 | REST API |
| Download Engine | JDownloader | Latest | Primary downloader |
| Fallback Downloader | yt-dlp | 2024.3+ | Backup downloader |
| Queue | Redis | 7 | Job queue & cache |
| Database | SQLite/PostgreSQL | - | Data persistence |
| Container | Docker | Latest | Containerization |
| Orchestration | Docker Compose | Latest | Service management |
| Language | Python | 3.11 | Core language |
| HTTP Client | httpx | 0.25.2 | Async HTTP |
| ORM | SQLAlchemy | 2.0.23 | Database ORM |

## Conclusion

This architecture provides a robust, scalable foundation for a Telegram download bot with:
- ✅ Modular design
- ✅ Easy deployment
- ✅ Horizontal scalability potential
- ✅ Fault tolerance
- ✅ Security by default
- ✅ Comprehensive monitoring
- ✅ Automatic maintenance

🎯 Goal

Create a Telegram bot that accepts a YouTube URL from an authorized user, downloads video/audio using JDownloader as backend, and delivers it via Telegram or fallback methods.

The downloader must be independent and reusable, not tightly coupled to the Telegram bot.

⸻

🔐 Access Control (MANDATORY)

User Approval System
	•	New users cannot use the bot immediately
	•	When a user starts:
	•	Add to pending list
	•	Notify admin with:
	•	Name
	•	Username
	•	User ID
	•	Include inline buttons:
	•	✅ Approve
	•	❌ Reject
	•	🚫 Ban

Rules
	•	Only approved users can use bot
	•	Rejected users blocked
	•	Banned users permanently blocked
	•	Persist:
	•	approved users
	•	pending users
	•	banned users

Admin Features
	•	Multiple admins supported
	•	Admins bypass all restrictions
	•	Config option: auto-approve (default OFF)

Admin Commands
	•	/approve <user_id>
	•	/reject <user_id>
	•	/ban <user_id>
	•	/users
	•	/pending
	•	/banned
	•	/remove <user_id>

⸻

🧩 Architecture (MANDATORY)

Use Docker Compose with modular services:
	•	telegram-bot → orchestration layer
	•	jdownloader → download engine
	•	fastapi-service → API wrapper for downloader
	•	redis → queue + state
	•	local-telegram-bot-api OR mtproto-uploader
	•	shared downloads volume
	•	optional worker (cleanup / uploads)

Downloader must be usable independently:
	•	via API
	•	via CLI
	•	via watch folder

⸻

📦 File Handling Rules

Size Constraints
	•	Files: 50MB – 2GB

Upload Strategy
	•	Use:
	•	self-hosted Telegram Bot API server OR
	•	MTProto uploader

Delivery Logic

IF file ≤ 2GB:
→ Upload to Telegram

IF file > 2GB:
→ Upload to external service:

	•	GoFile
	
→ Send link to user

Fallbacks

If upload fails:
	1.	send as document
	2.	split file
	3.	send direct server link

⸻

🗂️ Storage & Retention
	•	Store all downloads locally
	•	Auto-delete after 48 hours

Implementation
	•	Track:
	•	file path
	•	job ID
	•	timestamp
	•	expiry
	•	Use background worker / cron

Rules
	•	Delete ONLY server files
	•	Telegram copy remains intact

⸻

🔁 Download Flow
	1.	User sends URL
	2.	Check approval
	3.	If not approved → “awaiting approval”
	4.	Create job
	5.	Submit to JDownloader
	6.	Track progress
	7.	Process file
	8.	Deliver:
	•	Telegram OR
	•	external link
	9.	Store metadata
	10.	Cleanup after 48h

⸻

⚙️ Commands

User Commands
	•	/start
	•	/help
	•	/download <url>
	•	/audio <url>
	•	/video <url>
	•	/formats <url>
	•	/quality
	•	/status
	•	/queue
	•	/cancel <job_id>
	•	/retry <job_id>
	•	/list
	•	/link <job_id>

Admin Commands
	•	/approve
	•	/reject
	•	/ban
	•	/users
	•	/pending
	•	/banned
	•	/remove

⸻

⚡ Core Features
	•	Authorization middleware
	•	Job queue (Redis)
	•	Progress updates
	•	Retry system
	•	Rate limiting (per user)
	•	Logging + metrics
	•	Health checks
	•	Config via environment variables
	•	Separate temp and final folders

⸻

🧠 SMART ADDITIONS (HIGHLY RECOMMENDED)

1. File Cache System
	•	Detect duplicate URLs
	•	If already downloaded:
	•	reuse existing file
	•	skip re-download
	•	Cache by:
	•	URL hash
	•	format/quality

⸻

2. Link Expiry Tracker
	•	Track external upload expiry
	•	Store:
	•	provider
	•	expiry time
	•	Notify user:
	•	when link is generated
	•	optionally before expiry

⸻

3. Hybrid Upload Strategy
	•	Attempt Telegram upload first
	•	If fails automatically:
	•	fallback to external upload
	•	No manual intervention required

⸻

4. Admin Dashboard (Lightweight)
	•	View:
	•	active jobs
	•	completed jobs
	•	failed jobs
	•	Manage:
	•	users
	•	queue
	•	logs
	•	Can be:
	•	simple FastAPI UI
	•	or minimal web page

⸻

5. Download Profiles

Allow user presets:
	•	audio-only
	•	720p
	•	best quality

Store per-user preferences

⸻

6. Duplicate Detection
	•	Prevent duplicate downloads in queue
	•	Merge jobs if same URL already processing

⸻

7. Watch Folder Support
	•	Drop file with URLs
	•	Auto-trigger download

⸻

8. Post-processing (Optional)
	•	ffmpeg integration:
	•	extract audio
	•	convert formats
	•	compress large files
	•	split files

⸻

9. File Organization
	•	Store downloads by:
	•	user
	•	date
	•	type (audio/video)

⸻

10. Expiring Download Links (Server-hosted)
	•	Generate temporary HTTP links
	•	Expire after X hours

⸻

🔌 JDownloader Integration
	•	Use JDownloader as primary engine
	•	Interact via API or automation
	•	Bot must NOT directly download unless fallback needed

⸻

🧱 Tech Stack
	•	Python
	•	aiogram / pyrogram / telethon
	•	FastAPI (internal API)
	•	Redis (queue/state)
	•	Docker Compose
	•	Shared volumes
	•	ffmpeg

⸻

📦 Deliverables

Provide:
	1.	Architecture diagram
	2.	Explanation of Telegram file limits
	3.	Folder structure
	4.	Docker Compose file
	5.	.env config
	6.	Telegram bot code
	7.	Downloader API service
	8.	JDownloader integration layer
	9.	Upload handling system
	10.	External uploader module
	11.	Cleanup worker (48h TTL)
	12.	DB schema (users + jobs + cache)
	13.	Deployment steps
	14.	Security best practices
	15.	Future improvements

⸻

🎯 Design Principles
	•	Modular
	•	Self-hostable
	•	Reliable
	•	Minimal but extensible
	•	Clean separation of concerns

⸻

🚫 Scope Control

Do NOT include (unless optional and disabled):
	•	torrents
	•	Google Drive
	•	rclone

⸻

✅ Preferred Architecture
	•	JDownloader (independent service)
	•	FastAPI wrapper
	•	Telegram bot (controller)
	•	Local Bot API server
	•	Redis queue
	•	Cleanup worker
	•	Optional MTProto uploader

⸻

🔄 Final Behavior Summary

User → Bot → Queue → JDownloader → File →
→ Telegram (≤2GB)
→ External link (>2GB)
→ Auto cleanup after 48h
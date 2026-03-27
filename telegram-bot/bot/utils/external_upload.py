import httpx
import os
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


async def upload_to_external_service(file_path: str, file_size: int) -> dict:
    """
    Upload file to external service (GoFile)

    Returns:
        dict with keys: success, link, provider, expiry_date, error
    """

    # Try GoFile first
    try:
        result = await upload_to_gofile(file_path, file_size)
        if result["success"]:
            return result
    except Exception as e:
        logger.error(f"GoFile upload failed: {e}")

    return {
        "success": False,
        "error": "All upload services failed"
    }


async def upload_to_gofile(file_path: str, file_size: int) -> dict:
    """Upload file to GoFile.io"""

    logger.info(f"Uploading to GoFile: {file_path} ({file_size} bytes)")

    try:
        # Step 1: Get the best server
        async with httpx.AsyncClient(timeout=30.0) as client:
            server_response = await client.get("https://api.gofile.io/getServer")

            if server_response.status_code != 200:
                raise Exception(f"Failed to get GoFile server: {server_response.status_code}")

            server_data = server_response.json()
            if server_data["status"] != "ok":
                raise Exception("GoFile server request failed")

            server = server_data["data"]["server"]
            logger.info(f"Using GoFile server: {server}")

            # Step 2: Upload the file
            upload_url = f"https://{server}.gofile.io/uploadFile"

            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f)}

                # Add API token if available
                data = {}
                gofile_token = os.getenv("GOFILE_API_TOKEN")
                if gofile_token:
                    data['token'] = gofile_token

                upload_response = await client.post(
                    upload_url,
                    files=files,
                    data=data,
                    timeout=600.0  # 10 minutes for large files
                )

            if upload_response.status_code != 200:
                raise Exception(f"Upload failed: {upload_response.status_code}")

            upload_data = upload_response.json()

            if upload_data["status"] != "ok":
                raise Exception(f"Upload failed: {upload_data.get('status')}")

            download_page = upload_data["data"]["downloadPage"]
            file_id = upload_data["data"]["fileId"]

            logger.info(f"GoFile upload successful: {download_page}")

            # GoFile links typically don't expire, but we'll set a conservative estimate
            # Free uploads may be deleted after inactivity
            expiry = datetime.utcnow() + timedelta(days=30)

            return {
                "success": True,
                "link": download_page,
                "provider": "GoFile",
                "file_id": file_id,
                "expiry_date": expiry.strftime("%Y-%m-%d"),
                "note": "Free uploads may be deleted after prolonged inactivity"
            }

    except Exception as e:
        logger.error(f"GoFile upload error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def upload_to_anonfiles(file_path: str, file_size: int) -> dict:
    """
    Upload file to AnonFiles (BACKUP - may not be available)
    """

    logger.info(f"Uploading to AnonFiles: {file_path}")

    try:
        async with httpx.AsyncClient(timeout=600.0) as client:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f)}

                response = await client.post(
                    "https://api.anonfiles.com/upload",
                    files=files
                )

            if response.status_code != 200:
                raise Exception(f"Upload failed: {response.status_code}")

            data = response.json()

            if not data.get("status"):
                raise Exception("Upload failed")

            download_url = data["data"]["file"]["url"]["full"]

            logger.info(f"AnonFiles upload successful: {download_url}")

            return {
                "success": True,
                "link": download_url,
                "provider": "AnonFiles",
                "expiry_date": None,  # AnonFiles doesn't specify expiry
            }

    except Exception as e:
        logger.error(f"AnonFiles upload error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def upload_to_file_io(file_path: str, file_size: int) -> dict:
    """
    Upload file to File.io (1 download expiry - not ideal but works as emergency fallback)
    """

    logger.info(f"Uploading to File.io: {file_path}")

    try:
        async with httpx.AsyncClient(timeout=600.0) as client:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f)}

                response = await client.post(
                    "https://file.io",
                    files=files,
                    data={'expires': '1w'}  # 1 week expiry
                )

            if response.status_code != 200:
                raise Exception(f"Upload failed: {response.status_code}")

            data = response.json()

            if not data.get("success"):
                raise Exception("Upload failed")

            download_url = data["link"]
            expiry = datetime.utcnow() + timedelta(weeks=1)

            logger.info(f"File.io upload successful: {download_url}")

            return {
                "success": True,
                "link": download_url,
                "provider": "File.io",
                "expiry_date": expiry.strftime("%Y-%m-%d"),
                "note": "⚠️ Link expires after first download or 1 week!"
            }

    except Exception as e:
        logger.error(f"File.io upload error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

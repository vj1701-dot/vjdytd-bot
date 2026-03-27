import os
import logging
import time
from typing import Optional, List, Dict, Any
from myjdapi import Myjdapi

logger = logging.getLogger(__name__)


class JDownloaderService:
    """JDownloader API service wrapper"""

    def __init__(self):
        self.email = os.getenv("JDOWNLOADER_EMAIL")
        self.password = os.getenv("JDOWNLOADER_PASSWORD")
        self.device_name = os.getenv("JDOWNLOADER_DEVICE_NAME", "TelegramBot")

        self.jd = Myjdapi()
        self.device = None
        self._connected = False

    def connect(self) -> bool:
        """Connect to JDownloader"""
        try:
            if not self.email or not self.password:
                logger.error("JDownloader credentials not configured")
                return False

            # Connect to My.JDownloader
            self.jd.connect(self.email, self.password)
            logger.info("Connected to My.JDownloader")

            # Get device
            self.jd.update_devices()
            devices = self.jd.list_devices()

            if not devices:
                logger.error("No JDownloader devices found")
                return False

            # Find our device or use the first one
            self.device = devices[0]
            for dev in devices:
                if dev.get('name') == self.device_name:
                    self.device = dev
                    break

            logger.info(f"Using JDownloader device: {self.device.get('name')}")
            self._connected = True
            return True

        except Exception as e:
            logger.error(f"Failed to connect to JDownloader: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if connected"""
        return self._connected

    def add_links(self, links: List[str], download_path: str = None) -> Dict[str, Any]:
        """Add download links to JDownloader"""
        try:
            if not self.is_connected():
                if not self.connect():
                    return {"success": False, "error": "Not connected to JDownloader"}

            # Prepare download parameters
            params = {
                "links": ",".join(links) if isinstance(links, list) else links,
                "packageName": f"telegram_download_{int(time.time())}",
                "autostart": True,
                "autoExtract": False,
            }

            if download_path:
                params["destinationFolder"] = download_path

            # Add links via linkgrabber
            result = self.jd.linkgrabber.add_links(params)

            logger.info(f"Added links to JDownloader: {result}")

            return {
                "success": True,
                "result": result
            }

        except Exception as e:
            logger.error(f"Failed to add links: {e}")
            return {"success": False, "error": str(e)}

    def get_download_status(self, package_name: str = None) -> Dict[str, Any]:
        """Get download status"""
        try:
            if not self.is_connected():
                return {"success": False, "error": "Not connected"}

            # Get downloads list
            downloads = self.jd.downloads.query_links()

            if package_name:
                # Filter by package name
                filtered = [d for d in downloads if d.get('packageName') == package_name]
                return {"success": True, "downloads": filtered}

            return {"success": True, "downloads": downloads}

        except Exception as e:
            logger.error(f"Failed to get download status: {e}")
            return {"success": False, "error": str(e)}

    def get_linkgrabber_status(self) -> Dict[str, Any]:
        """Get linkgrabber status"""
        try:
            if not self.is_connected():
                return {"success": False, "error": "Not connected"}

            links = self.jd.linkgrabber.query_links()

            return {"success": True, "links": links}

        except Exception as e:
            logger.error(f"Failed to get linkgrabber status: {e}")
            return {"success": False, "error": str(e)}

    def move_to_downloads(self, link_ids: List[int] = None) -> Dict[str, Any]:
        """Move links from linkgrabber to downloads"""
        try:
            if not self.is_connected():
                return {"success": False, "error": "Not connected"}

            if link_ids:
                result = self.jd.linkgrabber.move_to_downloadlist(link_ids)
            else:
                # Move all links
                result = self.jd.linkgrabber.move_to_downloadlist()

            return {"success": True, "result": result}

        except Exception as e:
            logger.error(f"Failed to move to downloads: {e}")
            return {"success": False, "error": str(e)}

    def cleanup_packages(self, package_ids: List[int]) -> Dict[str, Any]:
        """Remove completed packages"""
        try:
            if not self.is_connected():
                return {"success": False, "error": "Not connected"}

            result = self.jd.downloads.cleanup(
                "DELETE_FINISHED",
                "REMOVE_LINKS_AND_DELETE_FILES",
                "SELECTED",
                package_ids
            )

            return {"success": True, "result": result}

        except Exception as e:
            logger.error(f"Failed to cleanup packages: {e}")
            return {"success": False, "error": str(e)}

    def start_downloads(self) -> Dict[str, Any]:
        """Start all downloads"""
        try:
            if not self.is_connected():
                return {"success": False, "error": "Not connected"}

            self.jd.downloadcontroller.start_downloads()

            return {"success": True}

        except Exception as e:
            logger.error(f"Failed to start downloads: {e}")
            return {"success": False, "error": str(e)}

    def stop_downloads(self) -> Dict[str, Any]:
        """Stop all downloads"""
        try:
            if not self.is_connected():
                return {"success": False, "error": "Not connected"}

            self.jd.downloadcontroller.stop_downloads()

            return {"success": True}

        except Exception as e:
            logger.error(f"Failed to stop downloads: {e}")
            return {"success": False, "error": str(e)}

    def pause_downloads(self, pause: bool = True) -> Dict[str, Any]:
        """Pause/unpause downloads"""
        try:
            if not self.is_connected():
                return {"success": False, "error": "Not connected"}

            self.jd.downloadcontroller.pause_downloads(pause)

            return {"success": True, "paused": pause}

        except Exception as e:
            logger.error(f"Failed to pause downloads: {e}")
            return {"success": False, "error": str(e)}


# Global instance
jdownloader_service = JDownloaderService()

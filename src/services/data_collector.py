"""Data archival service for packaging and sending feedback and transcripts."""

import tarfile
import tempfile
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import List

import requests

from configuration import configuration
from log import get_logger

logger = get_logger(__name__)


class DataCollectorService:
    """Service for collecting and sending user data to ingress server."""

    def run(self) -> None:
        """Run the periodic data collection loop."""
        collector_config = configuration.user_data_collection_configuration.data_collector
        
        logger.info("Starting data collection service")
        
        while True:
            try:
                self._perform_collection()
                logger.info(f"Next collection scheduled in {collector_config.collection_interval} seconds")
                time.sleep(collector_config.collection_interval)
            except KeyboardInterrupt:
                logger.info("Data collection service stopped by user")
                break
            except Exception as e:
                logger.error(f"Error during collection process: {e}", exc_info=True)
                time.sleep(300)  # Wait 5 minutes before retrying on error

    def _perform_collection(self) -> None:
        """Perform a single collection operation."""
        logger.info("Starting data collection process")

        # Collect files to archive
        feedback_files = self._collect_feedback_files()
        transcript_files = self._collect_transcript_files()

        if not feedback_files and not transcript_files:
            logger.info("No files to collect")
            return

        logger.info(f"Found {len(feedback_files)} feedback files and {len(transcript_files)} transcript files to collect")

        # Create and send archives
        collections_sent = 0
        try:
            if feedback_files:
                collections_sent += self._create_and_send_tarball(feedback_files, "feedback")
            if transcript_files:
                collections_sent += self._create_and_send_tarball(transcript_files, "transcripts")

            logger.info(f"Successfully sent {collections_sent} collections to ingress server")
        except Exception as e:
            logger.error(f"Failed to create or send collections: {e}", exc_info=True)
            raise

    def _collect_feedback_files(self) -> List[Path]:
        """Collect all feedback files that need to be collected."""
        udc_config = configuration.user_data_collection_configuration

        if udc_config.feedback_disabled or not udc_config.feedback_storage:
            return []

        feedback_dir = Path(udc_config.feedback_storage)
        if not feedback_dir.exists():
            return []

        return list(feedback_dir.glob("*.json"))

    def _collect_transcript_files(self) -> List[Path]:
        """Collect all transcript files that need to be collected."""
        udc_config = configuration.user_data_collection_configuration

        if udc_config.transcripts_disabled or not udc_config.transcripts_storage:
            return []

        transcripts_dir = Path(udc_config.transcripts_storage)
        if not transcripts_dir.exists():
            return []

        # Recursively find all JSON files in the transcript directory structure
        return list(transcripts_dir.rglob("*.json"))

    def _create_and_send_tarball(self, files: List[Path], data_type: str) -> int:
        """Create a single tarball from all files and send to ingress server."""
        if not files:
            return 0

        collector_config = configuration.user_data_collection_configuration.data_collector

        # Create one tarball with all files
        tarball_path = self._create_tarball(files, data_type)
        try:
            self._send_tarball(tarball_path)
            if collector_config.cleanup_after_send:
                self._cleanup_files(files)
                self._cleanup_empty_directories()
            return 1
        finally:
            self._cleanup_tarball(tarball_path)

    def _create_tarball(self, files: List[Path], data_type: str) -> Path:
        """Create a tarball containing the specified files."""
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        tarball_name = f"{data_type}_{timestamp}.tar.gz"

        # Create tarball in a temporary directory
        temp_dir = Path(tempfile.gettempdir())
        tarball_path = temp_dir / tarball_name

        logger.info(f"Creating tarball {tarball_path} with {len(files)} files")

        with tarfile.open(tarball_path, "w:gz") as tar:
            for file_path in files:
                try:
                    # Add file with relative path to maintain directory structure
                    arcname = str(file_path.relative_to(file_path.parents[-2]))
                    tar.add(file_path, arcname=arcname)
                except Exception as e:
                    logger.warning(f"Failed to add {file_path} to tarball: {e}")
        
        logger.info(f"Created tarball {tarball_path} ({tarball_path.stat().st_size} bytes)")
        return tarball_path

    def _send_tarball(self, tarball_path: Path) -> None:
        """Send the tarball to the ingress server."""
        collector_config = configuration.user_data_collection_configuration.data_collector

        headers = {
            "Content-Type": "application/vnd.redhat.lightspeed-stack.periodic+tar",
        }

        if collector_config.ingress_server_auth_token:
            headers["Authorization"] = f"Bearer {collector_config.ingress_server_auth_token}"

        with open(tarball_path, "rb") as f:
            data = f.read()

        logger.info(f"Sending tarball {tarball_path.name} to {collector_config.ingress_server_url}")

        response = requests.post(
            collector_config.ingress_server_url,
            data=data,
            headers=headers,
            timeout=collector_config.connection_timeout_seconds,
        )

        if response.status_code >= 400:
            raise Exception(
                f"Failed to send tarball to ingress server. "
                f"Status: {response.status_code}, Response: {response.text}"
            )

        logger.info(f"Successfully sent tarball {tarball_path.name} to ingress server")

    def _cleanup_files(self, files: List[Path]) -> None:
        """Remove files after successful transmission."""
        for file_path in files:
            try:
                file_path.unlink()
                logger.debug(f"Removed file {file_path}")
            except OSError as e:
                logger.warning(f"Failed to remove file {file_path}: {e}")

    def _cleanup_empty_directories(self) -> None:
        """Remove empty directories from transcript storage."""
        udc_config = configuration.user_data_collection_configuration

        if udc_config.transcripts_disabled or not udc_config.transcripts_storage:
            return

        transcripts_dir = Path(udc_config.transcripts_storage)
        if not transcripts_dir.exists():
            return

        # Remove empty directories (conversation and user directories)
        for user_dir in transcripts_dir.iterdir():
            if user_dir.is_dir():
                for conv_dir in user_dir.iterdir():
                    if conv_dir.is_dir() and not any(conv_dir.iterdir()):
                        try:
                            conv_dir.rmdir()
                            logger.debug(f"Removed empty directory {conv_dir}")
                        except OSError:
                            pass

                # Remove user directory if empty
                if not any(user_dir.iterdir()):
                    try:
                        user_dir.rmdir()
                        logger.debug(f"Removed empty directory {user_dir}")
                    except OSError:
                        pass

    def _cleanup_tarball(self, tarball_path: Path) -> None:
        """Remove the temporary tarball file."""
        try:
            tarball_path.unlink()
            logger.debug(f"Removed temporary tarball {tarball_path}")
        except OSError as e:
            logger.warning(f"Failed to remove temporary tarball {tarball_path}: {e}")

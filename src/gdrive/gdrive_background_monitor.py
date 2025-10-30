"""
Async Background Monitor for Google Drive RAG Pipeline
Wraps the synchronous pipeline in an async background task for FastAPI
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)


class BackgroundGDriveMonitor:
    """Async background task for Google Drive monitoring"""

    def __init__(self, pipeline, interval_seconds: int = 60):
        """
        Initialize background monitor

        Args:
            pipeline: GoogleDriveRAGPipeline instance
            interval_seconds: Polling interval (default: 60s)
        """
        self.pipeline = pipeline
        self.interval = interval_seconds
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.last_check_time: Optional[str] = None
        self.processed_count = 0
        self.error_count = 0
        self.pending_files: List[Dict] = []
        self._lock = asyncio.Lock()

    async def start(self):
        """Start monitoring loop"""
        if self.is_running:
            logger.warning("Monitor already running")
            return

        logger.info("Starting Google Drive background monitor")
        self.is_running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info(f"Monitor started with {self.interval}s interval")

    async def stop(self):
        """Stop monitoring loop"""
        if not self.is_running:
            logger.warning("Monitor not running")
            return

        logger.info("Stopping Google Drive background monitor")
        self.is_running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Monitor stopped")

    async def _monitor_loop(self):
        """Main monitoring loop (runs in background)"""
        logger.info("Monitor loop started")

        while self.is_running:
            try:
                self.last_check_time = datetime.now().isoformat()
                logger.info(f"Checking Google Drive for new files at {self.last_check_time}")

                # Run in thread pool to avoid blocking async loop
                result = await asyncio.to_thread(self._check_and_process_files)

                if result:
                    self.processed_count += result.get('processed', 0)
                    self.error_count += result.get('errors', 0)
                    self.pending_files = result.get('pending', [])

                    if result.get('processed', 0) > 0:
                        logger.info(f"Processed {result['processed']} new file(s)")

            except asyncio.CancelledError:
                logger.info("Monitor loop cancelled")
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}", exc_info=True)
                self.error_count += 1

            # Wait before next check
            try:
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                logger.info("Monitor sleep cancelled")
                break

        logger.info("Monitor loop ended")

    def _check_and_process_files(self) -> Dict:
        """
        Check for new files and process them (runs in thread pool)

        Returns:
            Dict with processing results
        """
        try:
            # Get folder ID from config
            folder_id = self.pipeline.config['google_drive'].get('folder_id')
            if not folder_id:
                logger.error("Folder ID not configured")
                return {'processed': 0, 'errors': 1, 'pending': []}

            # Get pending files (not yet processed)
            pending = self.pipeline.gdrive_monitor.list_documents_in_folder(
                folder_id,
                include_all=False  # Only unprocessed files
            )

            if not pending:
                logger.debug("No new files to process")
                return {'processed': 0, 'errors': 0, 'pending': []}

            logger.info(f"Found {len(pending)} pending file(s)")

            processed = 0
            errors = 0

            for file_meta in pending:
                try:
                    logger.info(f"Processing: {file_meta['name']}")

                    # Download file
                    file_content = self.pipeline.gdrive_monitor.download_file(
                        file_meta['id'],
                        file_meta['name']
                    )

                    if not file_content:
                        logger.error(f"Failed to download: {file_meta['name']}")
                        errors += 1
                        continue

                    # Process document
                    success = self.pipeline.process_document(file_meta, file_content)

                    if success:
                        # Mark as processed
                        self.pipeline.gdrive_monitor.mark_as_processed(file_meta['id'])
                        processed += 1
                        logger.info(f"Successfully processed: {file_meta['name']}")
                    else:
                        logger.error(f"Failed to process: {file_meta['name']}")
                        errors += 1

                except Exception as e:
                    logger.error(f"Error processing {file_meta['name']}: {e}", exc_info=True)
                    errors += 1

            return {
                'processed': processed,
                'errors': errors,
                'pending': pending
            }

        except Exception as e:
            logger.error(f"Error checking files: {e}", exc_info=True)
            return {'processed': 0, 'errors': 1, 'pending': []}

    async def trigger_processing(self) -> Dict:
        """
        Manually trigger processing (bypasses interval timer)

        Returns:
            Dict with processing results
        """
        async with self._lock:
            logger.info("Manual processing triggered")
            result = await asyncio.to_thread(self._check_and_process_files)
            
            if result:
                self.processed_count += result.get('processed', 0)
                self.error_count += result.get('errors', 0)
                self.pending_files = result.get('pending', [])

            return result

    def get_pending_count(self) -> int:
        """Get count of pending files"""
        return len(self.pending_files)

    def get_processed_count(self) -> int:
        """Get total processed count since start"""
        return self.processed_count

    def get_pending_files(self) -> List[Dict]:
        """Get list of pending files"""
        return [
            {
                'name': f['name'],
                'id': f['id'],
                'size': f.get('size', 'unknown'),
                'modified': f.get('modifiedTime', 'unknown')
            }
            for f in self.pending_files
        ]

    def get_status(self) -> Dict:
        """Get monitor status"""
        return {
            'running': self.is_running,
            'interval_seconds': self.interval,
            'last_check': self.last_check_time,
            'pending_files': self.get_pending_count(),
            'processed_total': self.processed_count,
            'errors_total': self.error_count
        }


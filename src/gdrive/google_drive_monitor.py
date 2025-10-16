"""
Google Drive Monitor for RAG Pipeline
Monitors a Google Drive folder for new documents and processes them automatically
"""

import os
import json
import time
import pickle
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Set
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io


class GoogleDriveMonitor:
    """Monitor Google Drive folder for new documents"""

    # Google Drive API scopes
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

    # Supported MIME types
    SUPPORTED_MIME_TYPES = {
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
        'application/pdf': '.pdf',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
        'application/vnd.ms-excel': '.xls',
        'application/msword': '.doc',
    }

    def __init__(self, credentials_file: str = 'config/credentials.json',
                 token_file: str = 'config/token.pickle',
                 state_file: str = 'config/gdrive_state.json'):
        """
        Initialize Google Drive monitor

        Args:
            credentials_file: Path to Google OAuth credentials JSON
            token_file: Path to store authentication token
            state_file: Path to store processed files state
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.state_file = state_file
        self.service = None
        self.processed_files: Set[str] = set()

        # Load state
        self._load_state()

    def authenticate(self) -> bool:
        """
        Authenticate with Google Drive API

        Returns:
            True if authentication successful
        """
        creds = None

        # Load existing token
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)

        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Refreshing expired credentials...")
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    print(f"[ERROR] Credentials file not found: {self.credentials_file}")
                    print("\nTo set up Google Drive API:")
                    print("1. Go to https://console.cloud.google.com/")
                    print("2. Create a new project or select existing")
                    print("3. Enable Google Drive API")
                    print("4. Create OAuth 2.0 credentials (Desktop app)")
                    print(f"5. Download credentials and save as '{self.credentials_file}'")
                    return False

                print("Starting OAuth authentication flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)

                # Try local server first, fall back to manual flow if no browser
                try:
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    print("\n[INFO] Cannot open browser (running on server)")
                    print("[INFO] Using manual authentication flow...")
                    print("\nPlease visit this URL to authorize:\n")

                    # Get authorization URL
                    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
                    auth_url, _ = flow.authorization_url(prompt='consent')
                    print(auth_url)
                    print("\n")

                    # Get authorization code from user
                    code = input("Enter the authorization code: ")
                    flow.fetch_token(code=code)
                    creds = flow.credentials

            # Save credentials
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)

        # Build service
        self.service = build('drive', 'v3', credentials=creds)
        print("[OK] Successfully authenticated with Google Drive")
        return True

    def find_folder_by_name(self, folder_name: str) -> Optional[str]:
        """
        Find folder ID by name

        Args:
            folder_name: Name of the folder to find

        Returns:
            Folder ID or None if not found
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        try:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)',
                pageSize=10
            ).execute()

            items = results.get('files', [])

            if not items:
                print(f"[WARN] Folder '{folder_name}' not found")
                return None

            if len(items) > 1:
                print(f"[WARN] Multiple folders named '{folder_name}' found. Using first one.")

            folder_id = items[0]['id']
            print(f"[OK] Found folder '{folder_name}': {folder_id}")
            return folder_id

        except Exception as e:
            print(f"[ERROR] Error finding folder: {e}")
            return None

    def list_documents_in_folder(self, folder_id: str, include_all: bool = False) -> List[Dict]:
        """
        List documents in a folder

        Args:
            folder_id: Google Drive folder ID
            include_all: If False, only return unprocessed files

        Returns:
            List of file metadata dicts
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        try:
            # Build query
            mime_type_query = " or ".join(
                f"mimeType='{mime}'" for mime in self.SUPPORTED_MIME_TYPES.keys()
            )
            query = f"'{folder_id}' in parents and ({mime_type_query}) and trashed=false"

            # List files
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, mimeType, createdTime, modifiedTime, size, owners)',
                pageSize=100
            ).execute()

            files = results.get('files', [])

            # Filter processed files if needed
            if not include_all:
                files = [f for f in files if f['id'] not in self.processed_files]

            return files

        except Exception as e:
            print(f"[ERROR] Error listing documents: {e}")
            return []

    def download_file(self, file_id: str, file_name: str) -> Optional[bytes]:
        """
        Download file content from Google Drive

        Args:
            file_id: Google Drive file ID
            file_name: Name of the file (for logging)

        Returns:
            File content as bytes or None if error
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        try:
            request = self.service.files().get_media(fileId=file_id)
            file_buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(file_buffer, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    print(f"  Downloading {file_name}... {progress}%", end='\r')

            print(f"  [OK] Downloaded {file_name}              ")
            return file_buffer.getvalue()

        except Exception as e:
            print(f"  [ERROR] Failed to download {file_name}: {e}")
            return None

    def mark_as_processed(self, file_id: str):
        """Mark file as processed"""
        self.processed_files.add(file_id)
        self._save_state()

    def get_new_documents(self, folder_id: str) -> List[Dict]:
        """
        Get new (unprocessed) documents from folder

        Args:
            folder_id: Google Drive folder ID

        Returns:
            List of new document metadata
        """
        return self.list_documents_in_folder(folder_id, include_all=False)

    def monitor_folder(self, folder_id: str, callback, interval_seconds: int = 60):
        """
        Continuously monitor folder for new documents

        Args:
            folder_id: Google Drive folder ID
            callback: Function to call with new file (signature: callback(file_metadata, file_content))
            interval_seconds: Check interval in seconds
        """
        print("="*70)
        print("GOOGLE DRIVE MONITOR - RUNNING")
        print("="*70)
        print(f"Folder ID: {folder_id}")
        print(f"Check interval: {interval_seconds} seconds")
        print("Press Ctrl+C to stop")
        print("="*70)

        try:
            while True:
                # Get new documents
                new_docs = self.get_new_documents(folder_id)

                if new_docs:
                    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Found {len(new_docs)} new document(s)")

                    for file_meta in new_docs:
                        print(f"\nProcessing: {file_meta['name']}")

                        # Download file
                        file_content = self.download_file(file_meta['id'], file_meta['name'])

                        if file_content:
                            # Call callback
                            try:
                                callback(file_meta, file_content)
                                self.mark_as_processed(file_meta['id'])
                                print(f"  [OK] Successfully processed {file_meta['name']}")
                            except Exception as e:
                                print(f"  [ERROR] Failed to process {file_meta['name']}: {e}")
                else:
                    # Silent check (no new files)
                    pass

                # Wait for next check
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            print("\n\n[OK] Monitor stopped by user")
        except Exception as e:
            print(f"\n[ERROR] Monitor error: {e}")

    def reset_state(self):
        """Reset processed files state (for testing)"""
        self.processed_files.clear()
        self._save_state()
        print("[OK] State reset - all files will be reprocessed")

    def _load_state(self):
        """Load processed files state"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.processed_files = set(data.get('processed_files', []))
                print(f"[OK] Loaded state: {len(self.processed_files)} files already processed")
            except Exception as e:
                print(f"[WARN] Could not load state: {e}")
                self.processed_files = set()
        else:
            self.processed_files = set()

    def _save_state(self):
        """Save processed files state"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump({
                    'processed_files': list(self.processed_files),
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"[WARN] Could not save state: {e}")


def test_connection():
    """Test Google Drive connection"""
    print("="*70)
    print("GOOGLE DRIVE CONNECTION TEST")
    print("="*70)

    monitor = GoogleDriveMonitor()

    # Authenticate
    if not monitor.authenticate():
        return

    # List all folders
    print("\nListing your Google Drive folders...")
    try:
        results = monitor.service.files().list(
            q="mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces='drive',
            fields='files(id, name)',
            pageSize=20
        ).execute()

        folders = results.get('files', [])

        if folders:
            print(f"\nFound {len(folders)} folders:")
            for folder in folders:
                print(f"  - {folder['name']} (ID: {folder['id']})")
        else:
            print("No folders found")

    except Exception as e:
        print(f"[ERROR] {e}")

    print("\n" + "="*70)
    print("[OK] Connection test complete!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_connection()
    else:
        print("Google Drive Monitor Module")
        print("\nUsage:")
        print("  python google_drive_monitor.py test    # Test connection")
        print("\nOr use in your code:")
        print("  from google_drive_monitor import GoogleDriveMonitor")
        print("  monitor = GoogleDriveMonitor()")
        print("  monitor.authenticate()")
        print("  folder_id = monitor.find_folder_by_name('RAG Documents')")
        print("  monitor.monitor_folder(folder_id, your_callback_function)")

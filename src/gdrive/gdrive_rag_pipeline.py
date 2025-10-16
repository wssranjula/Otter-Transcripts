"""
Google Drive to RAG Pipeline Integration
Automatically processes documents from Google Drive and loads them into Neo4j
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

from src.gdrive.document_parser import DocumentParser
from src.gdrive.google_drive_monitor import GoogleDriveMonitor
from src.core.parse_for_rag import RAGTranscriptParser
from src.core.load_to_neo4j_rag import RAGNeo4jLoader


class GoogleDriveRAGPipeline:
    """Integrated pipeline: Google Drive → Document Parser → RAG → Neo4j"""

    def __init__(self, config_file: str = 'config/gdrive_config.json'):
        """
        Initialize pipeline with configuration

        Args:
            config_file: Path to configuration JSON file
        """
        self.config = self._load_config(config_file)

        # Initialize components
        self.doc_parser = DocumentParser()
        self.gdrive_monitor = GoogleDriveMonitor(
            credentials_file=self.config['google_drive']['credentials_file'],
            token_file=self.config['google_drive']['token_file'],
            state_file=self.config['google_drive']['state_file']
        )

        # RAG components
        self.rag_parser = RAGTranscriptParser(
            transcript_dir=self.config['rag']['temp_transcript_dir'],
            mistral_api_key=self.config['rag']['mistral_api_key'],
            model=self.config['rag']['model']
        )

        self.neo4j_loader = None  # Initialize when needed

    def _load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file"""
        if not os.path.exists(config_file):
            print(f"[WARN] Config file not found: {config_file}")
            print("Creating default configuration...")
            self._create_default_config(config_file)

        with open(config_file, 'r') as f:
            config = json.load(f)

        return config

    def _create_default_config(self, config_file: str):
        """Create default configuration file"""
        default_config = {
            "google_drive": {
                "credentials_file": "config/credentials.json",
                "token_file": "config/token.pickle",
                "state_file": "config/gdrive_state.json",
                "folder_name": "RAG Documents",
                "folder_id": None,
                "monitor_interval_seconds": 60
            },
            "rag": {
                "temp_transcript_dir": "gdrive_transcripts",
                "output_json": "knowledge_graph_gdrive.json",
                "mistral_api_key": "YOUR_MISTRAL_API_KEY",
                "model": "mistral-large-latest"
            },
            "neo4j": {
                "uri": "bolt://localhost:7687",
                "user": "neo4j",
                "password": "YOUR_NEO4J_PASSWORD"
            },
            "processing": {
                "auto_load_to_neo4j": True,
                "clear_temp_files": False,
                "batch_processing": False
            }
        }

        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)

        print(f"[OK] Created default config: {config_file}")
        print("Please edit the config file with your settings:")
        print("  - Mistral API key")
        print("  - Neo4j credentials")
        print("  - Google Drive folder name")

    def setup_google_drive(self):
        """Setup and authenticate Google Drive"""
        print("\n" + "="*70)
        print("GOOGLE DRIVE SETUP")
        print("="*70)

        # Authenticate
        if not self.gdrive_monitor.authenticate():
            return False

        # Find folder
        folder_name = self.config['google_drive']['folder_name']
        folder_id = self.config['google_drive'].get('folder_id')

        if not folder_id:
            print(f"\nSearching for folder: {folder_name}")
            folder_id = self.gdrive_monitor.find_folder_by_name(folder_name)

            if folder_id:
                # Save folder ID to config
                self.config['google_drive']['folder_id'] = folder_id
                with open('config/gdrive_config.json', 'w') as f:
                    json.dump(self.config, f, indent=2)
                print("[OK] Folder ID saved to config")
            else:
                print(f"[ERROR] Folder '{folder_name}' not found")
                print("\nPlease either:")
                print(f"  1. Create a folder named '{folder_name}' in Google Drive")
                print("  2. Update the folder_name in gdrive_config.json")
                return False

        return True

    def process_document(self, file_metadata: Dict, file_content: bytes) -> bool:
        """
        Process a single document through the RAG pipeline

        Args:
            file_metadata: Google Drive file metadata
            file_content: File content as bytes

        Returns:
            True if successful, False if any step failed
        """
        print("\n" + "="*70)
        print(f"PROCESSING: {file_metadata['name']}")
        print("="*70)
        print(f"[LOG] File size: {len(file_content)} bytes")
        print(f"[LOG] File type: {file_metadata.get('mimeType', 'unknown')}")
        print(f"[LOG] Created: {file_metadata.get('createdTime', 'unknown')}")

        # Step 1: Parse document to text
        print("\n[STEP 1/5] Parsing document...")
        try:
            print(f"  [LOG] Calling document parser...")
            parsed_doc = self.doc_parser.parse_document(
                file_path=file_metadata['name'],
                file_content=file_content
            )
            print(f"  [OK] Extracted {len(parsed_doc['text'])} characters")
            print(f"  [LOG] Document type: {parsed_doc['type']}")
            print(f"  [LOG] Metadata: {parsed_doc['metadata']}")
        except Exception as e:
            print(f"  [ERROR] Failed to parse document: {e}")
            print(f"  [ERROR] Error type: {type(e).__name__}")
            import traceback
            print(f"  [ERROR] Traceback:\n{traceback.format_exc()}")
            return False

        # Step 2: Convert to transcript format and save
        print("\n[STEP 2/5] Converting to transcript format...")
        try:
            temp_dir = Path(self.config['rag']['temp_transcript_dir'])
            temp_dir.mkdir(parents=True, exist_ok=True)
            print(f"  [LOG] Temp directory: {temp_dir}")

            transcript_text = self.doc_parser.convert_to_transcript_format(
                parsed_doc,
                timestamp=file_metadata.get('createdTime')
            )
            print(f"  [LOG] Transcript length: {len(transcript_text)} characters")

            # Save as transcript file
            transcript_file = temp_dir / f"{Path(file_metadata['name']).stem}.txt"
            with open(transcript_file, 'w', encoding='utf-8') as f:
                f.write(transcript_text)

            print(f"  [OK] Saved as: {transcript_file}")
        except Exception as e:
            print(f"  [ERROR] Failed to save transcript: {e}")
            import traceback
            print(f"  [ERROR] Traceback:\n{traceback.format_exc()}")
            return False

        # Step 3: Run RAG extraction
        print("\n[STEP 3/5] Running RAG extraction...")
        try:
            print(f"  [LOG] Parsing transcript with RAG parser...")
            result = self.rag_parser.parse_transcript(transcript_file)
            print(f"  [OK] Created {len(result['chunks'])} chunks")
            print(f"  [OK] Extracted {len(result['entities'])} entities")
            print(f"  [LOG] Decisions: {len(result.get('decisions', []))}")
            print(f"  [LOG] Actions: {len(result.get('actions', []))}")
        except Exception as e:
            print(f"  [ERROR] Failed RAG extraction: {e}")
            import traceback
            print(f"  [ERROR] Traceback:\n{traceback.format_exc()}")
            return False

        # Step 4: Load to Neo4j (if enabled)
        if self.config['processing']['auto_load_to_neo4j']:
            print("\n[STEP 4/5] Loading to Neo4j...")
            try:
                print(f"  [LOG] Ensuring Neo4j connection...")
                self._ensure_neo4j_connection()

                # Create temporary JSON for this document
                temp_json = {
                    'metadata': {
                        'generated_at': datetime.now().isoformat(),
                        'transcript_count': 1,
                        'source': 'google_drive',
                        'file_name': file_metadata['name']
                    },
                    'transcripts': [result],
                    'entity_index': self.rag_parser.entity_cache
                }

                # Save temp JSON
                temp_json_file = Path(self.config['rag']['output_json'])
                temp_json_file.parent.mkdir(parents=True, exist_ok=True)
                print(f"  [LOG] Saving temp JSON to: {temp_json_file}")

                with open(temp_json_file, 'w', encoding='utf-8') as f:
                    json.dump(temp_json, f, indent=2)

                # Load to Neo4j
                print(f"  [LOG] Loading to Neo4j...")
                self.neo4j_loader.load_from_json(str(temp_json_file))
                print("  [OK] Loaded to Neo4j")

            except Exception as e:
                print(f"  [ERROR] Failed to load to Neo4j: {e}")
                import traceback
                print(f"  [ERROR] Traceback:\n{traceback.format_exc()}")
                return False
        else:
            print("\n[STEP 4/5] Skipping Neo4j load (disabled in config)")

        # Step 5: Cleanup (if enabled)
        if self.config['processing']['clear_temp_files']:
            print("\n[STEP 5/5] Cleaning up temporary files...")
            try:
                transcript_file.unlink()
                print("  [OK] Deleted temporary transcript file")
            except Exception as e:
                print(f"  [WARN] Could not delete temp file: {e}")
        else:
            print("\n[STEP 5/5] Keeping temporary files (clear_temp_files=false)")

        print("\n" + "="*70)
        print("[SUCCESS] DOCUMENT PROCESSING COMPLETE")
        print("="*70)
        return True

    def _ensure_neo4j_connection(self):
        """Ensure Neo4j connection is established"""
        if not self.neo4j_loader:
            neo4j_config = self.config['neo4j']
            self.neo4j_loader = RAGNeo4jLoader(
                neo4j_config['uri'],
                neo4j_config['user'],
                neo4j_config['password']
            )
            # Create schema if needed
            self.neo4j_loader.create_schema()

    def start_monitoring(self):
        """Start monitoring Google Drive folder"""
        # Setup Google Drive
        if not self.setup_google_drive():
            return

        # Get folder ID
        folder_id = self.config['google_drive']['folder_id']
        interval = self.config['google_drive']['monitor_interval_seconds']

        # Start monitoring
        self.gdrive_monitor.monitor_folder(
            folder_id=folder_id,
            callback=self.process_document,
            interval_seconds=interval
        )

    def process_existing_files(self):
        """Process all existing files in the folder (one-time batch)"""
        # Setup Google Drive
        if not self.setup_google_drive():
            return

        print("\n" + "="*70)
        print("BATCH PROCESSING EXISTING FILES")
        print("="*70)

        folder_id = self.config['google_drive']['folder_id']

        # Get all documents (including already processed)
        print("[LOG] Listing documents in folder...")
        all_docs = self.gdrive_monitor.list_documents_in_folder(folder_id, include_all=True)

        if not all_docs:
            print("[INFO] No documents found in folder")
            return

        print(f"\n[INFO] Found {len(all_docs)} document(s)")
        print("[LOG] Starting batch processing...\n")

        success_count = 0
        error_count = 0
        skipped_count = 0

        for i, file_meta in enumerate(all_docs, 1):
            print(f"\n{'='*70}")
            print(f"[FILE {i}/{len(all_docs)}] {file_meta['name']}")
            print(f"{'='*70}")

            # Download
            print(f"[LOG] Downloading file from Google Drive...")
            file_content = self.gdrive_monitor.download_file(file_meta['id'], file_meta['name'])

            if not file_content:
                print(f"[ERROR] Failed to download file")
                error_count += 1
                continue

            # Process document
            try:
                success = self.process_document(file_meta, file_content)

                if success:
                    print(f"[LOG] Marking file as processed...")
                    self.gdrive_monitor.mark_as_processed(file_meta['id'])
                    success_count += 1
                    print(f"[INFO] File successfully processed and marked")
                else:
                    print(f"[ERROR] File processing returned False (see errors above)")
                    error_count += 1

            except Exception as e:
                print(f"[ERROR] Unexpected exception during processing: {e}")
                import traceback
                print(f"[ERROR] Traceback:\n{traceback.format_exc()}")
                error_count += 1

        print("\n" + "="*70)
        print("BATCH PROCESSING SUMMARY")
        print("="*70)
        print(f"Total files: {len(all_docs)}")
        print(f"✓ Successfully processed: {success_count}")
        print(f"✗ Failed: {error_count}")
        if skipped_count > 0:
            print(f"⊘ Skipped: {skipped_count}")
        print("="*70)

        if error_count > 0:
            print("\n[WARN] Some files failed to process. Check logs above for details.")
        if success_count == len(all_docs):
            print("\n[SUCCESS] All files processed successfully!")
        elif success_count > 0:
            print(f"\n[PARTIAL] {success_count}/{len(all_docs)} files processed successfully")

    def close(self):
        """Close connections"""
        if self.neo4j_loader:
            self.neo4j_loader.close()


def main():
    """Main entry point"""
    print("="*70)
    print("GOOGLE DRIVE TO RAG PIPELINE")
    print("="*70)

    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "setup":
            # Setup only
            pipeline = GoogleDriveRAGPipeline()
            pipeline.setup_google_drive()
            return

        elif command == "batch":
            # Process all existing files
            pipeline = GoogleDriveRAGPipeline()
            try:
                pipeline.process_existing_files()
            finally:
                pipeline.close()
            return

        elif command == "monitor":
            # Start monitoring
            pipeline = GoogleDriveRAGPipeline()
            try:
                pipeline.start_monitoring()
            finally:
                pipeline.close()
            return

    # Default: show usage
    print("\nUsage:")
    print("  python gdrive_rag_pipeline.py setup     # Setup Google Drive connection")
    print("  python gdrive_rag_pipeline.py batch     # Process all existing files")
    print("  python gdrive_rag_pipeline.py monitor   # Start monitoring for new files")
    print("\n" + "="*70)
    print("\nBefore running, make sure you have:")
    print("  1. Google Drive API credentials (credentials.json)")
    print("  2. Updated gdrive_config.json with your settings")
    print("  3. Neo4j running and accessible")
    print("="*70)


if __name__ == "__main__":
    main()

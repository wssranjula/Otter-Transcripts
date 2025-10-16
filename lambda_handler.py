"""
AWS Lambda handler for Google Drive RAG Pipeline
Triggered by CloudWatch Events (cron schedule)
"""

import json
import sys
from src.gdrive.gdrive_rag_pipeline import GoogleDriveRAGPipeline


def lambda_handler(event, context):
    """
    AWS Lambda handler

    Triggered by CloudWatch Events on a schedule
    Processes new files from Google Drive
    """

    print("Starting Google Drive RAG Pipeline...")

    try:
        # Initialize pipeline
        pipeline = GoogleDriveRAGPipeline(config_file='config/gdrive_config.json')

        # Process existing files
        pipeline.process_existing_files()

        # Close connections
        pipeline.close()

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Pipeline completed successfully',
                'timestamp': context.request_id
            })
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }

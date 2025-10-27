"""
Quick script to run Sybil schema migration
Adds tag properties to Neo4j for confidentiality and freshness tracking
"""

from src.core.schema_migration_tags import main

if __name__ == "__main__":
    print("\n" + "="*70)
    print("SYBIL SCHEMA MIGRATION")
    print("="*70)
    print("\nThis will add the following properties to your Neo4j nodes:")
    print("  - tags: [string]")
    print("  - confidentiality_level: string")
    print("  - document_status: string")
    print("  - created_date: date")
    print("  - last_modified_date: date")
    print("\nThis is safe to run multiple times (idempotent).")
    print("="*70 + "\n")
    
    response = input("Continue with migration? (y/n): ")
    if response.lower() == 'y':
        main()
    else:
        print("\nMigration cancelled.")


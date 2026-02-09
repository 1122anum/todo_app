#!/usr/bin/env python3
"""
Database Migration Runner for Event-Driven Todo Platform
Runs SQL migrations in order against Neon PostgreSQL database
"""

import os
import sys
from pathlib import Path
import psycopg2
from psycopg2 import sql
from datetime import datetime

# Migration directory
MIGRATIONS_DIR = Path(__file__).parent / "migrations"

# Database connection from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    """Get database connection from environment variable"""
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL environment variable not set")
        print("Example: postgresql://user:password@host:5432/database")
        sys.exit(1)

    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"ERROR: Failed to connect to database: {e}")
        sys.exit(1)

def create_migrations_table(conn):
    """Create migrations tracking table if it doesn't exist"""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id SERIAL PRIMARY KEY,
                migration_file VARCHAR(255) NOT NULL UNIQUE,
                applied_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        conn.commit()
        print("✓ Migrations tracking table ready")

def get_applied_migrations(conn):
    """Get list of already applied migrations"""
    with conn.cursor() as cur:
        cur.execute("SELECT migration_file FROM schema_migrations ORDER BY id")
        return {row[0] for row in cur.fetchall()}

def get_pending_migrations(applied_migrations):
    """Get list of migrations that haven't been applied yet"""
    all_migrations = sorted([
        f.name for f in MIGRATIONS_DIR.glob("*.sql")
        if f.is_file()
    ])

    pending = [m for m in all_migrations if m not in applied_migrations]
    return pending

def apply_migration(conn, migration_file):
    """Apply a single migration file"""
    migration_path = MIGRATIONS_DIR / migration_file

    print(f"\nApplying migration: {migration_file}")

    try:
        # Read migration SQL
        with open(migration_path, 'r') as f:
            migration_sql = f.read()

        # Execute migration
        with conn.cursor() as cur:
            cur.execute(migration_sql)

            # Record migration as applied
            cur.execute(
                "INSERT INTO schema_migrations (migration_file) VALUES (%s)",
                (migration_file,)
            )

        conn.commit()
        print(f"✓ Successfully applied: {migration_file}")
        return True

    except Exception as e:
        conn.rollback()
        print(f"✗ Failed to apply {migration_file}: {e}")
        return False

def main():
    """Main migration runner"""
    print("=" * 60)
    print("Database Migration Runner")
    print("=" * 60)

    # Connect to database
    print("\nConnecting to database...")
    conn = get_connection()
    print("✓ Connected successfully")

    # Create migrations tracking table
    create_migrations_table(conn)

    # Get applied and pending migrations
    applied_migrations = get_applied_migrations(conn)
    pending_migrations = get_pending_migrations(applied_migrations)

    print(f"\nMigrations status:")
    print(f"  Applied: {len(applied_migrations)}")
    print(f"  Pending: {len(pending_migrations)}")

    if not pending_migrations:
        print("\n✓ All migrations are up to date!")
        conn.close()
        return

    # Apply pending migrations
    print(f"\nApplying {len(pending_migrations)} pending migration(s)...")

    success_count = 0
    for migration_file in pending_migrations:
        if apply_migration(conn, migration_file):
            success_count += 1
        else:
            print(f"\n✗ Migration failed. Stopping.")
            break

    # Summary
    print("\n" + "=" * 60)
    print(f"Migration Summary:")
    print(f"  Successfully applied: {success_count}/{len(pending_migrations)}")
    print("=" * 60)

    conn.close()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script to generate seed SQL with proper Django password hashes.
Run this script to regenerate the 02-seed-data.sql file with valid password hashes.

Usage:
    python generate_seed_sql.py

This will:
1. Generate a proper Django password hash for 'password123'
2. Update the 02-seed-data.sql file with the correct hash
"""

import hashlib
import base64
import secrets
import os
import re
from pathlib import Path


def make_password(password: str, salt: str = None, iterations: int = 720000) -> str:
    """
    Generate a Django-compatible PBKDF2-SHA256 password hash.

    Args:
        password: The plaintext password
        salt: Optional salt (generated if not provided)
        iterations: Number of PBKDF2 iterations (Django 4.2+ uses 720000)

    Returns:
        Django-format password hash string
    """
    if salt is None:
        salt = secrets.token_urlsafe(12)

    # Generate the hash using PBKDF2-SHA256
    dk = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        iterations,
        dklen=32
    )

    # Encode the hash in base64
    hash_b64 = base64.b64encode(dk).decode('ascii')

    # Return in Django's format
    return f"pbkdf2_sha256${iterations}${salt}${hash_b64}"


def update_seed_sql(password_hash: str):
    """Update the seed SQL file with the new password hash."""
    init_dir = Path(__file__).parent / "init"
    sql_file = init_dir / "02-seed-data.sql"

    if not sql_file.exists():
        print(f"Error: {sql_file} not found")
        return False

    content = sql_file.read_text()

    # Update the password hash in the SQL
    # Use simple string replacement to avoid regex escaping issues
    old_pattern = "\\set password_hash '"

    # Find the line and replace it
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith(old_pattern):
            lines[i] = f"\\set password_hash '{password_hash}'"
            break

    new_content = '\n'.join(lines)

    sql_file.write_text(new_content)
    print(f"Updated {sql_file}")
    print(f"New password hash: {password_hash[:50]}...")

    return True


def main():
    password = "password123"

    print("=" * 60)
    print("Generating Django password hash for seed data")
    print("=" * 60)

    # Generate password hash
    password_hash = make_password(password)

    print(f"Password: {password}")
    print(f"Hash: {password_hash}")
    print()

    # Update the SQL file
    if update_seed_sql(password_hash):
        print()
        print("=" * 60)
        print("SUCCESS! Now rebuild the Docker image:")
        print("  cd docker && docker build -f Dockerfile.postgres -t sda-postgres .")
        print("=" * 60)
    else:
        print("Failed to update SQL file")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())


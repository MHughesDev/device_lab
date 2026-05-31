#!/usr/bin/env python3
"""Generate cryptographically random secrets for .env.

Usage:
    python scripts/generate_secrets.py           # write missing secrets to .env
    python scripts/generate_secrets.py --dry-run # print what would change
    python scripts/generate_secrets.py --force   # overwrite existing values
"""

import argparse
import secrets
import sys
from pathlib import Path

SECRETS_FIELDS = ["SECRET_KEY", "POSTGRES_PASSWORD", "FIRST_SUPERUSER_PASSWORD"]


def generate() -> str:
    return secrets.token_urlsafe(32)


def parse_env(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def needs_replacement(value: str) -> bool:
    return not value or value.lower() in {"changethis", "change_this", "secret", "password"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate dev secrets for .env")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without writing")
    parser.add_argument("--force", action="store_true", help="Overwrite existing values")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    env_path = root / ".env"

    if not env_path.exists():
        print(f"No .env found at {env_path} — copy .env.example first.", file=sys.stderr)
        sys.exit(1)

    text = env_path.read_text()
    current = parse_env(text)
    lines = text.splitlines(keepends=True)
    changed: list[str] = []

    for field in SECRETS_FIELDS:
        existing = current.get(field, "")
        if not args.force and existing and not needs_replacement(existing):
            continue
        new_val = generate()
        changed.append(field)
        if args.dry_run:
            print(f"  {field}={new_val}")
        else:
            updated = False
            for i, line in enumerate(lines):
                if line.startswith(f"{field}=") or line.startswith(f"{field} ="):
                    lines[i] = f"{field}={new_val}\n"
                    updated = True
                    break
            if not updated:
                lines.append(f"{field}={new_val}\n")

    if not changed:
        print("All secrets already set. Use --force to regenerate.")
        return

    if args.dry_run:
        print(f"Would update {len(changed)} field(s): {', '.join(changed)}")
    else:
        env_path.write_text("".join(lines))
        print(f"Updated {len(changed)} field(s) in {env_path}: {', '.join(changed)}")


if __name__ == "__main__":
    main()

# skills/devops/compose-profile-matrix.py
"""Print docker compose --profile combinations (documentation helper)."""

from __future__ import annotations


def main() -> int:
    profiles = ["db", "ai", "worker"]
    print("Example:")
    print("  docker compose --profile db up")
    print("  docker compose --profile db --profile ai up")
    print("Profiles defined in docker-compose.yml:", ", ".join(profiles))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

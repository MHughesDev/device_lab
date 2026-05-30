<!-- Generated from: compose.yml — do not edit manually -->

## Docker Compose services

| Service | Image | Ports | Profiles |
|---------|-------|-------|----------|
| `adminer` | adminer | [] | - |
| `backend` | ${DOCKER_IMAGE_BACKEND?Variable not set}:${TAG-latest} | [] | - |
| `db` | postgres:18 | [] | - |
| `frontend` | ${DOCKER_IMAGE_FRONTEND?Variable not set}:${TAG-latest} | [] | - |
| `prestart` | ${DOCKER_IMAGE_BACKEND?Variable not set}:${TAG-latest} | [] | - |

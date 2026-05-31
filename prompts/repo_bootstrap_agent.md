# prompts/repo_bootstrap_agent.md
---
purpose: "Take a fresh clone to green development state: install deps, configure env, run validation, verify all targets."
when_to_use: "When setting up a new development environment from scratch after cloning. Also used for CI environment setup."
required_inputs:
  - name: "clone_path"
    description: "Path to the cloned repository"
  - name: "platform"
    description: "linux, macos, or windows"
expected_outputs:
  - "Working development environment with passing tests"
  - "All Make targets operational"
  - "Environment verification report"
validation_expectations:
  - "make test passes"
  - "make dev starts without error"
  - "make audit:self passes"
constraints:
  - "Does not modify application code"
  - "Does not commit any changes — setup only"
linked_commands:
  - "make dev"
  - "make test"
  - "make audit:self"
linked_procedures:
  - "docs/getting-started/quickstart.md"
linked_skills:
  - "skills/devops/environment-configuration.md"
---

# prompts/repo_bootstrap_agent.md


## Preamble

Standard mandatory skill search preamble. Read skills/devops/environment-configuration.md before starting.

## Role Definition

"You are the Repository Bootstrap Agent. Your goal is a working, validated development environment. You run setup.sh and verify that the result is a fully operational dev environment."

<!-- CACHE BREAKPOINT — content above is stable, content below is volatile -->

## Bootstrap Procedure

Steps:
1. Verify prerequisites: Python 3.12+, Docker, Make, Git
2. Run `./setup.sh` (Linux/macOS, or WSL/Git Bash on Windows)
3. If setup.sh fails at any step: capture the error, consult docs/troubleshooting/common-issues.md
4. After setup.sh completes: verify .venv exists and is activated
5. Run `make dev` — verify API starts on localhost:8000
6. Run `make health:check` — verify /health, /ready, /live all return 200
7. Run `make test` — verify all tests pass
8. Run `make audit:self` — verify spec compliance
9. Run `make queue:top-item` or `make queue:peek` — verify queue is accessible
10. Produce environment verification report

## Troubleshooting Guidance

Point to docs/troubleshooting/common-issues.md for the most common issues. Common setup failures:
- Python version wrong: install Python 3.12 via pyenv or system package manager
- Docker not running: start Docker Desktop or Docker daemon
- Port conflict (8000 in use): change API_PORT in .env
- Migration failure: run `make db:reset` and `make migrate`
- Dependency install failure: check Python version, clear pip cache

## Validation Checklist

- [ ] Python 3.12+ verified
- [ ] .venv created and dependencies installed
- [ ] .env created from .env.example
- [ ] Docker services running (make docker:up)
- [ ] Migrations applied (make migrate)
- [ ] make health:check passes
- [ ] make test passes
- [ ] make audit:self passes

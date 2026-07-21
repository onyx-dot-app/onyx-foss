# QYBE Development Procedures


==========================================================================================
                                    START
==========================================================================================
chmod +x start.sh
./start.sh
==========================================================================================

# One-time setup (run once)

Open terminal:
cd ~/projects/QYBE

Ensure Craft resources exist:
docker network inspect onyx_craft_sandbox >/dev/null 2>&1 || docker network create onyx_craft_sandbox
docker volume inspect sandbox_proxy_ca >/dev/null 2>&1 || docker volume create sandbox_proxy_ca

Ensure persistent Ollama exists:
docker volume inspect ollama_data >/dev/null 2>&1 || docker volume create ollama_data
docker rm -f ollama >/dev/null 2>&1 || true
docker run -d --name ollama -p 11434:11434 -v ollama_data:/root/.ollama ollama/ollama

Pull your model once:
docker exec -it ollama ollama pull gemma4:12b
docker exec -it ollama ollama list

# Daily start (Docker stack with Craft)

Terminal A:
cd ~/projects/QYBE
ENABLE_CRAFT=true docker compose
--env-file .env
-p qybe
-f docker-compose.yml
-f docker-compose.dev.yml
-f docker-compose.craft.yml
up -d --wait --remove-orphans

Verify:
docker compose
--env-file .env
-p qybe
-f docker-compose.yml
-f docker-compose.dev.yml
-f docker-compose.craft.yml
ps

Recommended for active frontend development (hot reload from your local code)

Terminal B:
cd ~/projects/QYBE
source "$HOME/.local/bin/env"
source .venv/bin/activate
export PATH="$HOME/.bun/bin:$PATH"
INTERNAL_URL=http://127.0.0.1:8080 uv run --with onyx-devtools ods web dev
Notes:

Keep Docker api_server/background running in Terminal A.
Use Terminal B for frontend edits and immediate reload.

# Daily stop

Stop local frontend (if running): Ctrl+C in Terminal B
Stop Docker stack:
cd ~/projects/QYBE
docker compose
--env-file .env
-p qybe
-f docker-compose.yml
-f docker-compose.dev.yml
-f docker-compose.craft.yml
down


# Optional full cleanup (containers + data volumes)

Use only when you want a fresh reset:
cd ~/projects/QYBE
docker compose
--env-file .env
-p qybe
-f docker-compose.yml
-f docker-compose.dev.yml
-f docker-compose.craft.yml
down -v

==========================================================================================

This file is a development runbook for starting, stopping, testing, committing, and synchronizing QYBE.

## Core rules

- Do not develop directly on `main`.
- Start feature work from an updated `dev`.
- Use one focused branch per change.
- Keep unrelated changes in separate commits and branches.
- Review the diff before staging.
- Run focused tests before committing.
- Push only after tests pass.
- Keep orchestration routing shadow-only unless separately enabled and approved.
- Never store raw business prompts in telemetry.

---

## 1. Start a new feature

Update `dev`:

```bash
cd ~/projects/QYBE
git switch dev
git pull --ff-only origin dev
git branch --show-current
git status --short
git log --oneline -5
```

The working tree should be clean before creating a feature branch.

Create one focused branch:

```bash
git switch -c feature/<short-feature-name>
```

For maintenance or documentation work:

```bash
git switch -c chore/<short-task-name>
```

For bug fixes:

```bash
git switch -c fix/<short-fix-name>
```

---

## 2. Activate the development environment

```bash
cd ~/projects/QYBE
source "$HOME/.local/bin/env"
export PATH="$HOME/.bun/bin:$PATH"
source .venv/bin/activate
```

Verify the tools:

```bash
python --version
uv --version
bun --version
ods --version
docker --version
docker compose version
```

Expected main versions:

- Python 3.13
- Bun version pinned by the repository
- `ods` from `~/projects/QYBE/.venv/bin/ods`

---

## 3. Install or refresh dependencies

Python dependencies:

```bash
cd ~/projects/QYBE
source "$HOME/.local/bin/env"
uv sync --frozen --python 3.13
```

Frontend dependencies:

```bash
cd ~/projects/QYBE/web
export PATH="$HOME/.bun/bin:$PATH"
bun install --frozen-lockfile
```

Install Git hooks:

```bash
cd ~/projects/QYBE
source .venv/bin/activate
uv run pre-commit install
```

---

## 4. Start the hybrid development environment

Use Docker for infrastructure and run the backend and frontend on the host with hot reload.

### Terminal 1 — infrastructure

```bash
cd ~/projects/QYBE
source "$HOME/.local/bin/env"
source .venv/bin/activate
ods compose dev --infra --no-ee
ods env
ods db upgrade
```

### Terminal 2 — backend API

```bash
cd ~/projects/QYBE
source "$HOME/.local/bin/env"
source .venv/bin/activate
ods backend api --no-ee
```

### Terminal 3 — frontend

```bash
cd ~/projects/QYBE
export PATH="$HOME/.bun/bin:$PATH"
source .venv/bin/activate
INTERNAL_URL=http://127.0.0.1:8080 ods web dev
```

Typical local endpoints:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8080`
- ReDoc: `http://localhost:8080/redoc`

When accessing the EdgeXpert remotely, use SSH port forwarding for ports `3000` and `8080`.

---

## 5. Inspect containers and logs

List running containers:

```bash
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
```

Follow all Docker service logs:

```bash
ods logs
```

Follow selected services:

```bash
ods logs api_server background
```

Show the last 100 lines without following:

```bash
ods logs --tail 100 --follow=false
```

---

## 6. Stop the development environment

Stop the host frontend and backend with `Ctrl+C` in their terminals.

Stop Docker development infrastructure:

```bash
cd ~/projects/QYBE
source .venv/bin/activate
ods compose dev --down
```

Verify that the expected containers stopped:

```bash
docker ps
```

---

## 7. Review work before testing

```bash
cd ~/projects/QYBE
git branch --show-current
git status --short
git diff --stat
git diff
git diff --check
```

Confirm:

- only intended files changed;
- no generated files were added accidentally;
- no credentials, tokens, secrets, or raw business prompts are present;
- no unrelated refactoring is included;
- feature flags remain safe by default.

---

## 8. Run tests

Run the smallest relevant test set first.

Backend example:

```bash
cd ~/projects/QYBE
source .venv/bin/activate
python -m pytest -xv <relevant-test-path>
```

Frontend checks:

```bash
cd ~/projects/QYBE
source .venv/bin/activate
ods web lint
ods web types:check
ods web test
```

Run pre-commit checks for changed files:

```bash
cd ~/projects/QYBE
source .venv/bin/activate
uv run pre-commit run
```

Run all configured pre-commit checks when appropriate:

```bash
uv run pre-commit run --all-files
```

Do not use the full repository test suite unnecessarily for a small isolated change, but run broader validation before merging high-risk changes.

---

## 9. Create a focused commit

Review the exact files to stage:

```bash
git status --short
git diff
```

Stage only intended files:

```bash
git add <specific-file-1> <specific-file-2>
```

Review the staged change:

```bash
git diff --cached --stat
git diff --cached
git diff --cached --check
```

Commit with a descriptive message:

```bash
git commit -m "<type>: <concise description>"
```

Examples:

```bash
git commit -m "docs: add QYBE development runbook"
git commit -m "feat: add shadow orchestration route model"
git commit -m "fix: prevent router telemetry from storing raw prompts"
git commit -m "test: cover domain pack provider fallback"
```

Confirm the result:

```bash
git status --short
git log --oneline -3
```

---

## 10. Push the feature branch

Push only after the relevant tests pass:

```bash
git push -u origin "$(git branch --show-current)"
```

Create a pull request from the focused branch into `dev`.

The pull request should include:

- purpose of the change;
- files or subsystems affected;
- tests executed and their results;
- risks and privacy implications;
- feature-flag behavior;
- rollback considerations;
- recommended next step.

---

## 11. After the pull request is merged

Return to `dev` and update it:

```bash
cd ~/projects/QYBE
git switch dev
git pull --ff-only origin dev
git status --short
git log --oneline -5
```

Delete the local merged branch:

```bash
git branch -d <merged-branch-name>
```

Delete the remote branch when appropriate:

```bash
git push origin --delete <merged-branch-name>
```

---

## 12. Synchronize with upstream Onyx

Do not mix upstream synchronization with feature development.

Start from clean and updated `dev`:

```bash
cd ~/projects/QYBE
git switch dev
git pull --ff-only origin dev
git status --short
```

Fetch upstream:

```bash
git fetch upstream --prune
```

Create a dedicated synchronization branch:

```bash
git switch -c sync/onyx-YYYY-MM-DD
```

Merge upstream:

```bash
git merge --no-ff upstream/main
```

Resolve conflicts cautiously. Preserve QYBE branding, privacy safeguards, feature flags, and local-first behavior.

After resolving conflicts:

```bash
git status --short
git diff --check
```

Run relevant backend and frontend tests before committing and pushing the synchronization branch.

Never force-push `main` or `dev`.

---

## 13. Database migration commands

Show the current migration revision:

```bash
ods db current
```

Apply migrations:

```bash
ods db upgrade
```

Show migration history:

```bash
ods db history
```

Database downgrade, drop, restore, and snapshot operations are destructive or state-changing. Review their help before running them:

```bash
ods db downgrade --help
ods db drop --help
ods db restore --help
ods db dump --help
```

---

## 14. QYBE-specific safety checklist

Before merging architecture or orchestration changes, confirm:

- normal chat behavior remains unchanged unless explicitly enabled;
- the orchestration router remains shadow-only;
- active execution requires separate feature flags;
- router failures cannot break normal chat;
- telemetry stores hashes or safe metadata, not raw prompts;
- tenant and organization policies override user preferences;
- external data egress is explicitly governed;
- existing Onyx/QYBE infrastructure is reused rather than broadly rewritten;
- changes are backward-compatible or have a documented migration path.

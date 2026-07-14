import os
import sys
import json
import shutil
import subprocess
import time
import requests
from pathlib import Path

RESET = "\033[0m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"

def log(msg, color=RESET):
    print(f"{color}{msg}{RESET}")

def log_step(step, msg):
    print(f"\n{CYAN}{BOLD}[Step {step}]{RESET} {BOLD}{msg}{RESET}")

def log_ok(msg):
    log(f"  [OK] {msg}", GREEN)

def log_warn(msg):
    log(f"  [WARN] {msg}", YELLOW)

def log_err(msg):
    log(f"  [ERROR] {msg}", RED)

def run_cmd(cmd, cwd=None, check=True):
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        log_err(f"Command failed: {cmd}")
        log_err(f"  stdout: {result.stdout.strip()}")
        log_err(f"  stderr: {result.stderr.strip()}")
        return False
    return True

def load_env(env_path):
    env = {}
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip().strip('"').strip("'")
    return env

def github_request(method, url, token, json_data=None):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    resp = getattr(requests, method)(url, headers=headers, json=json_data)
    return resp

def github_get_login(token):
    resp = github_request("get", "https://api.github.com/user", token)
    if resp.status_code == 200:
        return resp.json().get("login")
    return None

def github_create_repo(token, name):
    log(f"  Creating GitHub repository '{name}'...")
    resp = github_request("post", "https://api.github.com/user/repos", token, {
        "name": name,
        "description": "AI Chatbot with persistent memory and RAG",
        "auto_init": False,
        "private": False
    })
    if resp.status_code == 201:
        log_ok(f"Repository created: {resp.json()['html_url']}")
        return resp.json()
    else:
        log_err(f"GitHub API error ({resp.status_code}): {resp.json().get('message', '')}")
        return None

def github_upload_blob(token, owner, repo, path, content, message="Initial commit"):
    import base64
    b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    resp = github_request("put", f"https://api.github.com/repos/{owner}/{repo}/contents/{path}", token, {
        "message": message,
        "content": b64
    })
    return resp.status_code in [200, 201]

def github_upload_tree(token, owner, repo, project_root, remote_prefix=""):
    SKIP = {".git", "node_modules", "__pycache__", ".next", "venv", ".env", "local.db", ".venv"}
    SKIP_FILES = {".env", "local.db", "*.pyc"}
    uploaded = 0
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for fname in files:
            if fname in SKIP_FILES or fname.endswith(".pyc"):
                continue
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, project_root).replace("\\", "/")
            remote_path = f"{remote_prefix}/{rel}" if remote_prefix else rel
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                if github_upload_blob(token, owner, repo, remote_path, content):
                    uploaded += 1
                    log_ok(f"  Uploaded: {remote_path}")
                else:
                    log_warn(f"  Failed: {remote_path}")
            except Exception as e:
                log_warn(f"  Skip {rel}: {e}")
    return uploaded

def vercel_deploy(token, project_name, github_full_name, branch="main"):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    log(f"  Creating Vercel project '{project_name}'...")
    resp = requests.post("https://api.vercel.com/v10/projects", headers=headers, json={
        "name": project_name,
        "framework": "nextjs"
    })
    if resp.status_code not in [200, 201]:
        log_err(f"Vercel project creation failed: {resp.text}")
        return None
    project_id = resp.json()["id"]
    log_ok(f"Project created: {project_id}")

    log(f"  Triggering deployment from GitHub...")
    resp = requests.post("https://api.vercel.com/v13/deployments", headers=headers, json={
        "name": "production",
        "project": project_id,
        "gitSource": {
            "type": "github",
            "ref": branch,
            "repoId": github_full_name
        }
    })
    if resp.status_code not in [200, 201]:
        log_err(f"Vercel deploy failed: {resp.text}")
        return None
    deployment_id = resp.json()["id"]
    log_ok(f"Deployment triggered: {deployment_id}")

    log(f"  Waiting for deployment (timeout 180s)...")
    for i in range(36):
        time.sleep(5)
        resp = requests.get(f"https://api.vercel.com/v13/deployments/{deployment_id}", headers=headers)
        if resp.status_code == 200:
            state = resp.json().get("state", "unknown")
            if state == "ready":
                url = resp.json().get("url", "")
                log_ok(f"Deployment ready: https://{url}")
                return url
            elif state in ["error", "canceled"]:
                log_err(f"Deployment failed with state: {state}")
                return None
            if i % 6 == 0:
                log(f"    State: {state}...")
    log_warn("Deployment timed out but may still be building on Vercel.")
    return None

def turso_create_db(auth_token, db_name):
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }

    log("  Getting Turso organization...")
    resp = requests.get("https://api.turso.tech/v2/organizations", headers=headers)
    if resp.status_code != 200:
        log_err(f"Failed to get Turso org: {resp.text}")
        return None, None
    orgs = resp.json().get("organizations", [])
    if not orgs:
        log_err("No Turso organization found")
        return None, None
    org = orgs[0]["name"]
    log_ok(f"Organization: {org}")

    log(f"  Creating database '{db_name}'...")
    resp = requests.post(f"https://api.turso.tech/v2/organizations/{org}/databases", headers=headers, json={
        "name": db_name,
        "group": "default"
    })
    if resp.status_code not in [200, 201]:
        log_err(f"Database creation failed: {resp.text}")
        return None, None
    db_url = resp.json().get("database", {}).get("url", "")
    log_ok(f"Database URL: {db_url}")

    log("  Creating auth token...")
    resp = requests.post(f"https://api.turso.tech/v2/organizations/{org}/databases/{db_name}/auth/tokens", headers=headers)
    if resp.status_code not in [200, 201]:
        log_err(f"Token creation failed: {resp.text}")
        return db_url, None
    token_val = resp.json().get("token", "")
    log_ok(f"Auth token created")

    return db_url, token_val

def turso_exec_sql(db_url, auth_token, sql):
    resp = requests.post(
        f"{db_url}/v2/pipeline",
        headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"},
        json={"statements": [{"sql": sql}]}
    )
    return resp.status_code == 200

def turso_init_schema(db_url, auth_token):
    log("  Initializing database schema...")
    sql = """
    CREATE TABLE IF NOT EXISTS memoria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_input TEXT NOT NULL,
        response TEXT NOT NULL,
        embedding BLOB,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
    if turso_exec_sql(db_url, auth_token, sql):
        log_ok("Schema created successfully")
        return True
    else:
        log_warn("Schema creation returned non-OK (may already exist)")
        return True

def prompt_tokens():
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  AI Chatbot - Automated Setup{RESET}")
    print(f"{BOLD}{'='*60}{RESET}\n")
    print("I need your API tokens to set everything up.\n")
    print(f"{YELLOW}Get your tokens from:{RESET}")
    print("  GitHub  : https://github.com/settings/tokens (needs 'repo' scope)")
    print("  Vercel  : https://vercel.com/account/tokens")
    print("  Turso   : Run 'turso auth login' then 'turso db tokens create <db>'")
    print()

    github_token = input("GitHub Token  : ").strip()
    vercel_token = input("Vercel Token  : ").strip()
    turso_url     = input("Turso DB URL  (leave empty to auto-create): ").strip()
    turso_token   = input("Turso Auth Token (leave empty to auto-create): ").strip()
    repo_name     = input("Repo/Project name [ai-chatbot]: ").strip() or "ai-chatbot"
    turso_db_name = input("Turso DB name [chatbot-db]: ").strip() or "chatbot-db"

    return {
        "github_token": github_token,
        "vercel_token": vercel_token,
        "turso_url": turso_url,
        "turso_token": turso_token,
        "repo_name": repo_name,
        "turso_db_name": turso_db_name,
    }

def write_env_file(project_root, vars_dict):
    env_path = os.path.join(project_root, "config", ".env")
    with open(env_path, "w") as f:
        for key, val in vars_dict.items():
            f.write(f"{key}={val}\n")
    log_ok(f".env written to {env_path}")
    return env_path

def main():
    project_root = os.path.dirname(os.path.abspath(__file__))

    tokens = prompt_tokens()

    if not tokens["github_token"]:
        log_err("GitHub token is required!")
        return
    if not tokens["vercel_token"]:
        log_err("Vercel token is required!")
        return

    log_step(1, "Configuring Turso database")
    turso_url = tokens["turso_url"]
    turso_token = tokens["turso_token"]

    if not turso_url or not turso_token:
        if not tokens["turso_token"]:
            log_err("Turso auth token is required for auto-creation!")
            return
        turso_url, turso_token = turso_create_db(tokens["turso_token"], tokens["turso_db_name"])
        if not turso_url:
            log_err("Turso setup failed!")
            return
    else:
        log_ok("Using provided Turso credentials")

    turso_init_schema(turso_url, turso_token)

    log_step(2, "Writing environment configuration")
    env_vars = {
        "GITHUB_TOKEN": tokens["github_token"],
        "VERCEL_TOKEN": tokens["vercel_token"],
        "TURSO_DB_URL": turso_url,
        "TURSO_AUTH_TOKEN": turso_token,
        "API_URL": "http://localhost:8000",
        "NEXT_PUBLIC_API_URL": "http://localhost:8000",
    }
    env_path = write_env_file(project_root, env_vars)

    log_step(3, "Creating GitHub repository")
    github_token = tokens["github_token"]
    repo_name = tokens["repo_name"]

    owner = github_get_login(github_token)
    if not owner:
        log_err("Failed to get GitHub user info!")
        return
    log_ok(f"GitHub user: {owner}")

    repo_info = github_create_repo(github_token, repo_name)
    if not repo_info:
        return

    log_step(4, "Uploading code to GitHub")
    uploaded = github_upload_tree(github_token, owner, repo_name, project_root)
    log_ok(f"Uploaded {uploaded} files")

    github_full = f"{owner}/{repo_name}"
    log_ok(f"Repository URL: https://github.com/{github_full}")

    log_step(5, "Deploying frontend to Vercel")
    vercel_url = vercel_deploy(
        tokens["vercel_token"],
        repo_name,
        github_full
    )

    log_step(6, "Installing local dependencies")
    log("  Installing Python dependencies...")
    run_cmd("pip install -r backend/requirements.txt", cwd=project_root, check=False)

    log("  Installing Node.js dependencies...")
    run_cmd("npm install", cwd=os.path.join(project_root, "frontend"), check=False)

    print(f"\n{'='*60}")
    print(f"{GREEN}{BOLD}  SETUP COMPLETE!{RESET}")
    print(f"{'='*60}\n")

    print(f"{BOLD}GitHub:{RESET}  https://github.com/{github_full}")
    if vercel_url:
        print(f"{BOLD}Vercel:{RESET}   https://{vercel_url}")
    print(f"{BOLD}Turso:{RESET}   {turso_url}")
    print()
    print(f"{BOLD}To run backend locally:{RESET}")
    print(f"  python run_backend.py")
    print()
    print(f"{BOLD}To run frontend locally:{RESET}")
    print(f"  cd frontend && npm run dev")
    print()

if __name__ == "__main__":
    main()

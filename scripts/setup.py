import os
import sys
import subprocess
from pathlib import Path

def run_command(command, cwd=None):
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    print(f"Success: {result.stdout}")
    return True

def setup_environment():
    print("=== Setting up environment ===")
    
    env_file = Path("config/.env")
    if not env_file.exists():
        print("Creating .env file from template...")
        import shutil
        shutil.copy("config/.env.example", env_file)
    
    print("Please edit config/.env with your tokens:")
    print("1. GITHUB_TOKEN - Your GitHub personal access token")
    print("2. VERCEL_TOKEN - Your Vercel access token")
    print("3. TURSO_DB_URL - Your Turso database URL")
    print("4. TURSO_AUTH_TOKEN - Your Turso auth token")
    
    input("\nPress Enter after editing .env file...")
    
    from dotenv import load_dotenv
    load_dotenv(env_file)
    
    required_vars = ['GITHUB_TOKEN', 'VERCEL_TOKEN', 'TURSO_DB_URL', 'TURSO_AUTH_TOKEN']
    for var in required_vars:
        if not os.getenv(var):
            print(f"Error: {var} not set in .env")
            return False
    
    return True

def setup_turso():
    print("\n=== Setting up Turso database ===")
    
    from scripts.init_turso import setup_turso
    
    auth_token = os.getenv('TURSO_AUTH_TOKEN')
    db_name = input("Enter database name (default: chatbot): ") or "chatbot"
    
    db_url, token = setup_turso(auth_token, db_name)
    
    if db_url and token:
        print(f"\nUpdate your .env file with:")
        print(f"TURSO_DB_URL={db_url}")
        print(f"TURSO_AUTH_TOKEN={token}")
        
        input("\nPress Enter after updating .env...")
        return True
    
    return False

def setup_github():
    print("\n=== Setting up GitHub repository ===")
    
    from scripts.setup_github import setup_github
    
    token = os.getenv('GITHUB_TOKEN')
    repo_name = input("Enter repository name (default: ai-chatbot): ") or "ai-chatbot"
    
    repo_url = setup_github(token, repo_name, ".")
    
    if repo_url:
        print(f"\nGitHub repository created: {repo_url}")
        return repo_url
    
    return None

def setup_vercel(github_repo):
    print("\n=== Deploying to Vercel ===")
    
    from scripts.deploy_vercel import deploy_vercel
    
    token = os.getenv('VERCEL_TOKEN')
    project_name = input("Enter Vercel project name (default: ai-chatbot): ") or "ai-chatbot"
    
    project_id = deploy_vercel(token, project_name, github_repo)
    
    if project_id:
        print(f"\nVercel project deployed!")
        return True
    
    return False

def install_dependencies():
    print("\n=== Installing dependencies ===")
    
    print("Installing backend dependencies...")
    if not run_command("pip install -r backend/requirements.txt"):
        return False
    
    print("Installing frontend dependencies...")
    if not run_command("npm install", cwd="frontend"):
        return False
    
    return True

def start_backend():
    print("\n=== Starting backend server ===")
    
    if sys.platform == 'win32':
        subprocess.Popen("python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000", shell=True)
    else:
        subprocess.Popen("python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000", shell=True)
    
    print("Backend server started on http://localhost:8000")
    return True

def main():
    print("=== AI Chatbot Automated Setup ===")
    print("This script will set up everything automatically.\n")
    
    if not setup_environment():
        print("Environment setup failed!")
        return
    
    if not install_dependencies():
        print("Dependency installation failed!")
        return
    
    if not setup_turso():
        print("Turso setup failed!")
        return
    
    github_repo = setup_github()
    if not github_repo:
        print("GitHub setup failed!")
        return
    
    if not setup_vercel(github_repo):
        print("Vercel deployment failed!")
        return
    
    print("\n=== Setup complete! ===")
    print("Your AI chatbot is now deployed!")
    print("\nTo start the backend locally:")
    print("  python -m uvicorn backend.main:app --reload")
    
    response = input("\nStart backend server now? (y/n): ")
    if response.lower() == 'y':
        start_backend()

if __name__ == "__main__":
    main()

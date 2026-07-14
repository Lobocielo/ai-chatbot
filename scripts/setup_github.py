import os
import base64
import requests
from typing import Optional

class GitHubSetup:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.api_url = 'https://api.github.com'
    
    def create_repository(self, name: str, description: str = "") -> Optional[str]:
        print(f"Creating repository: {name}")
        
        data = {
            'name': name,
            'description': description,
            'auto_init': False,
            'private': False
        }
        
        response = requests.post(
            f'{self.api_url}/user/repos',
            headers=self.headers,
            json=data
        )
        
        if response.status_code == 201:
            repo_url = response.json()['html_url']
            print(f"Repository created: {repo_url}")
            return repo_url
        else:
            print(f"Error creating repository: {response.text}")
            return None
    
    def create_file(self, owner: str, repo: str, path: str, content: str, message: str = "Initial commit"):
        print(f"Creating file: {path}")
        
        data = {
            'message': message,
            'content': base64.b64encode(content.encode()).decode()
        }
        
        response = requests.put(
            f'{self.api_url}/repos/{owner}/{repo}/contents/{path}',
            headers=self.headers,
            json=data
        )
        
        if response.status_code in [200, 201]:
            print(f"File created: {path}")
            return True
        else:
            print(f"Error creating file {path}: {response.text}")
            return False
    
    def upload_directory(self, owner: str, repo: str, directory: str, prefix: str = ""):
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.startswith('.') or file == 'node_modules':
                    continue
                
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, directory)
                remote_path = f"{prefix}/{relative_path}" if prefix else relative_path
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                self.create_file(owner, repo, remote_path, content)

def setup_github(token: str, repo_name: str, project_path: str):
    github = GitHubSetup(token)
    
    repo_url = github.create_repository(
        repo_name,
        "AI Chatbot with persistent memory and RAG"
    )
    
    if not repo_url:
        return None
    
    owner = token.split(':')[0] if ':' in token else requests.get(
        'https://api.github.com/user',
        headers={'Authorization': f'token {token}'}
    ).json()['login']
    
    github.upload_directory(owner, repo_name, project_path)
    
    print(f"GitHub setup complete: {repo_url}")
    return repo_url

if __name__ == "__main__":
    token = input("Enter your GitHub token: ")
    repo_name = input("Enter repository name: ")
    setup_github(token, repo_name, ".")

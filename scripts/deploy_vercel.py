import requests
import time
from typing import Optional

class VercelDeploy:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        self.api_url = 'https://api.vercel.com'
    
    def create_project(self, name: str, framework: str = "nextjs") -> Optional[str]:
        print(f"Creating Vercel project: {name}")
        
        data = {
            'name': name,
            'framework': framework
        }
        
        response = requests.post(
            f'{self.api_url}/v10/projects',
            headers=self.headers,
            json=data
        )
        
        if response.status_code in [200, 201]:
            project_id = response.json()['id']
            print(f"Project created: {project_id}")
            return project_id
        else:
            print(f"Error creating project: {response.text}")
            return None
    
    def deploy_from_github(self, project_id: str, github_repo: str, branch: str = "main") -> Optional[str]:
        print(f"Deploying from GitHub: {github_repo}")
        
        data = {
            'name': 'production',
            'source': {
                'type': 'github',
                'ref': branch,
                'repoId': github_repo
            }
        }
        
        response = requests.post(
            f'{self.api_url}/v13/deployments',
            headers=self.headers,
            json=data
        )
        
        if response.status_code in [200, 201]:
            deployment_id = response.json()['id']
            print(f"Deployment started: {deployment_id}")
            return deployment_id
        else:
            print(f"Error starting deployment: {response.text}")
            return None
    
    def get_deployment_status(self, deployment_id: str) -> dict:
        response = requests.get(
            f'{self.api_url}/v13/deployments/{deployment_id}',
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()
        return {}
    
    def wait_for_deployment(self, deployment_id: str, timeout: int = 300) -> bool:
        print("Waiting for deployment...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_deployment_status(deployment_id)
            state = status.get('state', 'unknown')
            
            print(f"Deployment state: {state}")
            
            if state == 'ready':
                url = status.get('url', '')
                print(f"Deployment complete: {url}")
                return True
            elif state in ['error', 'canceled']:
                print(f"Deployment failed: {state}")
                return False
            
            time.sleep(5)
        
        print("Deployment timeout")
        return False
    
    def set_environment_variable(self, project_id: str, key: str, value: str, environments: list = None):
        if environments is None:
            environments = ['production', 'preview', 'development']
        
        data = {
            'key': key,
            'value': value,
            'environments': environments
        }
        
        response = requests.post(
            f'{self.api_url}/v10/projects/{project_id}/env',
            headers=self.headers,
            json=data
        )
        
        if response.status_code in [200, 201]:
            print(f"Environment variable set: {key}")
            return True
        else:
            print(f"Error setting environment variable: {response.text}")
            return False

def deploy_vercel(token: str, project_name: str, github_repo: str):
    vercel = VercelDeploy(token)
    
    project_id = vercel.create_project(project_name)
    if not project_id:
        return None
    
    deployment_id = vercel.deploy_from_github(project_id, github_repo)
    if not deployment_id:
        return None
    
    if vercel.wait_for_deployment(deployment_id):
        print("Vercel deployment complete!")
        return project_id
    else:
        print("Vercel deployment failed!")
        return None

if __name__ == "__main__":
    token = input("Enter your Vercel token: ")
    project_name = input("Enter project name: ")
    github_repo = input("Enter GitHub repo (owner/repo): ")
    deploy_vercel(token, project_name, github_repo)

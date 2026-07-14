import requests
import json
from typing import Optional

class TursoSetup:
    def __init__(self, auth_token: str):
        self.auth_token = auth_token
        self.headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        self.api_url = 'https://api.turso.tech/v2/organizations'
    
    def get_organization(self) -> Optional[str]:
        print("Getting organization...")
        
        response = requests.get(
            f'{self.api_url}',
            headers=self.headers
        )
        
        if response.status_code == 200:
            orgs = response.json().get('organizations', [])
            if orgs:
                org_name = orgs[0]['name']
                print(f"Organization found: {org_name}")
                return org_name
        
        print("Error getting organization")
        return None
    
    def create_database(self, org_name: str, db_name: str) -> Optional[str]:
        print(f"Creating database: {db_name}")
        
        data = {
            'name': db_name,
            'group': 'default',
            'size_instance': 'free'
        }
        
        response = requests.post(
            f'{self.api_url}/{org_name}/databases',
            headers=self.headers,
            json=data
        )
        
        if response.status_code in [200, 201]:
            db_info = response.json()
            db_url = db_info.get('database', {}).get('url', '')
            print(f"Database created: {db_url}")
            return db_url
        else:
            print(f"Error creating database: {response.text}")
            return None
    
    def create_auth_token(self, org_name: str, db_name: str) -> Optional[str]:
        print(f"Creating auth token for {db_name}")
        
        response = requests.post(
            f'{self.api_url}/{org_name}/databases/{db_name}/auth/tokens',
            headers=self.headers
        )
        
        if response.status_code in [200, 201]:
            token = response.json().get('token', '')
            print(f"Auth token created")
            return token
        else:
            print(f"Error creating auth token: {response.text}")
            return None
    
    def execute_sql(self, db_url: str, auth_token: str, sql: str):
        print(f"Executing SQL: {sql[:50]}...")
        
        data = {
            'sql': sql
        }
        
        response = requests.post(
            f'{db_url}/v2/pipeline',
            headers={
                'Authorization': f'Bearer {auth_token}',
                'Content-Type': 'application/json'
            },
            json=data
        )
        
        if response.status_code == 200:
            print("SQL executed successfully")
            return True
        else:
            print(f"Error executing SQL: {response.text}")
            return False

def setup_turso(auth_token: str, db_name: str):
    turso = TursoSetup(auth_token)
    
    org_name = turso.get_organization()
    if not org_name:
        return None, None
    
    db_url = turso.create_database(org_name, db_name)
    if not db_url:
        return None, None
    
    token = turso.create_auth_token(org_name, db_name)
    if not token:
        return None, None
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS memoria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_input TEXT NOT NULL,
        response TEXT NOT NULL,
        embedding BLOB,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    turso.execute_sql(db_url, token, create_table_sql)
    
    print(f"Turso setup complete!")
    print(f"DB URL: {db_url}")
    print(f"Auth Token: {token[:20]}...")
    
    return db_url, token

if __name__ == "__main__":
    auth_token = input("Enter your Turso auth token: ")
    db_name = input("Enter database name: ")
    setup_turso(auth_token, db_name)

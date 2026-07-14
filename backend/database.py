import requests
import json
import os
from typing import List, Dict

class Database:
    def __init__(self):
        raw_url = os.getenv("TURSO_DB_URL", "")
        self.db_url = raw_url.replace("libsql://", "https://")
        self.auth_token = os.getenv("TURSO_AUTH_TOKEN", "")
    
    def _pipeline(self, statements):
        url = f"{self.db_url}/v2/pipeline"
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        resp = requests.post(url, headers=headers, json={"requests": statements})
        return resp.json()
    
    async def init_db(self):
        sql = """CREATE TABLE IF NOT EXISTS memoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_input TEXT NOT NULL,
            response TEXT NOT NULL,
            embedding BLOB,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )"""
        self._pipeline([{"type": "execute", "stmt": {"sql": sql}}])
    
    async def save_memory(self, user_input: str, response: str, embedding: List[float]):
        existing = await self.check_duplicate(user_input)
        if existing:
            return
        
        embedding_json = json.dumps(embedding) if embedding else None
        
        self._pipeline([{
            "type": "execute",
            "stmt": {
                "sql": "INSERT INTO memoria (user_input, response, embedding) VALUES (?, ?, ?)",
                "args": [{"type": "text", "value": user_input}, {"type": "text", "value": response}, {"type": "text", "value": embedding_json}]
            }
        }])
    
    async def check_duplicate(self, user_input: str) -> bool:
        result = self._pipeline([{
            "type": "execute",
            "stmt": {
                "sql": "SELECT COUNT(*) FROM memoria WHERE user_input = ?",
                "args": [{"type": "text", "value": user_input}]
            }
        }])
        try:
            rows = result["results"][0]["response"]["result"]["rows"]
            return rows[0][0] > 0
        except:
            return False
    
    async def get_all_memories(self) -> List[Dict]:
        result = self._pipeline([{
            "type": "execute",
            "stmt": {"sql": "SELECT user_input, response, embedding FROM memoria ORDER BY timestamp DESC LIMIT 100"}
        }])
        try:
            rows = result["results"][0]["response"]["result"]["rows"]
            memories = []
            for row in rows:
                embedding = json.loads(row[2]) if row[2] else None
                memories.append({
                    "user_input": row[0],
                    "response": row[1],
                    "embedding": embedding
                })
            return memories
        except:
            return []

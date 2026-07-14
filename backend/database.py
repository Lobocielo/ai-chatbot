import libsql_experimental as libsql
import os
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    def __init__(self):
        self.url = os.getenv("TURSO_DB_URL")
        self.auth_token = os.getenv("TURSO_AUTH_TOKEN")
        self.conn = None
    
    async def init_db(self):
        if self.url and self.auth_token:
            self.conn = libsql.connect(
                database=self.url,
                auth_token=self.auth_token
            )
        else:
            self.conn = libsql.connect("local.db")
        
        await self._create_tables()
    
    async def _create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_input TEXT NOT NULL,
                response TEXT NOT NULL,
                embedding BLOB,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
    
    async def save_memory(self, user_input: str, response: str, embedding: List[float]):
        import json
        
        existing = await self.check_duplicate(user_input)
        if existing:
            return
        
        embedding_json = json.dumps(embedding) if embedding else None
        
        self.conn.execute(
            "INSERT INTO memoria (user_input, response, embedding) VALUES (?, ?, ?)",
            [user_input, response, embedding_json]
        )
        self.conn.commit()
    
    async def check_duplicate(self, user_input: str) -> bool:
        cursor = self.conn.execute(
            "SELECT COUNT(*) FROM memoria WHERE user_input = ?",
            [user_input]
        )
        result = cursor.fetchone()
        return result[0] > 0
    
    async def get_all_memories(self) -> List[Dict]:
        import json
        
        cursor = self.conn.execute(
            "SELECT user_input, response, embedding FROM memoria ORDER BY timestamp DESC LIMIT 100"
        )
        rows = cursor.fetchall()
        
        memories = []
        for row in rows:
            embedding = json.loads(row[2]) if row[2] else None
            memories.append({
                "user_input": row[0],
                "response": row[1],
                "embedding": embedding
            })
        
        return memories

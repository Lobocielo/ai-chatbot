import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict
import logging

from .database import Database

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models", "all-MiniLM-L6-v2"
)

class RAGSystem:
    def __init__(self):
        logger.info(f"Loading model from: {MODEL_PATH}")
        self.model = SentenceTransformer(MODEL_PATH)
        self.db = Database()
        self.top_k = 5
        logger.info("Model loaded successfully")
    
    async def get_embedding(self, text: str) -> List[float]:
        embedding = self.model.encode(text)
        return embedding.tolist()
    
    async def retrieve_context(self, query: str) -> List[Dict]:
        query_embedding = await self.get_embedding(query)
        memories = await self.db.get_all_memories()
        
        if not memories:
            return []
        
        similarities = []
        for memory in memories:
            if memory['embedding']:
                sim = self._cosine_similarity(query_embedding, memory['embedding'])
                similarities.append((memory, sim))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_results = similarities[:self.top_k]
        
        return [
            {
                "user_input": m[0]['user_input'],
                "response": m[0]['response'],
                "score": float(m[1])
            }
            for m in top_results
            if m[1] > 0.3
        ]
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        a = np.array(a)
        b = np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    
    async def generate_response(self, query: str, context: List[Dict]) -> str:
        if context:
            context_text = "\n".join([
                f"Usuario: {c['user_input']}\nRespuesta: {c['response']}"
                for c in context
            ])
            return f"Basado en conversaciones previas:\n{context_text}\n\nTu pregunta: {query}"
        
        return f"Recibido tu mensaje: {query}"

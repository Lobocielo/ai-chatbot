from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict
import os

from .database import Database

class RAGSystem:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.db = Database()
        self.top_k = 5
    
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
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    async def generate_response(self, query: str, context: List[Dict]) -> str:
        if context:
            context_text = "\n".join([
                f"Usuario: {c['user_input']}\nRespuesta: {c['response']}"
                for c in context
            ])
            prompt = f"Contexto de conversaciones anteriores:\n{context_text}\n\nPregunta actual: {query}\n\nRespuesta:"
        else:
            prompt = f"Pregunta: {query}\n\nRespuesta:"
        
        # Placeholder para integración con modelo de IA
        # En producción, aquí iría la llamada al modelo
        return f"Respuesta generada para: {query}"

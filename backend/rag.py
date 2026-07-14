import os
import re
import random
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

SALUDOS = ["hola", "hey", "buenas", "que tal", "buenos dias", "buenas tardes", "buenas noches", "saludos", "que onda", "que hay"]
DESPEDIDAS = ["chau", "adios", "hasta luego", "nos vemos", "bye", "me voy", "hasta pronto"]
AGRADECIMIENTOS = ["gracias", "te agradezco", "mil gracias", "thanks", "merci"]
PROGRAMACION = ["programar", "codigo", "python", "javascript", "html", "css", "react", "nextjs", "api", "backend", "frontend", "desarrollo"]
PREGUNTAS_QUE = ["que es", "que son", "que hace", "que significa", "define"]
PREGUNTAS_COMO = ["como se", "como hacer", "como puedo", "como funciona", "como work"]
PREGUNTAS_PORQUE = ["porque", "por que", "razon", "causa"]
PREGUNTAS_DONDE = ["donde", "ubicacion", "lugar"]
PREGUNTAS_CUANTO = ["cuanto", "cuanta", "cuantos", "cuantas", "precio", "costo"]

def detectar_tipo(texto):
    t = texto.lower().strip()
    if any(p in t for p in SALUDOS):
        return "saludo"
    if any(p in t for p in DESPEDIDAS):
        return "despedida"
    if any(p in t for p in AGRADECIMIENTOS):
        return "agradecimiento"
    if any(p in t for p in PREGUNTAS_QUE):
        return "que"
    if any(p in t for p in PREGUNTAS_COMO):
        return "como"
    if any(p in t for p in PREGUNTAS_PORQUE):
        return "porque"
    if any(p in t for p in PREGUNTAS_DONDE):
        return "donde"
    if any(p in t for p in PREGUNTAS_CUANTO):
        return "cuanto"
    if any(p in t for p in PROGRAMACION):
        return "programacion"
    if "?" in t:
        return "pregunta"
    return "general"

RESPUESTAS_SALUDO = [
    "Hola! En que puedo ayudarte?",
    "Hey! Que gusto verte. En que puedo asistirte?",
    "Buenas! Soy tu chatbot con IA. Preguntame lo que quieras.",
    "Hola! Bienvenido. Tengo memoria de nuestras conversaciones anteriores.",
]
RESPUESTAS_DESPEDIDA = [
    "Hasta luego! Fue charlar contigo.",
    "Nos vemos! Recorda que guardo todo en mi memoria.",
    "Adios! Volve cuando quieras.",
]
RESPUESTAS_AGRADECIMIENTO = [
    "De nada! Para eso estoy.",
    "No hay de que! Si necesitas algo mas, avisame.",
    "Con gusto! Estoy para ayudarte.",
]
RESPUESTAS_PROGRAMACION = [
    "Interesante tema la programacion! Actualmente trabajo con Python y Next.js. Que especifico quisieras saber?",
    "La programacion es genial! Puedo ayudarte con conceptos, codigo, o explicar funciones. Que necesitas?",
    "Me encanta hablar de codigo! Puedo explicar desde conceptos basicos hasta arquitecturas complejas.",
]
RESPUESTAS_QUE = [
    "Buena pregunta! Sin mas contexto, puedo decirte que es un tema amplio. Queres que profundice en algo especifico?",
    "Mmm, eso depende del contexto. Podes darme mas detalles para darte una mejor respuesta?",
]
RESPUESTAS_PREGUNTA = [
    "Buena pregunta! Lamentablemente soy un chatbot basado en embeddings, pero puedo guardar contexto de nuestras charlas y recuperar informacion relevante. Que te gustaria saber?",
    "Interesante pregunta! Mis respuestas mejoran con mas conversaciones. Contame mas sobre lo que queres saber.",
]
RESPUESTAS_GENERAL = [
    "Entendido! Guardo esto en mi memoria. Si tenes alguna pregunta, decime.",
    "Interesante! Lo tengo en cuenta. En que mas puedo ayudarte?",
    "Recibido! Mi memoria RAG guarda esto para futuras referencias. Algo mas?",
]

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
        tipo = detectar_tipo(query)
        
        if tipo == "saludo":
            respuesta = random.choice(RESPUESTAS_SALUDO)
        elif tipo == "despedida":
            respuesta = random.choice(RESPUESTAS_DESPEDIDA)
        elif tipo == "agradecimiento":
            respuesta = random.choice(RESPUESTAS_AGRADECIMIENTO)
        elif tipo == "programacion":
            respuesta = random.choice(RESPUESTAS_PROGRAMACION)
        elif tipo in ("que", "como", "porque", "donde", "cuanto"):
            respuesta = random.choice(RESPUESTAS_QUE)
        elif tipo == "pregunta":
            respuesta = random.choice(RESPUESTAS_PREGUNTA)
        else:
            respuesta = random.choice(RESPUESTAS_GENERAL)
        
        if context:
            ctx = context[0]
            sim = ctx['score']
            if sim > 0.7:
                respuesta += f"\n\n[Memoria RAG] Encontre una conversacion muy similar (similitud: {sim:.0%}): \"{ctx['user_input']}\""
            elif sim > 0.5:
                respuesta += f"\n\n[Memoria RAG] Tengo algo relacionado en mi memoria (similitud: {sim:.0%}): \"{ctx['user_input']}\""
        
        return respuesta

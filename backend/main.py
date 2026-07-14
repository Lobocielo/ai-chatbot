import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from dotenv import load_dotenv
load_dotenv("config/.env")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Chatbot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    user_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[dict]] = None

rag = None
db = None

@app.on_event("startup")
async def startup():
    global rag, db
    logger.info("Starting up...")
    from .database import Database
    from .rag import RAGSystem
    db = Database()
    await db.init_db()
    logger.info("Database initialized")
    try:
        rag = RAGSystem()
        logger.info("RAG system ready")
    except Exception as e:
        logger.error(f"RAG init failed: {e}")
        rag = None

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        if rag is None:
            return ChatResponse(response=f"Backend respondiendo a: {request.message}", sources=[])
        
        context = await rag.retrieve_context(request.message)
        response = await rag.generate_response(request.message, context)
        
        await db.save_memory(
            user_input=request.message,
            response=response,
            embedding=await rag.get_embedding(request.message)
        )
        
        return ChatResponse(response=response, sources=context)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}

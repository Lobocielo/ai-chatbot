from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from datetime import datetime

from .rag import RAGSystem
from .database import Database

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

rag = RAGSystem()
db = Database()

@app.on_event("startup")
async def startup():
    await db.init_db()

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        context = await rag.retrieve_context(request.message)
        response = await rag.generate_response(request.message, context)
        
        await db.save_memory(
            user_input=request.message,
            response=response,
            embedding=await rag.get_embedding(request.message)
        )
        
        return ChatResponse(response=response, sources=context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}

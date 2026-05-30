from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from backend.models.video import VideoProcessingRequest, ChatRequest, VideoMetadata
from backend.services.video_service import VideoService
from backend.services.rag_service import RAGService
from langchain_core.messages import HumanMessage, AIMessage
from typing import Dict, List, Any
import uvicorn
import os
import json

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for session data
sessions: Dict[str, Dict[str, Any]] = {}

video_service = VideoService()
rag_service = RAGService()

import asyncio

@app.post("/process")
async def process_videos(request: VideoProcessingRequest):
    print(f"Received process request for: {request.video_a_url} and {request.video_b_url}")
    try:
        # 1. Get metadata (required for both paths)
        meta_a = None
        meta_b = None
        
        print("Fetching metadata...")
        meta_tasks = []
        # Check if URL is real or manual placeholder
        is_real_a = request.video_a_url and "manual.video" not in request.video_a_url
        is_real_b = request.video_b_url and "manual.video" not in request.video_b_url

        if is_real_a:
            meta_tasks.append(video_service.get_video_info(request.video_a_url))
        else:
            meta_tasks.append(asyncio.sleep(0, result=VideoMetadata(
                video_id="manual_a", platform="manual", url=request.video_a_url or "", title="Manual Video A", engagement_rate=0.0
            )))

        if is_real_b:
            meta_tasks.append(video_service.get_video_info(request.video_b_url))
        else:
            meta_tasks.append(asyncio.sleep(0, result=VideoMetadata(
                video_id="manual_b", platform="manual", url=request.video_b_url or "", title="Manual Video B", engagement_rate=0.0
            )))

        meta_a, meta_b = await asyncio.gather(*meta_tasks)
        print(f"Metadata fetched: {meta_a.title}, {meta_b.title}")

        # 2. Get transcripts
        transcript_a = request.video_a_transcript
        transcript_b = request.video_b_transcript

        print(f"Transcripts provided manually: A={bool(transcript_a)}, B={bool(transcript_b)}")
        
        print("Fetching transcripts...")
        tasks = []
        if not transcript_a and is_real_a:
            print("Extracting transcript A from URL...")
            tasks.append(video_service.get_transcript(request.video_a_url, meta_a.video_id))
        else:
            tasks.append(asyncio.sleep(0, result=transcript_a or "No transcript provided."))

        if not transcript_b and is_real_b:
            print("Extracting transcript B from URL...")
            tasks.append(video_service.get_transcript(request.video_b_url, meta_b.video_id))
        else:
            tasks.append(asyncio.sleep(0, result=transcript_b or "No transcript provided."))

        results = await asyncio.gather(*tasks)
        transcript_a = results[0]
        transcript_b = results[1]
        print(f"Transcripts ready. Lengths: A={len(transcript_a)}, B={len(transcript_b)}")
        
        # 3. Index transcripts
        print("Indexing transcripts...")
        rag_service.process_videos(
            meta_a.dict(), 
            meta_b.dict(), 
            transcript_a, 
            transcript_b
        )
        print("Indexing complete.")
        
        # 4. Create session
        session_id = f"{meta_a.video_id}_{meta_b.video_id}"
        sessions[session_id] = {
            "video_context": {
                "A": meta_a.dict(),
                "B": meta_b.dict()
            },
            "history": []
        }
        
        return {
            "session_id": session_id,
            "video_a": meta_a,
            "video_b": meta_b
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(request: ChatRequest):
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[request.session_id]
    
    async def event_generator():
        full_response = ""
        try:
            print(f"Starting chat stream for session {request.session_id}...")
            async for chunk in rag_service.chat_stream(
                request.message, 
                session["history"], 
                session["video_context"]
            ):
                full_response += chunk
                yield chunk
            print(f"Chat stream completed for session {request.session_id}.")
        except Exception as e:
            print(f"Error in chat stream: {str(e)}")
            yield f"\n\n[Error: {str(e)}]"
        
        # After stream ends, update history
        session["history"].append(HumanMessage(content=request.message))
        session["history"].append(AIMessage(content=full_response))

    return StreamingResponse(event_generator(), media_type="text/plain")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

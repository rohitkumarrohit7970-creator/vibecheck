import os
from typing import List, Dict, Any, TypedDict, Annotated, AsyncGenerator
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv

load_dotenv()

# Define the state for LangGraph
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "The messages in the conversation"]
    video_context: Dict[str, Any]
    retrieved_docs: List[Document]
    video_id_a: str
    video_id_b: str

class RAGService:
    def __init__(self):
        # We switch to open-source BGE embeddings to remove dependency on OpenAI.
        # BAAI/bge-small-en-v1.5 is one of the best small embedding models.
        print("Initializing embeddings model...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        # Force download/load by embedding a dummy text
        self.embeddings.embed_query("warmup")
        print("Embeddings model ready.")
        
        # We use Groq for the LLM - Llama 3.3 70B for high-quality comparisons.
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            streaming=True
        )
        
        # Use an absolute path for the vector database to avoid permission/path issues
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.vector_db_path = os.path.join(base_dir, "chroma_db")
        
        # Ensure the directory exists and is writable
        if not os.path.exists(self.vector_db_path):
            os.makedirs(self.vector_db_path, exist_ok=True)
            
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

    def process_videos(self, video_a_meta: Dict, video_b_meta: Dict, transcript_a: str, transcript_b: str):
        # Create documents
        docs = []
        
        # Add transcript A chunks
        chunks_a = self.text_splitter.split_text(transcript_a)
        for i, chunk in enumerate(chunks_a):
            docs.append(Document(
                page_content=chunk,
                metadata={"video_id": "A", "id": video_a_meta['video_id'], "title": video_a_meta['title']}
            ))
            
        # Add transcript B chunks
        chunks_b = self.text_splitter.split_text(transcript_b)
        for i, chunk in enumerate(chunks_b):
            docs.append(Document(
                page_content=chunk,
                metadata={"video_id": "B", "id": video_b_meta['video_id'], "title": video_b_meta['title']}
            ))
            
        # If no documents were created (e.g., transcripts are empty), add a placeholder
        if not docs:
            docs.append(Document(
                page_content="No transcript content available for these videos.",
                metadata={"video_id": "N/A", "id": "none", "title": "None"}
            ))

        # Store in Chroma
        if os.path.exists(self.vector_db_path):
            import shutil
            shutil.rmtree(self.vector_db_path)
            
        self.vector_db = Chroma.from_documents(
            documents=docs,
            embedding=self.embeddings,
            persist_directory=self.vector_db_path
        )
        return self.vector_db

    def get_retriever(self):
        if not hasattr(self, 'vector_db'):
            self.vector_db = Chroma(persist_directory=self.vector_db_path, embedding_function=self.embeddings)
        return self.vector_db.as_retriever(search_kwargs={"k": 5})

    async def chat_stream(self, message: str, history: List[BaseMessage], video_context: Dict) -> AsyncGenerator[str, None]:
        retriever = self.get_retriever()
        docs = await retriever.ainvoke(message)
        
        # If no documents are found, provide a graceful fallback
        if not docs:
            context = "No specific transcript segments found for this query. Use the provided metadata for comparison."
        else:
            context = "\n\n".join([f"[Source: Video {d.metadata['video_id']}] {d.page_content}" for d in docs])
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert social media analyst specializing in content strategy and performance. 
            Your goal is to provide a deep, data-driven comparison between Video A and Video B.
            
            METADATA:
            Video A: {video_a_meta}
            Video B: {video_b_meta}
            
            TRANSCRIPT CONTEXT:
            {context}
            
            ANALYSIS GUIDELINES:
            1. Start by directly answering the user's question using the available data.
            2. Compare engagement rates: Video A ({engagement_rate_a}%) vs Video B ({engagement_rate_b}%). Explain what this might imply about the content's resonance.
            3. Use the transcript context to compare hooks, key arguments, or presentation styles.
            4. Be objective and professional. Always cite which video (A or B) a piece of information comes from.
            5. If transcript data is missing for a specific point, rely on the titles and hashtags from the metadata.
            """),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ])
        
        chain = prompt | self.llm
        
        async for chunk in chain.astream({
            "video_a_meta": video_context['A'],
            "video_b_meta": video_context['B'],
            "engagement_rate_a": video_context['A'].get('engagement_rate', 0),
            "engagement_rate_b": video_context['B'].get('engagement_rate', 0),
            "context": context,
            "history": history,
            "input": message
        }):
            if chunk.content:
                yield chunk.content

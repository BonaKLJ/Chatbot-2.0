import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from config import OLLAMA_MODEL, OLLAMA_URL
from rag.retriever import retrieve_relevant_chunks

app = FastAPI(title="Chatbot 2.0 Backend")

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    # Retrieve top 4 relevant chunks from the database
    chunks = retrieve_relevant_chunks(request.message, top_k=4)
    if not chunks:
        return {"reply": "I couldn't find anything relevant in the documents."}

    # Join relevant chunks as context
    context = "\n\n---\n\n".join(chunks)

    # Build prompt
    prompt = (
        "If the user's message is a greeting or small talk (like \"hi\", \"hello\", \"how are you\", \"thanks\"), "
        "reply with a short, friendly response and mention that you can answer questions about Heng Bunyi's resume. "
        "Do not say \"I don't know\" to greetings.\n"
        "For any other question, answer using ONLY the provided context. "
        "If the answer is not in the context, say you don't have that information in the resume.\n"
        "When asked for an overview or summary of the person, include education, all work experience, and skills from the context.\n\n"
        f"Context:\n{context}\n\n"
        f"Question:\n{request.message}\n\n"
        "Answer:"
    )

    # Send prompt to Ollama model
    try:
        response = requests.post(
            OLLAMA_URL + "/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        )
        if response.status_code != 200:
            return {
                "reply": "Error: could not reach the language model. Check that the Kaggle notebook and ngrok tunnel are running."
            }

        data = response.json()
        return {"reply": data.get("response", "")}
    except requests.RequestException:
        return {
            "reply": "Error: could not reach the language model. Check that the Kaggle notebook and ngrok tunnel are running."
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

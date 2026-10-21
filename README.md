# Chatbot 2.0

Chatbot 2.0 is a Retrieval-Augmented Generation (RAG) chatbot designed to answer questions accurately about a resume. It retrieves relevant text chunks from a PostgreSQL vector database and generates context-grounded answers using an LLM hosted remotely.

## Architecture

```text
Browser UI -> FastAPI backend -> pgvector retrieval (PostgreSQL) -> Ollama (Gemma3:4b) running on a Kaggle GPU through an ngrok tunnel -> answer back to the UI
```

```text
+-----------------------+
|      Browser UI       |
|   (HTML / CSS / JS)   |
+-----------+-----------+
            |  POST /chat (JSON)
            v
+-----------------------+
|    FastAPI Backend    |
|   (Uvicorn :8000)     |
+-----+-----------+-----+
      |           |
      | 1. Query  | 2. Top-k Chunks
      v           |
+-----------------+-----+
|     PostgreSQL 18     |
|   + pgvector (384d)   |
+-----------------------+
      |
      | 3. Context + Prompt
      v
+-----------------------+
|     ngrok Tunnel      |
+-----------+-----------+
            |
            v
+-----------------------+
|  Kaggle GPU Instance  |
|  Ollama (Gemma3:4b)   |
+-----------------------+
```

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Uvicorn, Requests
- **Database & Vector Search**: PostgreSQL 18 + `pgvector` extension
- **Embeddings**: `sentence-transformers` (`all-MiniLM-L6-v2`, 384 dimensions)
- **Text Chunking**: Custom recursive text chunker (chunk size: 500 characters, overlap: 50 characters)
- **LLM**: Ollama with `gemma3:4b` running on a Kaggle GPU
- **Tunneling**: ngrok (`pyngrok`)
- **Frontend**: Plain HTML5, CSS3, and vanilla JavaScript (Fetch API)

## Project Structure

```text
ChatBot2/
├── backend/
│   ├── db/
│   │   ├── __init__.py
│   │   ├── connection.py        # SQLAlchemy engine and session dependency
│   │   └── models.py            # Document model with pgvector Vector(384)
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── chunker.py           # Recursive text chunking implementation
│   │   ├── ingest.py            # Ingestion script for parsing & embedding .txt files
│   │   └── retriever.py         # Cosine-similarity chunk retriever
│   ├── .env.example             # Template for environment variables
│   ├── config.py                # Environment configuration loader
│   ├── main.py                  # FastAPI application and /chat endpoint
│   └── requirements.txt         # Python dependencies
├── data/
│   ├── examples/
│   │   └── sample_resume.txt    # Provided sample resume for testing
│   └── <your_resume>.txt        # Ingested resume file (.txt directly in data/)
├── frontend/
│   ├── index.html               # Chat interface markup
│   ├── script.js                # Chat logic, message rendering, and API calls
│   └── style.css                # Styling and responsive layout
└── README.md
```

## Setup

### 1. Install PostgreSQL and pgvector

Ensure PostgreSQL 18 and the `pgvector` extension are installed on your system.

On Debian/Ubuntu:
```bash
sudo apt update
sudo apt install postgresql-18 postgresql-18-pgvector
```

### 2. Create the Database and Schema

Log into PostgreSQL using `psql` and run the following commands to create the database, user, schema, and vector extension:

```sql
CREATE DATABASE chatbot_db;
CREATE USER your_db_user WITH ENCRYPTED PASSWORD 'your_db_password';
GRANT ALL PRIVILEGES ON DATABASE chatbot_db TO your_db_user;

\c chatbot_db

CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS chatbot2;
GRANT ALL ON SCHEMA chatbot2 TO your_db_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA chatbot2 TO your_db_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA chatbot2 GRANT ALL ON TABLES TO your_db_user;
```

> **Note**: The backend database connection sets `search_path=chatbot2,public` via connection options in `backend/db/connection.py`.

### 3. Create Python Virtual Environment

From the project root, navigate to `backend/`, create a virtual environment, and install dependencies:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file and update the variables with your database credentials and ngrok tunnel URL:

```bash
cp .env.example .env
```

Edit `backend/.env`:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=chatbot_db
DB_SCHEMA=chatbot2
DB_USER=your_db_user
DB_PASSWORD=your_db_password
OLLAMA_URL=https://your-ngrok-url.ngrok-free.dev
OLLAMA_MODEL=gemma3:4b
```

### 5. Ingest Resume Data

Place your resume as a `.txt` file directly inside the `data/` folder. A mock resume is provided in `data/examples/sample_resume.txt` for reference or testing:

```bash
# Example using the sample resume
cp ../data/examples/sample_resume.txt ../data/resume.txt
```

> **Note**: The ingestion script only processes `.txt` files located directly inside `data/` (subdirectories like `examples/` are ignored).

Run the ingestion script from the `backend/` directory:

```bash
python rag/ingest.py
```

This clears previous entries in the `chatbot2.documents` table, chunks the text (size 500, overlap 50), generates 384-dimensional embeddings using `all-MiniLM-L6-v2`, and stores them in PostgreSQL. The `chatbot2.documents` table is created automatically on the first ingest run.

## Kaggle + ngrok Setup

Run Ollama and the `gemma3:4b` model on a free Kaggle GPU notebook (ensure **GPU accelerator** is enabled and **Internet** is toggled ON under Notebook Settings).

Execute the following notebook cells:

### Cell 1: Install Dependencies & Ollama
```bash
!apt-get update && apt-get install -y zstd
!curl -fsSL https://ollama.com/install.sh | sh
```

### Cell 2: Start Ollama Server
```python
import subprocess, time
subprocess.Popen(["ollama", "serve"])
time.sleep(5)
```

### Cell 3: Pull Model
```bash
!ollama pull gemma3:4b
```

### Cell 4: Expose Ollama via ngrok
```python
!pip install pyngrok

from pyngrok import ngrok

# Authenticate with your personal ngrok authtoken
ngrok.set_auth_token("YOUR_NGROK_AUTHTOKEN")

# Expose port 11434 with host_header override
public_tunnel = ngrok.connect(11434, host_header="localhost:11434")
print("Public Ollama URL:", public_tunnel.public_url)
```

> **Important**:
> - The `host_header="localhost:11434"` parameter is required to prevent Ollama from rejecting requests with a `403 Forbidden` error.
> - The public ngrok URL changes with every Kaggle session. Copy the generated `https://...` URL into `OLLAMA_URL` in `backend/.env` each time you restart the notebook.

## Running the Application

### 1. Start the Backend API

From the `backend/` directory with the virtual environment activated:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The FastAPI server will start on `http://0.0.0.0:8000`.

### 2. Open the Frontend

Open `frontend/index.html` in your web browser (or serve it using any static file server). The interface connects to `http://localhost:8000/chat`.

## Notes and Limitations

- **Session Expiry**: Free Kaggle notebook sessions are subject to timeout and will expire after a period of inactivity or reaching maximum runtime limits.
- **Model Warm-up**: The very first query sent to the model may take approximately one minute while Gemma 3 loads into GPU memory. Subsequent requests respond much faster.
- **Strict Context Grounding**: The chatbot is prompted to answer strictly based on the ingested resume text. If information is not in the ingested document, it will inform the user that it does not have that information.

## Roadmap

- **Docker Support**: Containerize the FastAPI backend and PostgreSQL database with Docker Compose for single-command setup.
- **Reranker**: Integrate a re-ranking model (such as a cross-encoder) to refine chunk ordering before passing context to the LLM.

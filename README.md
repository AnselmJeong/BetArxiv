# Betarxiv

## Research Paper Knowledge Extraction API

A FastAPI-based service for extracting, summarizing, and searching research papers using LLMs, with PostgreSQL storage and directory monitoring.

## Features

- Upload and process research papers (PDFs)
- Extract metadata and generate summaries using LLMs (Ollama)
- Store all data and embeddings in PostgreSQL (with pgvector)
- Monitor a directory for new papers and process them automatically
- Search, browse, and find similar papers via API

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Ollama and Pull Model

```bash
ollama serve
ollama pull llama3.2
```

### 3. Configure PostgreSQL

- Enable the `pgvector` extension:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

- Create the schema:

```bash
psql <your_db_url> -f app/schema.sql
```

### 4. Run the API

```bash
python -m app.main --directory /path/to/papers --db-url postgresql://user:pass@localhost:5432/dbname
```

Or, for development with auto-reload:

```bash
uvicorn app.main:app --reload
```

### 5. Access the API

Visit [http://localhost:8000/docs](http://localhost:8000/docs) for the interactive API docs.

---

## CLI Options

- `--directory`: Directory to monitor for PDFs (default: current directory)
- `--db-url`: PostgreSQL connection string

---

## Environment Variables

You can also set `DIRECTORY` and `DATABASE_URL` in a `.env` file.

---




# How to setup the app

To test your Research Paper Knowledge Extraction API, follow these steps:

---

## 1. **Install All Dependencies**

```bash
pip install -r requirements.txt
```

---

## 2. **Start Ollama and Pull the Model**

Make sure [Ollama](https://ollama.com/) is running and the model is pulled:

```bash
ollama serve
ollama pull llama3.2
```

---

## 3. **Set Up PostgreSQL**

- Make sure PostgreSQL is running.
- Enable the `pgvector` extension and create the schema:

```bash
psql <your_db_url> -c "CREATE EXTENSION IF NOT EXISTS vector;"
psql <your_db_url> -f app/schema.sql
```

Replace `<your_db_url>` with your actual connection string, e.g.:
```
postgresql://user:password@localhost:5432/yourdbname
```

---

## 4. **Run the FastAPI App**

You can run the app in two ways:

### a) **With Python CLI (directory monitoring enabled):**

```bash
python -m app.main --directory /path/to/your/papers --db-url postgresql://user:password@localhost:5432/yourdbname
```

### b) **With Uvicorn (for development, hot reload):**

```bash
uvicorn app.main:app --reload
```

---

## 5. **Access the API Docs**

Open your browser and go to:

```
http://localhost:8000/docs
```

You will see the interactive Swagger UI where you can test all endpoints.

---

## 6. **Test the Endpoints**

### a) **Upload a Paper**

- Use the `/papers/upload` endpoint in the docs.
- Upload a PDF file.
- You should get a response with the paper’s metadata and ID.

### b) **List Papers**

- Use `/papers` to see all processed papers.

### c) **Get Paper Details**

- Use `/papers/{id}` with a valid paper ID.

### d) **Find Similar Papers**

- Use `/papers/{id}/similar` with a valid paper ID.

### e) **Trigger Directory Processing**

- Use `/papers/process-directory` to process all PDFs in the monitored directory.

### f) **Check Processing Status**

- Use `/papers/status` to see how many papers are processed, pending, or errored.

---

## 7. **Monitor Logs**

- The app logs to the console. Check for errors or status updates as you test.

---

## 8. **Directory Monitoring**

- If you add new PDFs to the monitored directory, the app will automatically process them in the background.

---

## 9. **Troubleshooting**

- If you get errors, check:
  - Ollama is running and the model is pulled.
  - PostgreSQL is running and the schema is created.
  - The database URL is correct.
  - The PDF files are valid and not corrupted.

---

**You can use tools like [httpie](https://httpie.io/) or `curl` for command-line testing, or just use the Swagger UI at `/docs`.**

If you want example `curl` commands or a Postman collection, let me know!

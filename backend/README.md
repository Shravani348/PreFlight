# PreFlight Backend

1. **What the backend does**
   A minimal FastAPI backend that provides the basic project structure and foundation for the PreFlight hackathon project.

2. **Installation command**
   ```bash
   pip install -r requirements.txt
   ```

3. **How to start the server**
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```

4. **Health endpoint**
   `GET /health`

5. **Swagger URL**
   http://127.0.0.1:8000/docs

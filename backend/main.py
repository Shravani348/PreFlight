from fastapi import FastAPI

app = FastAPI(title="PreFlight Backend")

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "PreFlight Backend"
    }

from fastapi import FastAPI

from umbrella_server.core.config import Settings


app = FastAPI()

@app.get('/health')
async def check_health():
    settings = Settings()
    return {"status": "ok"}
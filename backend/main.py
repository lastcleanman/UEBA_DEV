import sys
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ⭐️ 라우터 임포트 부분에 `system` 추가!
from backend.core.api.routers import pipeline, analytics, system, license, roadmap

app = FastAPI(title="UEBA Enterprise API Server", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ⭐️ 라우터 등록 부분에 `system.router` 추가!
app.include_router(pipeline.router)
app.include_router(analytics.router)
app.include_router(system.router) 
app.include_router(license.router)
app.include_router(roadmap.router)

@app.get("/")
def health_check():
    return {"status": "online"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
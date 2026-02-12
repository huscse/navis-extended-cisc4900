from fastapi import FastAPI

from backend.routes.datasets import router as datasets_router
from backend.routes.sequences import router as sequences_router
from backend.routes.frames import router as frames_router
from backend.routes.media import router as media_router
from backend.routes.search import router as search_router   
from backend.routes.caption import router as caption_router


app = FastAPI()

@app.get("/")
def root():
    return {"status": "Navis backend running"}

from fastapi.middleware.cors import CORSMiddleware

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(datasets_router, prefix="/datasets")
app.include_router(sequences_router, prefix="/sequences")
app.include_router(frames_router,    prefix="/frames")
app.include_router(media_router)
app.include_router(search_router) 
app.include_router(caption_router)


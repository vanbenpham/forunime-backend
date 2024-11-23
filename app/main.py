from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import models
from .database import engine
from .routers import auth, user, post, comment, thread, review
from .config import settings

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(post.router)
app.include_router(comment.router)
app.include_router(thread.router)
app.include_router(review.router)

@app.get("/")
def read_root():
    return {"Hello": "World"}

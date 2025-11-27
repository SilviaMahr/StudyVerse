#fast api starting point
#frontend is deployed on localhost:4200
#backend is deployed on localhost:8000
#nice to have - install docker container composition?

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware #needed for angular connection
#package imports:
from .routes import auth_routes
from .routes import planning_routes
from .routes import profile_routes
from .routes import chat_routes
from .db import init_db_pool, close_db_pool
#lifespan event handler
from contextlib import asynccontextmanager


# lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Startup was successful")
    await init_db_pool()
    yield
    print("Shutdown initiated")
    await close_db_pool()

app = FastAPI(title="StudyVerse Backend", lifespan=lifespan)

# Allow CORS for Angular (Cross Origin Resource Sharing ->
# ensures backend/frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  #frontend server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# register routes
app.include_router(auth_routes.router)
app.include_router(planning_routes.router)
app.include_router(profile_routes.router)
app.include_router(chat_routes.router)

@app.get("/")
async def root():
    return {"message": "StudyVerse API is running"}

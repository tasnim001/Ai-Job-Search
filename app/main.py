from fastapi import FastAPI
from app.controllers import search_controller

app = FastAPI(title="Matchmaker Service")

# Register routers
app.include_router(search_controller.router)

@app.get("/")
def root():
    return {"message": "Matchmaker Service is running!"}

@app.get("/job")
def get_job():
    return {"message": "Job is running!"}

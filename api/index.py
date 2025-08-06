from fastapi import FastAPI
from mangum import Mangum

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from Vercel + FastAPI"}

# This is needed for Vercel serverless to understand the app
handler = Mangum(app)

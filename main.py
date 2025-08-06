import os
import requests
from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import google.generativeai as genai
import httpx

load_dotenv()

app = FastAPI()

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

@app.post("/gemini")
async def call_gemini(request: Request):
    body = await request.json()
    prompt = body.get("prompt")

    if not prompt:
        return {"error": "Prompt is required."}

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={os.getenv('GEMINI_API_KEY')}"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json={"contents": [{"parts": [{"text": prompt}]}]},
            headers={"Content-Type": "application/json"}
        )
    return response.json()

@app.get("/search_jobs")
def search_jobs(query: str = Query(...), location: str = "India"):
    jobs = []

    # --- First: Try Adzuna ---
    adzuna_url = f"https://api.adzuna.com/v1/api/jobs/in/search/1"
    adzuna_params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": 50,
        "what": query,
        "where": location,
        "content-type": "application/json",
    }
    adzuna_response = requests.get(adzuna_url, params=adzuna_params)
    if adzuna_response.status_code == 200:
        adzuna_data = adzuna_response.json()
        for job in adzuna_data.get("results", []):
            jobs.append({
                "title": job.get("title"),
                "company": job.get("company", {}).get("display_name"),
                "location": job.get("location", {}).get("display_name"),
                "description": job.get("description"),
                "redirect_url": job.get("redirect_url"),
                "source": "Adzuna"
            })

    # --- If Adzuna gives 0 jobs, fallback to JSearch ---
    if not jobs:
        url = "https://jsearch.p.rapidapi.com/search"
        querystring = {
            "query": query,
            "num_pages": "1",
        }
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            result = response.json()
            for job in result.get("data", []):
                jobs.append({
                    "title": job.get("job_title"),
                    "company": job.get("employer_name"),
                    "location": job.get("job_city") or "N/A",
                    "description": job.get("job_description"),
                    "redirect_url": job.get("job_apply_link") or job.get("job_google_link"),
                    "source": "JSearch"
                })

    # Final response
    if jobs:
        return {"jobs": jobs}
    else:
        return {"jobs": [], "note": "No job results found. Try using broader keywords or changing the location."}


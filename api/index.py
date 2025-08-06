from fastapi import FastAPI
from mangum import Mangum
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # To import main.py from root
from main import app  # Import your FastAPI app

handler = Mangum(app)  # This makes it compatible with Vercel's serverless function

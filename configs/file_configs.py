import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
API_URL = os.getenv("API_URL")

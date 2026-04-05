from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS so the static index.html can fetch from the API if opened separately
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_class=PlainTextResponse)
def health_check():
    return "OK"

@app.get("/search")
def search_events():
    return [
        {"Name": "Jazz Festival", "Date": "2026-05-10", "Venue": "Downtown Park"},
        {"Name": "Tech Conference", "Date": "2026-06-15", "Venue": "Convention Center"},
        {"Name": "Food Truck Fiesta", "Date": "2026-04-20", "Venue": "City Square"}
    ]

@app.get("/")
def serve_home():
    return FileResponse("index.html")

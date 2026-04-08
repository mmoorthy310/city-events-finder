from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

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
async def search_events(city: str = ""):
    api_key = os.getenv("TICKETMASTER_API_KEY")
    
    if not api_key:
        return [
            {"Name": "Error: Missing API Key", "Date": "N/A", "Venue": "Backend Check"}
        ]
        
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        "apikey": api_key,
        "size": 10,
        "sort": "date,asc"
    }
    if city:
        params["city"] = city

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            events_list = []
            if "_embedded" in data and "events" in data["_embedded"]:
                for event in data["_embedded"]["events"]:
                    name = event.get("name", "Unknown Event")
                    
                    # Extract date safely
                    date = "TBD"
                    if "dates" in event and "start" in event["dates"] and "localDate" in event["dates"]["start"]:
                        date = event["dates"]["start"]["localDate"]
                        
                    # Extract venue safely
                    venue = "Unknown Venue"
                    if "_embedded" in event and "venues" in event["_embedded"] and len(event["_embedded"]["venues"]) > 0:
                        venue = event["_embedded"]["venues"][0].get("name", "Unknown Venue")
                        
                    events_list.append({"Name": name, "Date": date, "Venue": venue})
                    
            return events_list
        except Exception as e:
            print(f"Error fetching from Ticketmaster: {e}")
            return [{"Name": f"Error: {str(e)}", "Date": "N/A", "Venue": "N/A"}]

@app.get("/")
def serve_home():
    return FileResponse("index.html")

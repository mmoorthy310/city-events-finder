from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import asyncio
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

async def fetch_ticketmaster(city: str, client: httpx.AsyncClient):
    api_key = os.getenv("TICKETMASTER_API_KEY")
    if not api_key:
        return []
    try:
        params = {
            "apikey": api_key,
            "size": 10,
            "sort": "date,asc"
        }
        if city:
            params["city"] = city

        response = await client.get(
            "https://app.ticketmaster.com/discovery/v2/events.json",
            params=params
        )
        response.raise_for_status()
        data = response.json()

        events = []
        if "_embedded" in data and "events" in data["_embedded"]:
            for event in data["_embedded"]["events"]:
                name = event.get("name", "Unknown Event")
                date = "TBD"
                if "dates" in event and "start" in event["dates"] and "localDate" in event["dates"]["start"]:
                    date = event["dates"]["start"]["localDate"]
                venue = "Unknown Venue"
                if "_embedded" in event and "venues" in event["_embedded"] and len(event["_embedded"]["venues"]) > 0:
                    venue = event["_embedded"]["venues"][0].get("name", "Unknown Venue")
                events.append({"Name": name, "Date": date, "Venue": venue, "Source": "Ticketmaster"})
        return events
    except Exception as e:
        print(f"Ticketmaster error: {e}")
        return []

async def fetch_seatgeek(city: str, client: httpx.AsyncClient):
    client_id = os.getenv("SEATGEEK_CLIENT_ID")
    if not client_id:
        return []
    try:
        params = {
            "client_id": client_id,
            "per_page": 10,
            "sort": "datetime_utc.asc"
        }
        if city:
            params["venue.city"] = city

        response = await client.get(
            "https://api.seatgeek.com/2/events",
            params=params
        )
        response.raise_for_status()
        data = response.json()

        events = []
        for event in data.get("events", []):
            name = event.get("title", "Unknown Event")
            date = event.get("datetime_local", "TBD")
            # Trim time portion if present: "2026-05-10T19:00:00" -> "2026-05-10"
            if "T" in date:
                date = date.split("T")[0]
            venue = "Unknown Venue"
            if "venue" in event and event["venue"]:
                venue = event["venue"].get("name", "Unknown Venue")
            events.append({"Name": name, "Date": date, "Venue": venue, "Source": "SeatGeek"})
        return events
    except Exception as e:
        print(f"SeatGeek error: {e}")
        return []

@app.get("/search")
async def search_events(city: str = ""):
    async with httpx.AsyncClient() as client:
        # Fetch from both APIs simultaneously
        tm_events, sg_events = await asyncio.gather(
            fetch_ticketmaster(city, client),
            fetch_seatgeek(city, client)
        )

    # Merge and sort combined results by date
    combined = tm_events + sg_events
    combined.sort(key=lambda e: e["Date"] if e["Date"] != "TBD" else "9999")
    return combined

@app.get("/")
def serve_home():
    return FileResponse("index.html")

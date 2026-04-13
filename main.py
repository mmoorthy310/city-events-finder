from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import asyncio
from dotenv import load_dotenv
from datetime import datetime, timezone

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
        now = datetime.now(timezone.utc)
        params = {
            "apikey": api_key,
            "size": 10,
            "sort": "date,asc",
            "startDateTime": now.strftime("%Y-%m-%dT%H:%M:%SZ")
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
        now = datetime.now(timezone.utc)
        params = {
            "client_id": client_id,
            "per_page": 10,
            "sort": "datetime_utc.asc",
            "datetime_utc.gte": now.strftime("%Y-%m-%d")
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

async def fetch_predicthq(city: str, client: httpx.AsyncClient):
    api_key = os.getenv("PREDICTHQ_API_KEY")
    if not api_key:
        return []
    try:
        now = datetime.now(timezone.utc)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }
        params = {
            "limit": 10,
            "sort": "start",
            "start.gte": now.strftime("%Y-%m-%d")
        }
        if city:
            params["q"] = city

        response = await client.get(
            "https://api.predicthq.com/v1/events/",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        data = response.json()

        events = []
        for event in data.get("results", []):
            name = event.get("title", "Unknown Event")
            date = "TBD"
            if "start_local" in event and event["start_local"]:
                date = event["start_local"].split("T")[0]
            elif "start" in event and event["start"]:
                date = event["start"].split("T")[0]
            
            venue = "Unknown Venue"
            for entity in event.get("entities", []):
                if entity.get("type") == "venue":
                    venue = entity.get("name", "Unknown Venue")
                    break
            
            if venue == "Unknown Venue" and "geo" in event and event["geo"] and "address" in event["geo"] and "formatted_address" in event["geo"]["address"]:
                venue = event["geo"]["address"]["formatted_address"]
            
            events.append({"Name": name, "Date": date, "Venue": venue, "Source": "PredictHQ"})
        return events
    except Exception as e:
        print(f"PredictHQ error: {e}")
        return []

@app.get("/search")
async def search_events(city: str = ""):
    async with httpx.AsyncClient() as client:
        # Fetch from all APIs simultaneously
        tm_events, sg_events, phq_events = await asyncio.gather(
            fetch_ticketmaster(city, client),
            fetch_seatgeek(city, client),
            fetch_predicthq(city, client)
        )

    # Merge results
    combined = tm_events + sg_events + phq_events

    # Deduplicate by normalized name + date fingerprint
    seen = set()
    deduped = []
    for event in combined:
        name_normalized = event["Name"].lower().strip()
        key = (name_normalized, event["Date"])
        if key not in seen:
            seen.add(key)
            deduped.append(event)

    # Sort deduplicated results by date
    deduped.sort(key=lambda e: e["Date"] if e["Date"] != "TBD" else "9999")

    # Print deduplication stats to console
    print(f"Merged {len(combined)} events → {len(deduped)} after deduplication (removed {len(combined) - len(deduped)} duplicates)")

    return deduped

@app.get("/")
def serve_home():
    return FileResponse("index.html")

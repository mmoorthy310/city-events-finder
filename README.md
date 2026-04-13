# City Events Finder

City Events Finder is a fast, lightweight web application built with FastAPI that aggregates real-time event data from major ticketing platforms. By simply searching for a city name, it seamlessly retrieves, normalizes, and displays chronological events from around the internet.

## 🌟 Features
- **Multi-Source Aggregation**: Pulls and normalizes live data seamlessly from Ticketmaster, SeatGeek, and PredictHQ.
- **Chronological Sorting**: Retrieves all upcoming events dynamically starting from the current date.
- **Intelligent Deduplication**: Automatically deduplicates identical events happening on the same day fetched from multiple platforms.
- **Async Backend Architecture**: Uses asynchronous API requests (`httpx` & `asyncio`) to fetch from all three providers simultaneously for enhanced speed.
- **Responsive UI**: Clean HTML/CSS frontend with dynamic loader rendering and color-coded provider badges.

## 🚀 Tech Stack
- **Backend:** Python 3, FastAPI, Uvicorn, HTTPX
- **Frontend:** HTML, Vanilla CSS, Vanilla JavaScript
- **Integrated Events APIs:** Ticketmaster, SeatGeek, PredictHQ

## 🛠️ Prerequisites & Setup

Ensure you have Python 3 installed on your system. It is highly recommended to use a virtual environment:

```bash
# Create a virtual environment
python3 -m venv venv

# Activate it (Mac/Linux)
source venv/bin/activate

# (Optional) Activate it (Windows)
# venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn httpx python-dotenv
```

### Environment Variables

For the application to fetch real live data, you will need to obtain API credentials from the three providers.
Create a `.env` file in the root directory and add the following keys:

```ini
TICKETMASTER_API_KEY=your_ticketmaster_api_key_here
SEATGEEK_CLIENT_ID=your_seatgeek_client_id_here
PREDICTHQ_API_KEY=your_predicthq_api_key_here
```

## 💻 Running the Application

To start the local web backend development server, run:

```bash
uvicorn main:app --reload
```

Once running, simply open your web browser and navigate to: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## 🏗️ Deep Dive / How it Works
1. The frontend (`index.html`) takes a search parameter and hits the `/search` endpoint on the FastAPI router.
2. The endpoint utilizes `asyncio.gather` to instantaneously request payload data from Ticketmaster, SeatGeek, and PredictHQ.
3. Each distinct JSON output is chopped up and normalized perfectly into identical formatting (`Name`, `Date`, `Venue`, `Source`).
4. The finalized dataset is merged, evaluated for duplicates using name + string formatting, chronologically sorted, and served dynamically.

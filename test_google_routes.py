import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_MAPS_API_KEY")

if not api_key:
    raise ValueError("GOOGLE_MAPS_API_KEY missing in .env")

url = "https://routes.googleapis.com/directions/v2:computeRoutes"

headers = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": api_key,
    "X-Goog-FieldMask": (
        "routes.duration,"
        "routes.distanceMeters,"
        "routes.polyline.encodedPolyline"
    ),
}

payload = {
    "origin": {
        "address": "Delhi Airport, New Delhi, India"
    },
    "destination": {
        "address": "Noida Sector 62, Uttar Pradesh, India"
    },
    "travelMode": "DRIVE",
    "routingPreference": "TRAFFIC_AWARE",
    "computeAlternativeRoutes": True,
}

response = requests.post(
    url,
    headers=headers,
    json=payload,
    timeout=30,
)

print("HTTP Status:", response.status_code)

if response.ok:
    routes = response.json().get("routes", [])

    print("Routes found:", len(routes))

    for i, route in enumerate(routes, 1):
        distance = route["distanceMeters"] / 1000
        duration = route["duration"]

        print(f"\nRoute {i}")
        print(f"Distance: {distance:.2f} km")
        print(f"Duration: {duration}")
else:
    print("API Error:", response.text)
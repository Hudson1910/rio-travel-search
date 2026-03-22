"""Flight and hotel search via RapidAPI."""
import requests
from config import RAPIDAPI_KEY

HEADERS = {
    'x-rapidapi-key': RAPIDAPI_KEY,
}


def search_flights(origin, destination, departure_date, return_date=None, adults=1, currency='USD'):
    """Search flights via Flights Scraper Real-Time (Kiwi)."""
    try:
        url = 'https://flights-scraper-real-time.p.rapidapi.com/flights/search'
        params = {
            'origin': origin,
            'destination': destination,
            'departureDate': departure_date,
            'adults': adults,
            'currency': currency,
        }
        if return_date:
            params['returnDate'] = return_date

        headers = {**HEADERS, 'x-rapidapi-host': 'flights-scraper-real-time.p.rapidapi.com'}
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        data = resp.json()

        if 'message' in data and 'not subscribed' in data['message'].lower():
            print(f"[Search] Not subscribed to Flights API")
            return {'flights': [], 'error': 'API not subscribed'}

        return data
    except Exception as e:
        print(f"[Search] Flight error: {e}")
        return {'flights': [], 'error': str(e)}


def search_hotels(destination, checkin, checkout, adults=2, currency='USD'):
    """Search hotels via Booking COM API."""
    try:
        url = 'https://booking-com-cheaper-version.p.rapidapi.com/search'
        params = {
            'destination': destination,
            'checkIn': checkin,
            'checkOut': checkout,
            'adults': adults,
            'currency': currency,
        }
        headers = {**HEADERS, 'x-rapidapi-host': 'booking-com-cheaper-version.p.rapidapi.com'}
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        data = resp.json()

        if 'message' in data and 'not subscribed' in data['message'].lower():
            return {'hotels': [], 'error': 'API not subscribed'}

        return data
    except Exception as e:
        print(f"[Search] Hotel error: {e}")
        return {'hotels': [], 'error': str(e)}

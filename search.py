"""Flight and hotel search via RapidAPI (Booking COM)."""
import requests
from config import RAPIDAPI_KEY

HEADERS = {
    'x-rapidapi-key': RAPIDAPI_KEY,
    'x-rapidapi-host': 'booking-com15.p.rapidapi.com',
    'Content-Type': 'application/json',
}

BASE_URL = 'https://booking-com15.p.rapidapi.com/api/v1'


def search_flights(origin, destination, depart_date, return_date=None, adults=1):
    """Search flights via Booking COM API."""
    try:
        params = {
            'fromId': f'{origin}.AIRPORT',
            'toId': f'{destination}.AIRPORT',
            'departDate': depart_date,
            'adults': adults,
            'currencyCode': 'USD',
        }
        if return_date:
            params['returnDate'] = return_date

        resp = requests.get(f'{BASE_URL}/flights/searchFlights', headers=HEADERS, params=params, timeout=30)
        data = resp.json()

        if not data.get('status'):
            return {'flights': [], 'error': data.get('message', 'API error')}

        offers = data.get('data', {}).get('flightOffers', [])
        flights = []

        for offer in offers[:20]:
            price_data = offer.get('priceBreakdown', {}).get('total', {})
            price = price_data.get('units', 0)
            segments = offer.get('segments', [])

            if not segments:
                continue

            seg = segments[0]
            legs = seg.get('legs', [])
            dep_airport = seg.get('departureAirport', {})
            arr_airport = seg.get('arrivalAirport', {})

            # Get first and last leg times
            dep_time = legs[0].get('departureTime', '') if legs else ''
            arr_time = legs[-1].get('arrivalTime', '') if legs else ''

            # Airline from first leg
            carrier = {}
            if legs and legs[0].get('carriersData'):
                carrier = legs[0]['carriersData'][0]

            # Duration
            total_duration = seg.get('totalTime', 0)
            hours = total_duration // 3600
            mins = (total_duration % 3600) // 60
            duration_str = f'{hours}h {mins}m' if total_duration else ''

            # Stops
            stops = len(legs) - 1

            flights.append({
                'price': price,
                'airline': carrier.get('name', ''),
                'airlineCode': carrier.get('code', ''),
                'airlineLogo': carrier.get('logo', ''),
                'departureTime': dep_time[11:16] if len(dep_time) > 16 else dep_time,
                'arrivalTime': arr_time[11:16] if len(arr_time) > 16 else arr_time,
                'departureDate': dep_time[:10] if len(dep_time) > 10 else '',
                'arrivalDate': arr_time[:10] if len(arr_time) > 10 else '',
                'origin': dep_airport.get('code', origin),
                'destination': arr_airport.get('code', destination),
                'originCity': dep_airport.get('city', ''),
                'destinationCity': arr_airport.get('city', ''),
                'stops': stops,
                'duration': duration_str,
                'legs': [{
                    'airline': (l.get('carriersData', [{}])[0].get('name', '') if l.get('carriersData') else ''),
                    'airlineCode': (l.get('carriersData', [{}])[0].get('code', '') if l.get('carriersData') else ''),
                    'flightNumber': l.get('flightInfo', {}).get('flightNumber', ''),
                    'departure': l.get('departureTime', ''),
                    'arrival': l.get('arrivalTime', ''),
                    'depAirport': l.get('departureAirport', {}).get('code', ''),
                    'arrAirport': l.get('arrivalAirport', {}).get('code', ''),
                } for l in legs],
            })

        # Sort by price
        flights.sort(key=lambda x: x['price'])
        return {'flights': flights, 'total': len(offers)}

    except Exception as e:
        print(f"[Search] Flight error: {e}")
        return {'flights': [], 'error': str(e)}


def search_hotels(destination, checkin, checkout, adults=2):
    """Search hotels via Booking COM API."""
    try:
        # First get destination ID
        dest_resp = requests.get(f'{BASE_URL}/hotels/searchDestination',
            headers=HEADERS,
            params={'query': destination},
            timeout=15)
        dest_data = dest_resp.json()
        destinations = dest_data.get('data', [])

        if not destinations:
            return {'hotels': [], 'error': 'Destination not found'}

        dest = destinations[0]
        dest_id = dest.get('dest_id', '')
        dest_type = dest.get('dest_type', 'city')

        # Search hotels
        resp = requests.get(f'{BASE_URL}/hotels/searchHotels',
            headers=HEADERS,
            params={
                'dest_id': dest_id,
                'search_type': dest_type.upper(),
                'arrival_date': checkin,
                'departure_date': checkout,
                'adults': adults,
                'room_qty': 1,
                'currency_code': 'USD',
                'sort_by': 'price',
            },
            timeout=30)
        data = resp.json()

        hotels_raw = data.get('data', {}).get('hotels', [])
        hotels = []

        for h in hotels_raw[:15]:
            prop = h.get('property', {})
            price_data = prop.get('priceBreakdown', {}).get('grossPrice', {})

            hotels.append({
                'name': prop.get('name', ''),
                'price': round(price_data.get('value', 0), 2),
                'currency': price_data.get('currency', 'USD'),
                'stars': prop.get('propertyClass', 0),
                'rating': prop.get('reviewScore', 0),
                'reviewCount': prop.get('reviewCount', 0),
                'photo': prop.get('photoUrls', [''])[0] if prop.get('photoUrls') else '',
                'location': prop.get('wishlistName', ''),
            })

        hotels.sort(key=lambda x: x['price'])
        return {'hotels': hotels, 'total': len(hotels_raw)}

    except Exception as e:
        print(f"[Search] Hotel error: {e}")
        return {'hotels': [], 'error': str(e)}

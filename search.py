"""Flight search via Google Flights API (RapidAPI) + Hotels via Booking COM."""
import requests
from config import RAPIDAPI_KEY

# ========== GOOGLE FLIGHTS ==========
GF_HEADERS = {
    'x-rapidapi-key': RAPIDAPI_KEY,
    'x-rapidapi-host': 'google-flights2.p.rapidapi.com',
    'Content-Type': 'application/json',
}
GF_BASE = 'https://google-flights2.p.rapidapi.com/api/v1'

# ========== BOOKING COM (hotels only) ==========
BK_HEADERS = {
    'x-rapidapi-key': RAPIDAPI_KEY,
    'x-rapidapi-host': 'booking-com15.p.rapidapi.com',
    'Content-Type': 'application/json',
}
BK_BASE = 'https://booking-com15.p.rapidapi.com/api/v1'


def search_flights(origin, destination, depart_date, return_date=None,
                   adults=1, children=0, infants=0, cabin='ECONOMY',
                   lang='en-US', currency='USD', stops=None):
    """Search flights via Google Flights API."""
    try:
        params = {
            'departure_id': origin,
            'arrival_id': destination,
            'outbound_date': depart_date,
            'adults': adults,
            'travel_class': cabin,
            'currency': currency,
            'language_code': lang,
            'country_code': 'US',
            'search_type': 'best',
            'show_hidden': 1,
        }
        if return_date:
            params['return_date'] = return_date
        if children > 0:
            params['children'] = children
        if infants > 0:
            params['infants_on_lap'] = infants
        if stops is not None:
            params['stops'] = stops

        resp = requests.get(f'{GF_BASE}/searchFlights', headers=GF_HEADERS,
                            params=params, timeout=30)
        data = resp.json()

        if not data.get('status'):
            msg = data.get('message', 'API error')
            return {'flights': [], 'error': str(msg)}

        d = data.get('data', {})
        itineraries = d.get('itineraries', {})
        top = itineraries.get('topFlights', [])
        other = itineraries.get('otherFlights', [])
        all_flights = top + other

        # Price history
        ph = d.get('priceHistory', {})
        price_summary = ph.get('summary', {})

        flights = []
        for fl in all_flights[:25]:
            legs = fl.get('flights', [])
            if not legs:
                continue

            first_leg = legs[0]
            last_leg = legs[-1]
            dep = first_leg.get('departure_airport', {})
            arr = last_leg.get('arrival_airport', {})
            duration = fl.get('duration', {})
            bags = fl.get('bags', {})
            carbon = fl.get('carbon_emissions', {})
            layovers = fl.get('layovers', [])

            # Parse departure/arrival times
            dep_time_raw = dep.get('time', '')
            arr_time_raw = arr.get('time', '')
            dep_time = dep_time_raw.split(' ')[-1] if dep_time_raw else ''
            arr_time = arr_time_raw.split(' ')[-1] if arr_time_raw else ''
            dep_date = dep_time_raw.split(' ')[0] if dep_time_raw else ''
            arr_date = arr_time_raw.split(' ')[0] if arr_time_raw else ''

            flights.append({
                'price': fl.get('price', 0),
                'airline': first_leg.get('airline', ''),
                'airlineCode': '',
                'airlineLogo': first_leg.get('airline_logo', ''),
                'flightNumber': first_leg.get('flight_number', ''),
                'aircraft': first_leg.get('aircraft', ''),
                'departureTime': dep_time,
                'arrivalTime': arr_time,
                'departureDate': dep_date,
                'arrivalDate': arr_date,
                'origin': dep.get('airport_code', origin),
                'destination': arr.get('airport_code', destination),
                'originAirport': dep.get('airport_name', ''),
                'destinationAirport': arr.get('airport_name', ''),
                'originCity': dep.get('airport_name', '').split(' International')[0].split(' Airport')[0] if dep.get('airport_name') else '',
                'destinationCity': arr.get('airport_name', '').split(' International')[0].split(' Airport')[0] if arr.get('airport_name') else '',
                'stops': len(legs) - 1,
                'duration': duration.get('text', ''),
                'durationMin': duration.get('raw', 0),
                'legroom': first_leg.get('legroom', ''),
                'seatInfo': first_leg.get('seat', ''),
                'bagsCarryOn': bags.get('carry_on', None),
                'bagsChecked': bags.get('checked', None),
                'co2': carbon.get('CO2e', 0),
                'co2Diff': carbon.get('difference_percent', 0),
                'co2Typical': carbon.get('typical_for_this_route', 0),
                'layovers': [{
                    'city': lo.get('city', ''),
                    'airport': lo.get('airport_name', ''),
                    'airportCode': lo.get('airport_code', ''),
                    'duration': lo.get('duration', 0),
                    'durationLabel': lo.get('duration_label', ''),
                } for lo in layovers],
                'legs': [{
                    'airline': l.get('airline', ''),
                    'airlineLogo': l.get('airline_logo', ''),
                    'flightNumber': l.get('flight_number', ''),
                    'aircraft': l.get('aircraft', ''),
                    'depAirport': l.get('departure_airport', {}).get('airport_code', ''),
                    'depAirportName': l.get('departure_airport', {}).get('airport_name', ''),
                    'depTime': l.get('departure_airport', {}).get('time', '').split(' ')[-1] if l.get('departure_airport', {}).get('time') else '',
                    'arrAirport': l.get('arrival_airport', {}).get('airport_code', ''),
                    'arrAirportName': l.get('arrival_airport', {}).get('airport_name', ''),
                    'arrTime': l.get('arrival_airport', {}).get('time', '').split(' ')[-1] if l.get('arrival_airport', {}).get('time') else '',
                    'duration': l.get('duration', {}).get('text', ''),
                    'legroom': l.get('legroom', ''),
                    'seat': l.get('seat', ''),
                } for l in legs],
                'isTopFlight': fl in top,
                'bookingToken': fl.get('booking_token', ''),
                'extensions': first_leg.get('extensions', []),
            })

        flights.sort(key=lambda x: x['price'])

        # Price history for chart
        price_history = ph.get('history', [])
        history_points = [{'t': p['time'], 'v': p['value']} for p in price_history]

        # Determine price level
        current_price = price_summary.get('current', 0)
        low_val = price_summary.get('low', [{}])[0].get('value', 0) if price_summary.get('low') else 0
        typical_range = price_summary.get('typical', [])
        typical_low = typical_range[0].get('value', 0) if len(typical_range) > 0 else 0
        typical_high = typical_range[2].get('value', 0) if len(typical_range) > 2 else 0

        if current_price and low_val and current_price < low_val:
            price_level = 'low'
        elif current_price and typical_high and current_price > typical_high:
            price_level = 'high'
        else:
            price_level = 'typical'

        # Trend: compare current to average of last 7 days
        recent = [p['value'] for p in price_history[-7:]] if price_history else []
        older = [p['value'] for p in price_history[-30:-7]] if len(price_history) > 7 else []
        trend = 'stable'
        if recent and older:
            avg_recent = sum(recent) / len(recent)
            avg_older = sum(older) / len(older)
            if avg_recent > avg_older * 1.05:
                trend = 'rising'
            elif avg_recent < avg_older * 0.95:
                trend = 'falling'

        return {
            'flights': flights,
            'total': len(all_flights),
            'priceInsight': {
                'current': current_price,
                'low': low_val,
                'typicalLow': typical_low,
                'typicalHigh': typical_high,
                'level': price_level,
                'trend': trend,
                'history': history_points,
            },
            'source': 'google_flights',
        }

    except Exception as e:
        print(f"[Search] Flight error: {e}")
        return {'flights': [], 'error': str(e)}


def search_hotels(destination, checkin, checkout, adults=2):
    """Search hotels via Booking COM API."""
    try:
        dest_resp = requests.get(f'{BK_BASE}/hotels/searchDestination',
            headers=BK_HEADERS,
            params={'query': destination},
            timeout=15)
        dest_data = dest_resp.json()
        destinations = dest_data.get('data', [])

        if not destinations:
            return {'hotels': [], 'error': 'Destination not found'}

        dest = destinations[0]
        dest_id = dest.get('dest_id', '')
        dest_type = dest.get('dest_type', 'city')

        resp = requests.get(f'{BK_BASE}/hotels/searchHotels',
            headers=BK_HEADERS,
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

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

# ========== BOOKING COM (hotels + car rentals) ==========
BK_HEADERS = {
    'x-rapidapi-key': RAPIDAPI_KEY,
    'x-rapidapi-host': 'booking-com.p.rapidapi.com',
}
BK_BASE = 'https://booking-com.p.rapidapi.com'


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

        d = data.get('data') or {}
        itineraries = d.get('itineraries') or {}
        top = itineraries.get('topFlights') or []
        other = itineraries.get('otherFlights') or []
        all_flights = top + other

        # Price history
        ph = d.get('priceHistory') or {}
        price_summary = ph.get('summary') or {}

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


def get_price_graph(origin, destination, date, currency='USD'):
    """Get price calendar — cheapest price for each day of the month."""
    try:
        params = {
            'departure_id': origin,
            'arrival_id': destination,
            'outbound_date': date,
            'currency': currency,
        }
        resp = requests.get(f'{GF_BASE}/getPriceGraph', headers=GF_HEADERS,
                            params=params, timeout=30)
        data = resp.json()

        if not data.get('status'):
            return {'prices': [], 'error': str(data.get('message', 'API error'))}

        prices = data.get('data', [])
        result = []
        for p in prices:
            result.append({
                'date': p.get('departure', ''),
                'price': p.get('price', 0),
            })

        # Find cheapest
        if result:
            min_price = min(r['price'] for r in result if r['price'] > 0)
            for r in result:
                r['isCheapest'] = r['price'] == min_price

        return {'prices': result, 'total': len(result)}

    except Exception as e:
        print(f"[Search] Price graph error: {e}")
        return {'prices': [], 'error': str(e)}


def search_airport(query):
    """Search airports via Google Flights."""
    try:
        resp = requests.get(f'{GF_BASE}/searchAirport', headers=GF_HEADERS,
                            params={'query': query}, timeout=10)
        data = resp.json()

        if not data.get('status'):
            return {'results': []}

        raw = data.get('data', [])
        results = []
        for item in raw:
            # City-level result with sub-airports
            if item.get('list'):
                for sub in item['list']:
                    if sub.get('type') == 'airport':
                        results.append({
                            'code': sub.get('id', ''),
                            'name': sub.get('title', ''),
                            'city': item.get('city', ''),
                            'distance': sub.get('distance', ''),
                        })
            elif item.get('type') == 'airport':
                results.append({
                    'code': item.get('id', ''),
                    'name': item.get('title', ''),
                    'city': item.get('city', ''),
                    'distance': '',
                })

        return {'results': results}

    except Exception as e:
        print(f"[Search] Airport search error: {e}")
        return {'results': []}


def search_hotels(destination, checkin, checkout, adults=2, locale='en-gb'):
    """Search hotels via Booking.com API (new host)."""
    try:
        # Step 1: Get destination ID
        dest_resp = requests.get(f'{BK_BASE}/v1/hotels/locations',
            headers=BK_HEADERS,
            params={'name': destination, 'locale': locale},
            timeout=15)
        destinations = dest_resp.json()

        if not isinstance(destinations, list) or not destinations:
            return {'hotels': [], 'error': 'Destination not found'}

        dest = destinations[0]
        dest_id = dest.get('dest_id', '')
        dest_type = dest.get('dest_type', 'city')

        # Step 2: Search hotels
        resp = requests.get(f'{BK_BASE}/v1/hotels/search',
            headers=BK_HEADERS,
            params={
                'locale': locale,
                'dest_id': dest_id,
                'dest_type': dest_type,
                'checkin_date': checkin,
                'checkout_date': checkout,
                'adults_number': adults,
                'room_number': 1,
                'filter_by_currency': 'USD',
                'order_by': 'popularity',
                'units': 'metric',
            },
            timeout=30)
        data = resp.json()

        hotels_raw = data.get('result', [])
        hotels = []

        for h in hotels_raw[:15]:
            photo = ''
            if h.get('max_photo_url'):
                photo = h['max_photo_url']
            elif h.get('main_photo_url'):
                photo = h['main_photo_url']

            hotels.append({
                'id': h.get('hotel_id', ''),
                'name': h.get('hotel_name', ''),
                'price': round(h.get('min_total_price', 0), 2),
                'currency': h.get('currency_code', 'USD'),
                'stars': h.get('class', 0),
                'rating': h.get('review_score', 0),
                'ratingWord': h.get('review_score_word', ''),
                'reviewCount': h.get('review_nr', 0),
                'photo': photo,
                'address': h.get('address', ''),
                'city': h.get('city', ''),
                'distance': h.get('distance_to_cc', ''),
                'distanceUnit': h.get('distance_to_cc_unit', 'km'),
                'checkin': h.get('checkin', {}),
                'checkout': h.get('checkout', {}),
                'url': h.get('url', ''),
                'isFreeCancel': h.get('is_free_cancellable', False),
                'isNoPrepay': h.get('is_no_prepayment_block', False),
            })

        hotels.sort(key=lambda x: x['price'] if x['price'] > 0 else 99999)
        return {
            'hotels': hotels,
            'total': data.get('count', len(hotels_raw)),
            'destination': dest.get('label', destination),
        }

    except Exception as e:
        print(f"[Search] Hotel error: {e}")
        return {'hotels': [], 'error': str(e)}


def search_cars(location, pickup_date, dropoff_date, pickup_time='10:00:00',
                dropoff_time='10:00:00', locale='en-gb'):
    """Search car rentals via Booking.com API."""
    try:
        # Step 1: Get location coordinates
        loc_resp = requests.get(f'{BK_BASE}/v1/car-rental/locations',
            headers=BK_HEADERS,
            params={'name': location, 'locale': locale},
            timeout=15)
        locations = loc_resp.json()

        if not isinstance(locations, list) or not locations:
            return {'cars': [], 'error': 'Location not found'}

        loc = locations[0]
        lat = loc.get('latitude', 0)
        lng = loc.get('longitude', 0)

        # from_country must be a locale code, not country code
        # Allowed: it,de,nl,fr,es,ca,no,fi,sv,da,cs,hu,ro,ja,pl,el,ru,tr,bg,ar,ko,he,lv,uk,id,ms,th,et,hr,lt,sk,sr,sl,vi,tl
        country = 'es'  # default to Spanish (works for US, Mexico, Latin America)
        loc_lower = location.lower()
        if any(x in loc_lower for x in ['france', 'paris', 'lyon', 'nice']):
            country = 'fr'
        elif any(x in loc_lower for x in ['italy', 'rome', 'milan', 'roma']):
            country = 'it'
        elif any(x in loc_lower for x in ['germany', 'berlin', 'munich', 'frankfurt']):
            country = 'de'
        elif any(x in loc_lower for x in ['netherlands', 'amsterdam']):
            country = 'nl'
        elif any(x in loc_lower for x in ['japan', 'tokyo', 'osaka']):
            country = 'ja'
        elif any(x in loc_lower for x in ['turkey', 'istanbul']):
            country = 'tr'
        elif any(x in loc_lower for x in ['russia', 'moscow']):
            country = 'ru'
        elif any(x in loc_lower for x in ['korea', 'seoul']):
            country = 'ko'

        # Step 2: Search cars
        resp = requests.get(f'{BK_BASE}/v1/car-rental/search',
            headers=BK_HEADERS,
            params={
                'locale': locale,
                'currency': 'USD',
                'sort_by': 'price_low_to_high',
                'from_country': country,
                'pick_up_latitude': lat,
                'pick_up_longitude': lng,
                'pick_up_datetime': f'{pickup_date} {pickup_time}',
                'drop_off_latitude': lat,
                'drop_off_longitude': lng,
                'drop_off_datetime': f'{dropoff_date} {dropoff_time}',
            },
            timeout=30)
        data = resp.json()

        if not isinstance(data, dict):
            return {'cars': [], 'error': 'Invalid response'}
        cars_raw = data.get('search_results') or data.get('result') or []
        if not isinstance(cars_raw, list):
            cars_raw = []

        cars = []
        for c in cars_raw[:15]:
            vehicle = c.get('vehicle_info', c.get('vehicle_type', {}))
            supplier = c.get('supplier_info', c.get('supplier', {}))
            price_info = c.get('pricing_info', {})
            price = price_info.get('price', c.get('price', 0))
            if isinstance(price, str):
                try:
                    price = float(price)
                except ValueError:
                    price = 0

            cars.append({
                'name': vehicle.get('v_name', vehicle.get('name', '')),
                'group': vehicle.get('group', ''),
                'type': vehicle.get('label', vehicle.get('vehicle_type', '')),
                'transmission': vehicle.get('transmission', ''),
                'fuel': vehicle.get('fuel_type', vehicle.get('fuel_policy', '')),
                'seats': vehicle.get('seats', vehicle.get('seat_count', '')),
                'doors': vehicle.get('doors', vehicle.get('door_count', '')),
                'bags': vehicle.get('bags', vehicle.get('bag_count', '')),
                'ac': vehicle.get('aircon', vehicle.get('air_conditioning', False)),
                'photo': vehicle.get('image_url', vehicle.get('image_thumbnail_url', '')),
                'price': round(price, 2) if price else 0,
                'currency': price_info.get('currency', 'USD'),
                'supplier': supplier.get('name', supplier.get('supplier_name', '')),
                'supplierLogo': supplier.get('logo_url', ''),
                'supplierRating': supplier.get('review_score', supplier.get('rating', 0)),
                'pickup': loc.get('label', location),
            })

        cars.sort(key=lambda x: x['price'] if x['price'] > 0 else 99999)
        return {
            'cars': cars,
            'total': len(cars_raw),
            'location': loc.get('label', location),
        }

    except Exception as e:
        print(f"[Search] Car rental error: {e}")
        return {'cars': [], 'error': str(e)}

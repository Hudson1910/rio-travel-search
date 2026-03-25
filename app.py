"""Rio Travel Search — Flight & Hotel Search for Clients."""
from flask import Flask, render_template, request, jsonify, send_from_directory
import config
import search

app = Flask(__name__)
app.secret_key = config.SECRET_KEY


@app.route('/')
def home():
    return render_template('home.html', config=config)


@app.route('/robots.txt')
def robots():
    return send_from_directory('static', 'robots.txt', mimetype='text/plain')


@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('static', 'sitemap.xml', mimetype='application/xml')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/x-icon')


@app.route('/api/flights')
def api_flights():
    """Search flights via Google Flights."""
    origin = request.args.get('origin', '').strip().upper()
    destination = request.args.get('destination', '').strip().upper()
    departure = request.args.get('departure', '')
    ret = request.args.get('return', '')
    adults = int(request.args.get('adults', 1))
    children = int(request.args.get('children', 0))
    infants = int(request.args.get('infants', 0))
    cabin = request.args.get('cabin', 'ECONOMY').upper()
    lang = request.args.get('lang', 'en-US')
    currency = request.args.get('currency', 'USD')
    stops = request.args.get('stops', None)
    if stops is not None:
        stops = int(stops)

    if not origin or not destination or not departure:
        return jsonify({'error': 'Missing required fields', 'flights': []})

    results = search.search_flights(
        origin, destination, departure,
        return_date=ret or None,
        adults=adults,
        children=children,
        infants=infants,
        cabin=cabin,
        lang=lang,
        currency=currency,
        stops=stops,
    )
    return jsonify(results)


@app.route('/api/priceGraph')
def api_price_graph():
    """Get price calendar for a route."""
    origin = request.args.get('origin', '').strip().upper()
    destination = request.args.get('destination', '').strip().upper()
    date = request.args.get('date', '')
    currency = request.args.get('currency', 'USD')

    if not origin or not destination or not date:
        return jsonify({'error': 'Missing required fields', 'prices': []})

    results = search.get_price_graph(origin, destination, date, currency)
    return jsonify(results)


@app.route('/api/searchAirport')
def api_search_airport():
    """Search airports via Google Flights."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'results': []})
    results = search.search_airport(query)
    return jsonify(results)


@app.route('/api/hotelLocations')
def api_hotel_locations():
    """Search hotel destinations via Booking.com."""
    query = request.args.get('q', '').strip()
    lang = request.args.get('lang', 'en-gb')
    if not query or len(query) < 2:
        return jsonify({'results': []})
    results = search.search_hotel_locations(query, locale=lang)
    return jsonify(results)


@app.route('/api/carLocations')
def api_car_locations():
    """Search car rental locations via Booking.com."""
    query = request.args.get('q', '').strip()
    lang = request.args.get('lang', 'en-gb')
    if not query or len(query) < 2:
        return jsonify({'results': []})
    results = search.search_car_locations(query, locale=lang)
    return jsonify(results)


@app.route('/api/cars')
def api_cars():
    """Search car rentals via Booking.com."""
    location = request.args.get('location', '').strip()
    pickup = request.args.get('pickup', '')
    dropoff = request.args.get('dropoff', '')
    lang = request.args.get('lang', 'en-gb')

    if not location or not pickup or not dropoff:
        return jsonify({'error': 'Missing required fields', 'cars': []})

    results = search.search_cars(location, pickup, dropoff, locale=lang)
    return jsonify(results)


@app.route('/api/hotels')
def api_hotels():
    """Search hotels via Booking COM."""
    destination = request.args.get('destination', '').strip()
    checkin = request.args.get('checkin', '')
    checkout = request.args.get('checkout', '')
    adults = int(request.args.get('adults', 2))

    if not destination or not checkin or not checkout:
        return jsonify({'error': 'Missing required fields', 'hotels': []})

    lang = request.args.get('lang', 'en-gb')
    results = search.search_hotels(destination, checkin, checkout, adults, locale=lang)
    return jsonify(results)


@app.route('/contact')
def contact():
    return render_template('contact.html', config=config)


if __name__ == '__main__':
    print(f"  Rio Travel Search")
    print(f"  http://localhost:{config.PORT}")
    app.run(host='0.0.0.0', port=config.PORT, debug=True)

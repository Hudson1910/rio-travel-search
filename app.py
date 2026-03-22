"""Rio Travel Search — Flight & Hotel Search for Clients."""
from flask import Flask, render_template, request, jsonify
import config
import search

app = Flask(__name__)
app.secret_key = config.SECRET_KEY


@app.route('/')
def home():
    return render_template('home.html', config=config)


@app.route('/api/flights')
def api_flights():
    """Search flights."""
    origin = request.args.get('origin', '').strip().upper()
    destination = request.args.get('destination', '').strip().upper()
    departure = request.args.get('departure', '')
    ret = request.args.get('return', '')
    adults = int(request.args.get('adults', 1))

    if not origin or not destination or not departure:
        return jsonify({'error': 'Missing required fields', 'flights': []})

    results = search.search_flights(origin, destination, departure, ret or None, adults)
    return jsonify(results)


@app.route('/api/hotels')
def api_hotels():
    """Search hotels."""
    destination = request.args.get('destination', '').strip()
    checkin = request.args.get('checkin', '')
    checkout = request.args.get('checkout', '')
    adults = int(request.args.get('adults', 2))

    if not destination or not checkin or not checkout:
        return jsonify({'error': 'Missing required fields', 'hotels': []})

    results = search.search_hotels(destination, checkin, checkout, adults)
    return jsonify(results)


@app.route('/contact')
def contact():
    return render_template('contact.html', config=config)


if __name__ == '__main__':
    print(f"  Rio Travel Search")
    print(f"  http://localhost:{config.PORT}")
    app.run(host='0.0.0.0', port=config.PORT, debug=True)

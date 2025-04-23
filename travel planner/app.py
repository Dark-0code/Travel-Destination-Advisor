from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure key for production

# API Configuration
OPENWEATHER_API_KEY = "55b336ff5d4abb770ba08510f413c758"
RAPIDAPI_KEY = "YOUR_RAPIDAPI_KEY_HERE"
RAPIDAPI_HOST = "booking-com15.p.rapidapi.com"


def get_weather(city):
    """Fetch weather data from OpenWeatherMap"""
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            'temp': data['main']['temp'],
            'humidity': data['main']['humidity'],
            'description': data['weather'][0]['description'],
            'icon': data['weather'][0]['icon']
        }
    except Exception as e:
        print(f"Weather API Error: {e}")
        return None


def get_fallback_hotels(city):
    """Provide static fallback hotels when API fails or returns empty"""
    fallback = {
        "Paris": [
            {'id':'p1','name':'Hotel Parisian','price':200,'address':'10 Rue de Rivoli, Paris','rating':4.2,'photo':'https://via.placeholder.com/400x300'},
            {'id':'p2','name':'Eiffel Stay','price':180,'address':'5 Avenue Anatole, Paris','rating':4.5,'photo':'https://via.placeholder.com/400x300'},
            {'id':'p3','name':'Louvre Lodge','price':220,'address':'Place du Louvre, Paris','rating':4.3,'photo':'https://via.placeholder.com/400x300'},
            {'id':'p4','name':'Champs-Elysees Hotel','price':250,'address':'Avenue des Champs-Élysées, Paris','rating':4.6,'photo':'https://via.placeholder.com/400x300'},
            {'id':'p5','name':'Seine Riverside','price':170,'address':'Quai de la Seine, Paris','rating':4.1,'photo':'https://via.placeholder.com/400x300'}
        ],
        "London": [
            {'id':'l1','name':'London Bridge Inn','price':190,'address':'Borough High St, London','rating':4.4,'photo':'https://via.placeholder.com/400x300'},
            {'id':'l2','name':'Piccadilly Palace','price':210,'address':'Piccadilly Circus, London','rating':4.5,'photo':'https://via.placeholder.com/400x300'},
            {'id':'l3','name':'Kensington Suites','price':230,'address':'Kensington Rd, London','rating':4.2,'photo':'https://via.placeholder.com/400x300'},
            {'id':'l4','name':'Westminster Stay','price':240,'address':'Westminster, London','rating':4.6,'photo':'https://via.placeholder.com/400x300'},
            {'id':'l5','name':'Camden Comfort','price':160,'address':'Camden Town, London','rating':4.1,'photo':'https://via.placeholder.com/400x300'}
        ],
        "New York": [
            {'id':'n1','name':'Manhattan Hotel','price':220,'address':'5th Ave, New York','rating':4.3,'photo':'https://via.placeholder.com/400x300'},
            {'id':'n2','name':'Central Park Inn','price':240,'address':'59th St & 5th Ave, NY','rating':4.6,'photo':'https://via.placeholder.com/400x300'},
            {'id':'n3','name':'Times Square Lodge','price':200,'address':'Times Square, New York','rating':4.0,'photo':'https://via.placeholder.com/400x300'},
            {'id':'n4','name':'Empire State Suites','price':260,'address':'350 5th Ave, NY','rating':4.7,'photo':'https://via.placeholder.com/400x300'},
            {'id':'n5','name':'Brooklyn Retreat','price':180,'address':'Brooklyn, New York','rating':4.2,'photo':'https://via.placeholder.com/400x300'}
        ],
        "Tokyo": [
            {'id':'t1','name':'Shinjuku Stay','price':190,'address':'Shinjuku, Tokyo','rating':4.3,'photo':'https://via.placeholder.com/400x300'},
            {'id':'t2','name':'Asakusa Inn','price':180,'address':'Asakusa, Tokyo','rating':4.4,'photo':'https://via.placeholder.com/400x300'},
            {'id':'t3','name':'Ginza Grand','price':250,'address':'Ginza, Tokyo','rating':4.6,'photo':'https://via.placeholder.com/400x300'},
            {'id':'t4','name':'Akihabara Hotel','price':170,'address':'Akihabara, Tokyo','rating':4.1,'photo':'https://via.placeholder.com/400x300'},
            {'id':'t5','name':'Tokyo Bay Resort','price':230,'address':'Odaiba, Tokyo','rating':4.5,'photo':'https://via.placeholder.com/400x300'}
        ]
    }
    return fallback.get(city, [])


def get_hotels(city, check_in, check_out):
    """Fetch hotels from RapidAPI, fallback to static list if needed"""
    hotels = []
    try:
        city_id = get_city_id(city)
        if city_id:
            url = f"https://{RAPIDAPI_HOST}/v1/hotels/search"
            params = {
                "checkin_date": check_in,
                "checkout_date": check_out,
                "dest_id": city_id,
                "dest_type": "city",
                "room_number": "1",
                "children_number": "0",
                "currency": "USD",
                "units": "metric",
                "adults_number": "2",
                "order_by": "popularity",
                "locale": "en-gb",
                "page_number": "0"
            }
            headers = {
                "X-RapidAPI-Key": RAPIDAPI_KEY,
                "X-RapidAPI-Host": RAPIDAPI_HOST
            }
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            hotels = parse_hotel_data(response.json())
    except Exception as e:
        print(f"Hotel API Error: {e}")

    # Use fallback if API fails or returns empty
    return hotels or get_fallback_hotels(city)


def get_city_id(city_name):
    """Map city names to API-specific IDs"""
    city_mapping = {
        "Paris": "-1456928",
        "London": "-2601889",
        "New York": "-553173",
        "Tokyo": "-246227"
    }
    return city_mapping.get(city_name)


def parse_hotel_data(response):
    """Extract relevant hotel data from API response"""
    hotels = []
    for hotel in response.get('result', [])[:5]:  # Limit to 5
        hotels.append({
            'id': str(hotel.get('hotel_id', '')),
            'name': hotel.get('hotel_name', ''),
            'price': hotel.get('min_total_price', 0),
            'address': hotel.get('address', ''),
            'rating': round(float(hotel.get('review_score', 0)), 1),
            'photo': hotel.get('main_photo_url', '').replace("square60", "max500") if hotel.get('main_photo_url') else None
        })
    return hotels


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        dest = request.form['destination']
        check_in = request.form['check_in']
        check_out = request.form['check_out']
        # Validate dates
        try:
            in_date = datetime.strptime(check_in, '%Y-%m-%d')
            out_date = datetime.strptime(check_out, '%Y-%m-%d')
            if out_date <= in_date:
                flash('Check-out date must be after check-in date.', 'danger')
                return redirect(url_for('index'))
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(url_for('index'))
        session['destination'] = dest
        session['check_in'] = check_in
        session['check_out'] = check_out
        return redirect(url_for('results'))
    return render_template('index.html')


@app.route('/results')
def results():
    destination = session.get('destination')
    raw_check_in = session.get('check_in')
    raw_check_out = session.get('check_out')
    if not all([destination, raw_check_in, raw_check_out]):
        return redirect(url_for('index'))
    formatted_in = datetime.strptime(raw_check_in, '%Y-%m-%d').strftime('%B %d, %Y')
    formatted_out = datetime.strptime(raw_check_out, '%Y-%m-%d').strftime('%B %d, %Y')
    weather = get_weather(destination)
    hotels = get_hotels(destination, raw_check_in, raw_check_out)
    return render_template('results.html', destination=destination, check_in=formatted_in, check_out=formatted_out, weather=weather, hotels=hotels)


@app.route('/payment/<hotel_id>', methods=['GET', 'POST'])
def payment(hotel_id):
    dest = session.get('destination')
    in_date = session.get('check_in')
    out_date = session.get('check_out')
    hotels = get_hotels(dest, in_date, out_date)
    hotel = next((h for h in hotels if h['id'] == hotel_id), None)
    if not hotel:
        return redirect(url_for('results'))
    nights = (datetime.strptime(out_date, '%Y-%m-%d') - datetime.strptime(in_date, '%Y-%m-%d')).days
    total = int(hotel['price']) * nights
    if request.method == 'POST':
        session['booking_details'] = {'hotel': hotel, 'total': total, 'nights': nights}
        return redirect(url_for('confirmation'))
    return render_template('payment.html', hotel=hotel, nights=nights, total=total, check_in=in_date, check_out=out_date)


@app.route('/confirmation')
def confirmation():
    details = session.get('booking_details')
    if not details:
        return redirect(url_for('index'))

    hotel  = details['hotel']
    nights = details['nights']
    total  = details['total']

    return render_template(
      'confirmation.html',
      hotel=hotel,
      nights=nights,
      total=total
    )
if __name__ == '__main__':
    app.run(debug=True)

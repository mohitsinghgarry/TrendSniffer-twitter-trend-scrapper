from flask import Flask, jsonify, render_template, request
from selenium_script import fetch_trends  # Import your script's fetch function
from pymongo import MongoClient
from datetime import datetime
from templates.config import Config

# Flask app setup
app = Flask(__name__)

# MongoDB setup
client = MongoClient(Config.MONGO_URL)
db = client['twitter_trends']
collection = db['trends']

@app.route('/')
def index():
    """Render the main HTML page."""
    return render_template('index.html')

@app.route('/fetch_trends', methods=['GET'])
def fetch_and_show_trends():
    """Fetch trends using the Python script and return JSON response."""
    try:
        # Run the Python script to fetch trends
        fetch_trends()

        # Retrieve the latest trends from MongoDB
        latest_trend = collection.find_one(sort=[('timestamp', -1)])
        if latest_trend and 'trends' in latest_trend:
            return jsonify(
                success=True,
                trends=latest_trend['trends'],
                timestamp=latest_trend['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                ip_address=latest_trend['ip_address']
            )
        else:
            return jsonify(success=False, message="No trends found in the database.")
    except Exception as e:
        return jsonify(success=False, message=str(e))

@app.route('/fetch_trends_by_date', methods=['GET'])
def fetch_trends_by_date():
    """Fetch unique trends by the selected date."""
    try:
        selected_date = request.args.get('date')
        if not selected_date:
            return jsonify(success=False, message="Please provide a valid date.")

        # Convert selected date to datetime object
        selected_datetime = datetime.strptime(selected_date, '%Y-%m-%d')

        # Find trends on the selected date (ignore time part by comparing only the date)
        trends_by_date = collection.find({
            'timestamp': {
                '$gte': selected_datetime,
                '$lt': selected_datetime.replace(hour=23, minute=59, second=59, microsecond=999999)
            }
        }).sort('timestamp', -1)

        trends_data = []
        seen_trends = set()  # To store unique trends

        for trend in trends_by_date:
            # Filter only unique trends
            unique_trends = [t for t in trend['trends'] if t not in seen_trends]
            seen_trends.update(unique_trends)

            if unique_trends:  # If there are any unique trends to show
                trends_data.append({
                    'timestamp': trend['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                    'trends': unique_trends,
                    'ip_address': trend['ip_address']
                })

        if trends_data:
            return jsonify(success=True, trends=trends_data)
        else:
            return jsonify(success=False, message="No trends found for the selected date.")

    except Exception as e:
        return jsonify(success=False, message=str(e))

if __name__ == '__main__':
    app.run(debug=True)

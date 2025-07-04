from flask import Flask, jsonify, request
from datetime import date
from src.mental_insights_database import InsightsDatabase

app = Flask(__name__)

IOT_PATH = 'data/university_mental_health_iot_dataset.csv'
DATABASE_PATH = 'data/mental_insights.db'
TOP_N = 5

INSIGHTS_DB = InsightsDatabase(DATABASE_PATH, IOT_PATH, TOP_N)


@app.route('/mental-insights', methods=['GET'])
def mental_insights():
    """
    GET endpoint for mental insights
    
    Returns mental health insights for the entire dataset, including top stress features
    and their correlations with stress levels.
    
    Returns:
        JSON: A JSON response containing mental health insights for the whole dataset
    """
    return jsonify(INSIGHTS_DB.get_insights_on_whole_set())


@app.route('/mental-insights-by-day', methods=['GET'])
def mental_insights_by_day():
    """
    GET endpoint for mental insights by specific date
    
    Returns mental health insights for a specific date. If no date is provided,
    returns insights for today. The date should be in YYYY-MM-DD format.
    
    Query Parameters:
        date (str, optional): Date in YYYY-MM-DD format. If not provided, uses today's date.
    
    Returns:
        JSON: A JSON response containing mental health insights for the specified date
              or an error message if the date is invalid or no data is found
    
    Raises:
        400: If the date format is invalid
        404: If no insights are found for the specified date
    """
    # Check if a specific date is requested
    requested_date = request.args.get('date')

    if requested_date is None:
        day = date.today()
    else:
        try:
            day = date.fromisoformat(requested_date)
        except ValueError:
            return jsonify({
                "error": "Invalid date format. Use YYYY-MM-DD"
            }), 400

    stored_insights = INSIGHTS_DB.get_mental_insights_by_day(day)

    if stored_insights:
        return jsonify({
            "date": day.isoformat(),
            "insights": stored_insights,
            "source": "database"
        })
    else:
        return jsonify({
            "error": "No insights found for the specified date",
            "date": day.isoformat()
        }), 404


@app.route('/', methods=['GET'])
def home():
    """
    Home endpoint
    
    Returns basic information about the Mental Insights Flask API and available endpoints.
    
    Returns:
        JSON: A JSON response containing API information and available endpoints
    """
    return jsonify({
        "message": "Mental Insights Flask API",
        "endpoints": {
            "mental-insights": "/mental-insights",
            "mental-insights-all-days": "/mental-insights-all-days",
            "mental-insights-by-day": "/mental-insights-by-day?date=YYYY-MM-DD"
        }
    })


@app.route('/mental-insights-all-days', methods=['GET'])
def all_insights():
    """
    GET endpoint to retrieve all stored mental insights
    
    Returns mental health insights for all available dates in the database.
    
    Returns:
        JSON: A JSON response containing the total number of records and insights
              for all available dates
    """
    all_stored_insights = INSIGHTS_DB.get_mental_insights_for_all_days()

    return jsonify({
        "total_records": len(all_stored_insights),
        "insights": [
            {
                "date": day,
                "insights": insights_data
            }
            for day, insights_data in all_stored_insights
        ]
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

# Mental Insights Flask API

A Flask-based REST API that analyzes university mental health IoT data to provide insights about stress levels and their correlations with various environmental and physiological factors.

## Overview

This application processes a university mental health IoT dataset to identify the top factors that correlate with student stress levels. The system:

- Analyzes correlations between stress levels and other features in the dataset
- Stores daily insights in a SQLite database
- Provides REST API endpoints to access insights for specific dates or the entire dataset
- Preprocesses IoT data by adding timestamp-based features for better analysis

## Architecture

### Core Components

1. **Flask Application** (`app.py`): Main API server with REST endpoints
2. **Insights Database** (`src/mental_insights_database.py`): Database operations and data analysis
3. **SQLite Database** (`data/mental_insights.db`): Persistent storage for daily insights
4. **IoT Dataset** (`data/university_mental_health_iot_dataset.csv`): Source data for analysis
5. **Exploratory Notebook** (`scripts/data_exploration.ipynb`): Exploratory notebook analyzing data and doing correlation studies 
6. **Exploratory Notebook HTML output** (`output/data_exploration.html`): HTML output of exploratory notebook

### Data Processing

The system processes IoT data by:
- Extracting various time based features in addition to the provided features
- Calculating correlations between stress levels and all other features
- Identifying the top N features with highest correlation to stress levels

## Setup

1. Install venv and then add dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
Note that `requirements.in` contains the initial requirements and `requirements.txt` contains
the currently frozen version of the requirements. For the future, there should be a Dockerfile
with this script so the environment can be put into a docker image. 

2. Ensure the IoT dataset is available at `data/university_mental_health_iot_dataset.csv`

3. Run the application:
```bash
python app.py
```

The server will start on `http://localhost:5000`

## Database

The application uses SQLite to store mental insights by day. The database file `mental_insights.db` is automatically created when the app starts.

### Database Schema

- **Table**: `mental_insights_by_day`
- **Columns**:
  - `day` (DATE, PRIMARY KEY) - The date for the insights
  - `mental_insights_json` (TEXT) - JSON string containing the insights data

### Data Structure

Each insight record contains:
```json
{
  "top_stress_features": ["feature1", "feature2", ...],
  "correlations": [
    ["feature1", 0.85],
    ["feature2", -0.72],
    ...
  ]
}
```

## API Endpoints

### `GET /`
**Home endpoint** - Returns API information and available endpoints

**Response:**
```json
{
  "message": "Mental Insights Flask API",
  "endpoints": {
    "mental-insights": "/mental-insights",
    "mental-insights-all-days": "/mental-insights-all-days",
    "mental-insights-by-day": "/mental-insights-by-day"
  }
}
```

### `GET /mental-insights`
**Dataset insights** - Returns mental health insights for the entire dataset

**Response:**
```json
{
  "top_stress_features": ["feature1", "feature2", ...],
  "correlations": [
    ["feature1", 0.85],
    ["feature2", -0.72],
    ...
  ]
}
```

### `GET /mental-insights-by-day`
**Daily insights** - Returns mental health insights for a specific date

**Query Parameters:**
- `date` (optional): Date in YYYY-MM-DD format

**Response (with date parameter):**
```json
{
  "date": "2025-01-15",
  "insights": {
    "top_stress_features": ["feature1", "feature2", ...],
    "correlations": [["feature1", 0.85], ...]
  },
  "source": "database"
}
```

**Error Responses:**
- `400`: Invalid date format
- `404`: No insights found for the specified date

### `GET /mental-insights-all-days`
**All daily insights** - Returns mental health insights for all available dates

**Response:**
```json
{
  "total_records": 30,
  "insights": [
    {
      "date": "2025-01-15",
      "insights": {
        "top_stress_features": ["feature1", "feature2", ...],
        "correlations": [["feature1", 0.85], ...]
      }
    },
    ...
  ]
}
```

## Example Usage

```bash
# Get API information
curl http://localhost:5000/

# Get insights for the entire dataset
curl http://localhost:5000/mental-insights

# Get insights for a specific date
curl "http://localhost:5000/mental-insights-by-day?date=2025-01-03"

# Get insights for all available dates
curl http://localhost:5000/mental-insights-all-days
```

## Code Structure

### Key Functions

**Data Analysis:**
- `get_stress_level_insights()`: Analyzes correlations between stress levels and other features
- `generate_insights_from_iot_data()`: Processes IoT data and generates daily insights

**Database Operations:**
- `execute_db_command()`: Unified database command execution
- `insert_mental_insights_for_day()`: Stores insights for a specific date
- `get_mental_insights_by_day()`: Retrieves insights for a specific date
- `get_mental_insights_for_all_days()`: Retrieves all stored insights

**API Endpoints:**
- `mental_insights()`: Returns dataset-wide insights
- `mental_insights_by_day()`: Returns date-specific insights
- `all_insights()`: Returns all daily insights
- `home()`: Returns API information

## Configuration

The application uses the following configuration constants:
- `IOT_PATH`: Path to the IoT dataset CSV file
- `DATABASE_PATH`: Path to the SQLite database file
- `TOP_N`: Number of top stress features to analyze (default: 5)

## Dependencies

Key dependencies include:
- Flask: Web framework
- pandas: Data manipulation and analysis
- numpy: Numerical computations
- sqlite3: Database operations

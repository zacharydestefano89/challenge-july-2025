import sqlite3
import json
from datetime import date
from typing import Dict, Any
import pandas as pd
import numpy as np

CREATE_TABLE_COMMAND = """
    CREATE TABLE IF NOT EXISTS mental_insights_by_day (
                day DATE PRIMARY KEY,
                mental_insights_json TEXT NOT NULL
            )"""


def get_stress_level_insights(df_to_check, top_n):
    """
    Analyze stress level correlations with other features in the dataset.
    
    This function calculates the correlation between stress_level and all other features
    in the dataset, then returns the top N features with the highest absolute correlation
    values, sorted in descending order.
    
    Args:
        df_to_check (pd.DataFrame): DataFrame containing the dataset with stress_level column
        top_n (int): Number of top stress features to return
    
    Returns:
        dict: Dictionary containing:
            - 'top_stress_features': List of feature names with highest correlation to stress
            - 'correlations': List of tuples (feature_name, correlation_value) sorted by absolute correlation
    """
    tuples = \
        [(col_name, correlation_value)
         for col_name, correlation_value in dict(df_to_check.corr()['stress_level']).items()
         if col_name != 'stress_level' and not np.isnan(correlation_value)]

    # sort in descending order (hence the negative) by absolute correlation value
    tuples.sort(key=lambda tup: -1 * np.abs(tup[1]))
    return \
        {
            'top_stress_features': [tup[0] for tup in tuples[:top_n]],
            'correlations': tuples[:top_n]
            # keeping the list of tuples on purpose so it displays in order
        }


def execute_db_command(database_path: str, command: str, params_tuple=None, to_fetch: str = None):
    """
    Execute a database command on the SQLite database.
    
    This function provides a unified interface for executing SQL commands on the database,
    handling connection management, and returning results as needed.
    
    Args:
        database_path (str): Path to the SQLite database file
        command (str): SQL command to execute
        params_tuple (tuple, optional): Parameters for the SQL command. Defaults to None.
        to_fetch (str, optional): Type of fetch operation. Options: 'one', 'all', or None. Defaults to None.
    
    Returns:
        Any: Query results if to_fetch is specified, None otherwise
    """
    if params_tuple is None:
        params_tuple = ()
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Create the mental_insights_by_day table
    cursor.execute(command, params_tuple)

    result = None
    if to_fetch == 'one':
        result = cursor.fetchone()
    elif to_fetch == 'all':
        result = cursor.fetchall()

    conn.commit()
    conn.close()

    return result


class InsightsDatabase:

    def __init__(self, database_path: str, iot_file_path: str, top_n: int):
        """
        Initialize the InsightsDatabase with database and IoT data file paths.
        
        This constructor sets up the database connection, creates the necessary table
        if it doesn't exist, and generates insights from the IoT data.
        
        Args:
            database_path (str): Path to the SQLite database file
            iot_file_path (str): Path to the IoT dataset CSV file
            top_n (int): Number of top stress features to analyze
        """
        self.insights_on_whole_set = None
        self.database_path = database_path
        execute_db_command(self.database_path, CREATE_TABLE_COMMAND)
        self.top_n = top_n
        self.iot_file_path = iot_file_path
        self.generate_insights_from_iot_data()

    def insert_mental_insights_for_day(self, _day: date, insights: Dict[str, Any]) -> bool:
        """
        Insert or update mental insights for a specific day in the database.
        
        This method stores mental health insights for a given date in the database.
        If insights already exist for that date, they will be replaced.
        
        Args:
            _day (date): The date for which to store insights
            insights (Dict[str, Any]): Dictionary containing mental health insights
        
        Returns:
            bool: True if the operation was successful
        """
        cmd_to_run = f"""
        INSERT OR REPLACE INTO mental_insights_by_day (day, mental_insights_json)
                VALUES (?, ?)
        """
        execute_db_command(self.database_path,
                           cmd_to_run,
                           params_tuple=(_day.isoformat(), json.dumps(insights)))

    def generate_insights_from_iot_data(self):
        """
        Generate mental health insights from the IoT dataset.
        
        This method reads the IoT dataset, preprocesses the data by adding timestamp-based
        features, generates insights for the entire dataset, and then creates daily insights
        for each unique date in the dataset.
        
        The method adds several derived features:
        - timestamp_day: Date extracted from timestamp
        - timestamp_day_of_month: Day of month
        - timestamp_hour: Hour of day
        - timestamp_hour_4_hour_bucket: 4-hour time buckets
        - timestamp_hour_6_hour_bucket: 6-hour time buckets
        """
        iot_data = pd.read_csv(self.iot_file_path)

        # pre-compute the mental insights
        iot_data['timestamp'] = pd.to_datetime(iot_data['timestamp'])
        iot_data['timestamp_day'] = iot_data['timestamp'].dt.date
        iot_data['timestamp_day_of_month'] = iot_data['timestamp'].dt.day
        iot_data['timestamp_day_of_week'] = iot_data['timestamp'].apply(lambda x: x.isoweekday())
        iot_data['timestamp_hour'] = iot_data['timestamp'].dt.hour
        iot_data['timestamp_hour_4_hour_bucket'] = iot_data['timestamp'].dt.hour // 4
        iot_data['timestamp_hour_6_hour_bucket'] = iot_data['timestamp'].dt.hour // 6

        self.insights_on_whole_set = get_stress_level_insights(
            iot_data.drop('timestamp_day', axis=1), self.top_n)

        iot_data_by_day = iot_data.drop('timestamp_day_of_week', axis=1).set_index('timestamp_day')
        for _day in set(iot_data_by_day.index):
            insights = get_stress_level_insights(iot_data_by_day.loc[_day], self.top_n)
            self.insert_mental_insights_for_day(_day, insights)

    def get_insights_on_whole_set(self):
        """
        Get mental health insights for the entire dataset.
        
        Returns:
            dict: Dictionary containing top stress features and correlations for the entire dataset
        """
        return self.insights_on_whole_set

    def get_mental_insights_by_day(self, day: date) -> Dict[str, Any]:
        """
        Retrieve mental health insights for a specific day.
        
        Args:
            day (date): The date for which to retrieve insights
        
        Returns:
            Dict[str, Any]: Dictionary containing mental health insights for the specified day,
                           or None if no insights are found for that date
        """
        cmd_to_run = f"""
            SELECT mental_insights_json 
            FROM mental_insights_by_day 
            WHERE day = ?"""
        result = execute_db_command(self.database_path,
                                    cmd_to_run,
                                    params_tuple=(day.isoformat(),),
                                    to_fetch='one')

        if result:
            return json.loads(result[0])
        return None

    def get_mental_insights_for_all_days(self) -> list:
        """
        Retrieve mental health insights for all available dates.
        
        Returns:
            list: List of tuples containing (date, insights) for all available dates,
                  sorted by date in ascending order
        """
        cmd_to_run = f"""
            SELECT day, mental_insights_json 
            FROM mental_insights_by_day 
            ORDER BY day"""
        results = execute_db_command(self.database_path, cmd_to_run, to_fetch='all')

        return [(row[0], json.loads(row[1])) for row in results]

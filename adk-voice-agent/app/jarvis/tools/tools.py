from datetime import datetime
import requests
import os
from typing import Dict, Any, Optional


def get_current_time() -> dict:
    """
    Get the current time in the format YYYY-MM-DD HH:MM:SS
    """
    return {
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def get_current_weather(latitude: float, longitude: float, units_system: str = "METRIC") -> Dict[str, Any]:
    """
    Get current weather conditions for a specific location using Google Weather API
    
    Args:
        latitude (float): Latitude coordinate of the location
        longitude (float): Longitude coordinate of the location
        units_system (str): Unit system - "METRIC" or "IMPERIAL" (default: "METRIC")
    
    Returns:
        dict: JSON response containing current weather conditions
    """
    # Get API key from environment variable
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        return {
            "error": "Google Weather API key not found. Please set GOOGLE_API_KEY environment variable."
        }
    
    # Validate units_system parameter
    if units_system not in ["METRIC", "IMPERIAL"]:
        return {
            "error": "Invalid units_system. Must be 'METRIC' or 'IMPERIAL'"
        }
    
    # Construct the API URL
    base_url = "https://weather.googleapis.com/v1/currentConditions:lookup"
    params = {
        "key": api_key,
        "location.latitude": latitude,
        "location.longitude": longitude,
        "unitsSystem": units_system
    }
    
    try:
        # Make the API request
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Return the JSON response
        return response.json()
        
    except requests.exceptions.RequestException as e:
        return {
            "error": f"Failed to fetch weather data: {str(e)}"
        }
    except ValueError as e:
        return {
            "error": f"Invalid JSON response: {str(e)}"
        }


def get_weather_forecast(latitude: float, longitude: float, days: int = 10, units_system: str = "METRIC", page_size: Optional[int] = None, page_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Get weather forecast for up to 10 days for a specific location using Google Weather API
    
    Args:
        latitude (float): Latitude coordinate of the location
        longitude (float): Longitude coordinate of the location
        days (int): Number of days to forecast (1-10, default: 10)
        units_system (str): Unit system - "METRIC" or "IMPERIAL" (default: "METRIC")
        page_size (int, optional): Number of days per page (default: 5)
        page_token (str, optional): Token for pagination to get next page of results
    
    Returns:
        dict: JSON response containing weather forecast data
    """
    # Get API key from environment variable
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        return {
            "error": "Google Weather API key not found. Please set GOOGLE_API_KEY environment variable."
        }
    
    # Validate parameters
    if not 1 <= days <= 10:
        return {
            "error": "Invalid days parameter. Must be between 1 and 10."
        }
    
    if units_system not in ["METRIC", "IMPERIAL"]:
        return {
            "error": "Invalid units_system. Must be 'METRIC' or 'IMPERIAL'"
        }
    
    # Construct the API URL
    base_url = "https://weather.googleapis.com/v1/forecast/days:lookup"
    params = {
        "key": api_key,
        "location.latitude": latitude,
        "location.longitude": longitude,
        "days": days,
        "unitsSystem": units_system
    }
    
    # Add optional parameters if provided
    if page_size is not None:
        params["pageSize"] = page_size
    
    if page_token is not None:
        params["pageToken"] = page_token
    
    try:
        # Make the API request
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Return the JSON response
        return response.json()
        
    except requests.exceptions.RequestException as e:
        return {
            "error": f"Failed to fetch forecast data: {str(e)}"
        }
    except ValueError as e:
        return {
            "error": f"Invalid JSON response: {str(e)}"
        } 
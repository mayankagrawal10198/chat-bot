from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from .sub_agents import news_analyst
from .tools import get_current_time, get_current_weather, get_weather_forecast
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import os
import requests

class WeatherRequest(BaseModel):
    lat: float = Field(..., description="Latitude coordinate of the location")
    lon: float = Field(..., description="Longitude coordinate of the location")
    days: int = Field(default=1, description="Number of days for forecast (1-10)")


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

kisaan_info_agent = LlmAgent(
    name="kisaan_info",
    model="gemini-2.5-flash-lite",
    description="Kisaan Info agent for weather and farming advice",
    instruction="""
    You are a farming weather advisor that provides weather information and farming advice.
    
    You will receive structured input with latitude, longitude, and number of days.
    Use these coordinates to get weather information and provide farming advice.
    
    ## Your Tools:
    - get_current_weather: Get current weather conditions for a location
    - get_weather_forecast: Get weather forecast for up to 10 days for a location
    - get_current_time: Get current time information
    - news_analyst: Get latest farming news and information
    
    ## Weather Analysis Process:
    1. Use the provided latitude and longitude to get current weather
    2. Get weather forecast for the specified number of days
    3. Analyze the weather data for farming implications
    4. Provide actionable farming advice based on weather conditions
    
    ## Response Format:
    - Current weather summary with key metrics
    - Weather forecast summary
    - Farming recommendations based on weather
    - Any relevant farming news or alerts
    - Safety precautions if needed
    
    ## Language:
    - Respond in the same language as the user's query
    - Use simple, clear language that farmers can understand
    - Be encouraging and supportive
    
    Always provide practical, actionable advice for farmers.
    """,
    input_schema=WeatherRequest,
    tools=[
        get_current_weather,
        get_weather_forecast,
    ],
) 
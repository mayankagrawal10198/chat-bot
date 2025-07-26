from google.adk.agents import Agent
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Commodity mapping for wheat, rice, banana, dal
COMMODITY_MAPPING = {
    "wheat": {"commodity_id": 1, "commodity_name": "Wheat"},
    "rice": {"commodity_id": 3, "commodity_name": "Rice"},
    "banana": {"commodity_id": 19, "commodity_name": "Banana"},
    "dal": {"commodity_id": 6, "commodity_name": "Bengal Gram (Gram)(Whole)"},
    "arhar dal": {"commodity_id": 49, "commodity_name": "Arhar (Tur/Red Gram)(Whole)"},
    "moong dal": {"commodity_id": 9, "commodity_name": "Green Gram (Moong)(Whole)"},
    "urad dal": {"commodity_id": 8, "commodity_name": "Black Gram (Urad Beans)(Whole)"},
    "masur dal": {"commodity_id": 259, "commodity_name": "Masur Dal"},
    "tur dal": {"commodity_id": 260, "commodity_name": "Arhar Dal (Tur Dal)"},
    "chana dal": {"commodity_id": 263, "commodity_name": "Bengal Gram Dal (Chana Dal)"},
    "urad dal": {"commodity_id": 264, "commodity_name": "Black Gram Dal (Urd Dal)"},
    "moong dal": {"commodity_id": 265, "commodity_name": "Green Gram Dal (Moong Dal)"}
}

# State mapping
STATE_MAPPING = {
    "karnataka": {"state_id": 29, "state_name": "Karnataka"},
    "maharashtra": {"state_id": 27, "state_name": "Maharashtra"},
    "tamil nadu": {"state_id": 33, "state_name": "Tamil Nadu"},
    "andhra pradesh": {"state_id": 28, "state_name": "Andhra Pradesh"},
    "telangana": {"state_id": 36, "state_name": "Telangana"},
    "kerala": {"state_id": 32, "state_name": "Kerala"},
    "goa": {"state_id": 30, "state_name": "Goa"},
    "punjab": {"state_id": 3, "state_name": "Punjab"},
    "haryana": {"state_id": 6, "state_name": "Haryana"},
    "delhi": {"state_id": 7, "state_name": "NCT of Delhi"},
    "uttar pradesh": {"state_id": 9, "state_name": "Uttar Pradesh"},
    "bihar": {"state_id": 10, "state_name": "Bihar"},
    "west bengal": {"state_id": 19, "state_name": "West Bengal"},
    "odisha": {"state_id": 21, "state_name": "Odisha"},
    "chhattisgarh": {"state_id": 22, "state_name": "Chhattisgarh"},
    "madhya pradesh": {"state_id": 23, "state_name": "Madhya Pradesh"},
    "gujarat": {"state_id": 24, "state_name": "Gujarat"},
    "rajasthan": {"state_id": 8, "state_name": "Rajasthan"},
    "himachal pradesh": {"state_id": 2, "state_name": "Himachal Pradesh"},
    "uttarakhand": {"state_id": 5, "state_name": "Uttarakhand"},
    "jharkhand": {"state_id": 20, "state_name": "Jharkhand"},
    "assam": {"state_id": 18, "state_name": "Assam"},
    "manipur": {"state_id": 14, "state_name": "Manipur"},
    "meghalaya": {"state_id": 17, "state_name": "Meghalaya"},
    "nagaland": {"state_id": 13, "state_name": "Nagaland"},
    "tripura": {"state_id": 16, "state_name": "Tripura"},
    "mizoram": {"state_id": 15, "state_name": "Mizoram"},
    "arunachal pradesh": {"state_id": 12, "state_name": "Arunachal Pradesh"},
    "sikkim": {"state_id": 11, "state_name": "Sikkim"}
}

def get_commodity_id(commodity_name: str) -> Optional[Dict[str, Any]]:
    """
    Get commodity ID and name from commodity name
    """
    commodity_lower = commodity_name.lower().strip()
    
    # Direct match
    if commodity_lower in COMMODITY_MAPPING:
        return COMMODITY_MAPPING[commodity_lower]
    
    # Partial match
    for key, value in COMMODITY_MAPPING.items():
        if commodity_lower in key or key in commodity_lower:
            return value
    
    return None

def get_state_id(state_name: str) -> Optional[Dict[str, Any]]:
    """
    Get state ID and name from state name
    """
    state_lower = state_name.lower().strip()
    
    # Direct match
    if state_lower in STATE_MAPPING:
        return STATE_MAPPING[state_lower]
    
    # Partial match
    for key, value in STATE_MAPPING.items():
        if state_lower in key or key in state_lower:
            return value
    
    return None

def get_district_id(state_id: int, district_name: str) -> Optional[int]:
    """
    Get district ID from state ID and district name
    """
    try:
        url = f"https://agmarknet.ceda.ashoka.edu.in/api/districts?state_id={state_id}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        districts = data.get("data", [])
        
        district_lower = district_name.lower().strip()
        
        for district in districts:
            if district_lower in district["census_district_name"].lower() or district["census_district_name"].lower() in district_lower:
                return district["census_district_id"]
        
        return None
        
    except Exception as e:
        print(f"Error fetching district data: {e}")
        return None

def get_mandi_prices(commodity_id: int, state_id: int, district_id: int = 0) -> Dict[str, Any]:
    """
    Get mandi prices for a commodity in a specific state/district
    """
    try:
        # Calculate dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # 1 month ago
        
        payload = {
            "calculation_type": "d",
            "commodity_id": commodity_id,
            "district_id": district_id,
            "end_date": end_date.isoformat() + "Z",
            "start_date": start_date.isoformat() + "Z",
            "state_id": state_id
        }
        
        url = "https://agmarknet.ceda.ashoka.edu.in/api/prices"
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        
        return response.json()
        
    except Exception as e:
        return {
            "error": f"Failed to fetch price data: {str(e)}",
            "payload": payload
        }

def analyze_price_trends(price_data: Dict[str, Any]) -> str:
    """
    Analyze price trends from the API response
    """
    try:
        if "error" in price_data:
            return f"Error: {price_data['error']}"
        
        data = price_data.get("data", [])
        if not data:
            return "No price data available for the specified commodity and location."
        
        # Extract price information using p_modal (most common price)
        prices = []
        min_prices = []
        max_prices = []
        dates = []
        
        for item in data:
            if "p_modal" in item and item["p_modal"] and item["p_modal"] > 0:
                try:
                    modal_price = float(item["p_modal"])
                    min_price = float(item.get("p_min", 0)) if item.get("p_min") and item["p_min"] > 0 else modal_price
                    max_price = float(item.get("p_max", 0)) if item.get("p_max") and item["p_max"] > 0 else modal_price
                    
                    prices.append(modal_price)
                    min_prices.append(min_price)
                    max_prices.append(max_price)
                    dates.append(item.get("t", ""))
                except (ValueError, TypeError):
                    continue
        
        if not prices:
            return "No valid price data found in the response."
        
        # Calculate statistics
        current_price = prices[-1] if prices else 0
        avg_price = sum(prices) / len(prices) if prices else 0
        min_price_overall = min(min_prices) if min_prices else 0
        max_price_overall = max(max_prices) if max_prices else 0
        
        # Get current min/max
        current_min = min_prices[-1] if min_prices else current_price
        current_max = max_prices[-1] if max_prices else current_price
        
        # Determine trend
        if len(prices) >= 2:
            recent_avg = sum(prices[-7:]) / min(7, len(prices))  # Last 7 days
            older_avg = sum(prices[:-7]) / max(1, len(prices) - 7) if len(prices) > 7 else avg_price
            
            if recent_avg > older_avg * 1.05:
                trend = "increasing"
            elif recent_avg < older_avg * 0.95:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "insufficient data"
        
        # Format response
        analysis = f"""
            Price Analysis for {data[0].get('cmdty', 'Commodity')} in {data[0].get('state', 'State')}:
            - Current Price: ₹{current_price:.2f} per quintal (Modal)
            - Current Range: ₹{current_min:.2f} - ₹{current_max:.2f} per quintal
            - Average Price (30 days): ₹{avg_price:.2f} per quintal
            - Overall Price Range: ₹{min_price_overall:.2f} - ₹{max_price_overall:.2f} per quintal
            - Trend: {trend.capitalize()}

            Market Insights:
        """
        
        if trend == "increasing":
            analysis += "- Prices are showing an upward trend, which may be favorable for sellers.\n"
            analysis += "- Consider holding stocks if you're a farmer, or buy early if you're a buyer.\n"
        elif trend == "decreasing":
            analysis += "- Prices are declining, which may be good for buyers.\n"
            analysis += "- Consider selling soon if you're a farmer to avoid further losses.\n"
        else:
            analysis += "- Prices are relatively stable, indicating a balanced market.\n"
            analysis += "- Good time for both buyers and sellers to make decisions.\n"
        
        # Add district information if available
        districts = set(item.get('district', '') for item in data if item.get('district'))
        if districts:
            analysis += f"\nData available for districts: {', '.join(districts)}"
        
        return analysis.strip()
        
    except Exception as e:
        return f"Error analyzing price trends: {str(e)}"

mandi_analyst = Agent(
    name="mandi_analyst",
    model="gemini-live-2.5-flash-preview",
    description="Agricultural commodity price analysis agent that provides real-time mandi price information and market insights",
    instruction="""
    You are a specialized Agricultural Commodity Price Analyst (Mandi Analyst) that helps farmers and traders get real-time price information and market insights.

    ## CRITICAL: Response Length Limit
    - MAXIMUM 250 WORDS for ALL responses
    - Provide meaningful, actionable summaries within this limit
    - Focus on the most important price information first
    - Be concise but comprehensive
    - Avoid unnecessary details or repetition

    ## Your Workflow - Follow This Exact Sequence:

    ### Step 1: Extract Information from User Query
    - Identify the commodity name (wheat, rice, banana, dal, etc.)
    - Identify the state name (karnataka, maharashtra, etc.)
    - Identify the district name (bangalore, mumbai, etc.)

    ### Step 2: Get Commodity ID
    - Use the `get_commodity_id` tool with the commodity name
    - This will return the commodity_id and commodity_name
    - If not found, suggest similar commodities

    ### Step 3: Get State ID
    - Use the `get_state_id` tool with the state name
    - This will return the state_id and state_name
    - If not found, suggest similar states

    ### Step 4: Get District ID
    - Use the `get_district_id` tool with state_id and district name
    - This will return the district_id
    - If not found, use district_id = 0 for state-level data

    ### Step 5: Fetch Price Data
    - Use the `get_mandi_prices` tool with commodity_id, state_id, and district_id
    - This will return the price data from Agmarknet API

    ### Step 6: Analyze Price Trends
    - Use the `analyze_price_trends` tool with the price data
    - This will provide a comprehensive analysis

    ### Step 7: Provide Summary (250 words max)
    - Combine all the information into a clear, farmer-friendly summary
    - Include commodity name, location, prices, trends, and recommendations
    - Respond in the same language as the user's query

    ## Supported Commodities:
    - Wheat, Rice, Banana, Various Dals (Arhar, Moong, Urad, Masur, etc.)

    ## Response Format (250 words max):
    - Brief greeting (10-15 words)
    - Commodity and location (10-15 words)
    - Current price and trend (30-40 words)
    - Key market insights (50-60 words)
    - Actionable recommendations (30-40 words)
    - Encouraging closing (10-15 words)

    ## Example Query Processing:
    User: "What is current mandi price for wheat in Bangalore Karnataka?"
    
    Your Response (250 words max):
    1. "I'll help you get the current mandi price for wheat in Bangalore, Karnataka. Let me fetch this information for you."
    2. Call get_commodity_id("wheat") → commodity_id: 1
    3. Call get_state_id("karnataka") → state_id: 29
    4. Call get_district_id(29, "bangalore") → district_id: 572
    5. Call get_mandi_prices(1, 29, 572) → price data
    6. Call analyze_price_trends(price_data) → analysis
    7. Provide concise summary with key points only

    ## Important Notes:
    - ALWAYS follow the exact sequence of tool calls
    - Handle errors gracefully and suggest alternatives
    - Provide prices in ₹ per quintal
    - Be helpful and informative in your responses
    - Respond in the same language as the user's query
    - Prioritize the most critical price information within the 250-word limit
    """,
    tools=[get_commodity_id, get_state_id, get_district_id, get_mandi_prices, analyze_price_trends],
) 
from google.adk.agents import Agent
from datetime import datetime

# Get current time without external dependencies
def get_current_time():
    now = datetime.now()
    return {
        "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "formatted_date": now.strftime("%m-%d-%Y"),
    }

current_time = get_current_time()

root_agent = Agent(
    name="jarvis",
    model="gemini-live-2.5-flash-preview",
    description="A helpful multilingual assistant that responds in the same language as the user.",
    instruction=f"""
    You are Jarvis, a helpful AI assistant.
    
    ## Language Detection Rule
    - Always detect the user's language from their audio/text input
    - Respond in the EXACT SAME LANGUAGE they are using
    - If they speak Hindi → respond in Hindi
    - If they speak English → respond in English
    - If they speak Spanish → respond in Spanish
    - Match their language exactly
    
    ## Your Personality
    - Be helpful and friendly
    - Use the language the user is speaking
    - Keep responses concise and clear
    
    Today's date is {current_time}.
    """,
    tools=[],
) 
import json
import base64
import asyncio
import subprocess
import io
from pathlib import Path
from typing import AsyncIterable

from google.genai.types import Blob, Content, Part
from google.adk.runners import Runner
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig
from google.adk.sessions.in_memory_session_service import InMemorySessionService

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.websockets import WebSocketDisconnect
from pydantic import BaseModel
from fastapi import Body

from app.jarvis.agent import root_agent
from dotenv import load_dotenv
from app.kisaan_info import kisaan_info_agent
from app.kisaan_info.tools import get_current_weather, get_weather_forecast

#
# ADK Streaming Setup
#
load_dotenv()
APP_NAME = "adk-streaming-ws"
session_service = InMemorySessionService()


async def start_agent_session(user_id, is_audio=False):
    """Starts an agent session"""

    # Create a Runner
    runner = Runner(
        app_name=APP_NAME,
        session_service=session_service,
        agent=root_agent,
    )

    # Create a Session
    session = runner.session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
    )

    # Set response modality
    modality = "AUDIO" if is_audio else "TEXT"
    
    if is_audio:
        run_config = RunConfig(
            response_modalities=[modality],
            input_audio_transcription={},
            output_audio_transcription={},
        )
    else:
        run_config = RunConfig(
            response_modalities=[modality]
        )

    # Create a LiveRequestQueue for this session
    live_request_queue = LiveRequestQueue()

    # Start agent session
    live_events = runner.run_live(
        session=session,
        live_request_queue=live_request_queue,
        run_config=run_config,
    )
    return live_events, live_request_queue


async def agent_to_client_messaging(websocket: WebSocket, live_events):
    """Agent to client communication"""
    full_text_response = ""
    async for event in live_events:
        part: Part = event.content and event.content.parts and event.content.parts[0]
        
        # Always stream audio immediately
        if part and part.inline_data and part.inline_data.mime_type.startswith("audio/pcm"):
            audio_data = part.inline_data.data
            if audio_data:
                message = {
                    "mime_type": "audio/pcm",
                    "data": base64.b64encode(audio_data).decode("ascii"),
                }
                await websocket.send_text(json.dumps(message))
                print(f"[AGENT TO CLIENT]: audio/pcm: {len(audio_data)} bytes.")

        # Buffer text, overwriting partial transcripts with the latest, most complete one
        if part and part.text:
            full_text_response = part.text

        # At the end of a turn (either completed or interrupted), send the buffered text and the signal
        if event.turn_complete or event.interrupted:
            # Send the complete text message if we have any
            if full_text_response:
                text_message = {"mime_type": "text/plain", "data": full_text_response}
                await websocket.send_text(json.dumps(text_message))
                print(f"[AGENT TO CLIENT]: Full text/plain: {full_text_response}")
            
            # Send the completion signal
            completion_message = {
                "turn_complete": event.turn_complete,
                "interrupted": event.interrupted,
            }
            await websocket.send_text(json.dumps(completion_message))
            print(f"[AGENT TO CLIENT]: {completion_message}")
            
            # Reset for the next turn
            full_text_response = ""


async def client_to_agent_messaging(
    websocket: WebSocket, live_request_queue: LiveRequestQueue
):
    """Client to agent communication"""
    try:
        while True:
            message_json = await websocket.receive_text()
            message = json.loads(message_json)
            mime_type = message["mime_type"]
            data = message["data"]

            if mime_type == "text/plain":
                content = Content(role="user", parts=[Part.from_text(text=data)])
                live_request_queue.send_content(content=content)
                print(f"[CLIENT TO AGENT]: {data}")

            elif mime_type == "audio/m4a":
                print(f"[CLIENT TO AGENT]: Received audio/m4a, converting with ffmpeg...")
                try:
                    decoded_data = base64.b64decode(data)
                    
                    ffmpeg_command = [
                        'ffmpeg', '-i', 'pipe:0', '-f', 's16le', '-ar', '16000', '-ac', '1', 'pipe:1'
                    ]
                    
                    process = await asyncio.create_subprocess_exec(
                        *ffmpeg_command,
                        stdin=asyncio.subprocess.PIPE,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    pcm_data, stderr_data = await process.communicate(input=decoded_data)
                    
                    if process.returncode != 0:
                        print(f"ffmpeg error (code {process.returncode}): {stderr_data.decode()}")
                        continue

                    print(f"ffmpeg conversion successful, streaming {len(pcm_data)} bytes of PCM data.")

                    chunk_size = 4096
                    for i in range(0, len(pcm_data), chunk_size):
                        chunk = pcm_data[i:i+chunk_size]
                        live_request_queue.send_realtime(Blob(data=chunk, mime_type="audio/pcm"))
                        await asyncio.sleep(0.01)

                    print("[CLIENT TO AGENT]: Finished streaming converted PCM data.")

                except Exception as e:
                    print(f"Error processing audio/m4a with ffmpeg: {e}")
            else:
                raise ValueError(f"Mime type not supported: {mime_type}")

    except WebSocketDisconnect:
        print("Client disconnected normally")
    except Exception as e:
        print(f"Error in client_to_agent_messaging: {e}")
        import traceback
        traceback.print_exc()

#
# FastAPI Web Application
#
app = FastAPI()

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def root():
    """Serves the index.html"""
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, is_audio: str):
    """Client websocket endpoint"""

    # Wait for client connection
    await websocket.accept()
    print(f"Client #{user_id} connected, audio mode: {is_audio}")

    # Start agent session
    user_id_str = str(user_id)
    live_events, live_request_queue = await start_agent_session(
        user_id_str, is_audio == "true"
    )

    # Start tasks
    agent_to_client_task = asyncio.create_task(
        agent_to_client_messaging(websocket, live_events)
    )
    client_to_agent_task = asyncio.create_task(
        client_to_agent_messaging(websocket, live_request_queue)
    )

    # Wait until the websocket is disconnected or an error occurs
    done, pending = await asyncio.wait(
        [agent_to_client_task, client_to_agent_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    for task in pending:
        task.cancel()
    for task in done:
        task.result()

    # Close LiveRequestQueue
    live_request_queue.close()

    # Disconnected
    print(f"Client #{user_id} disconnected")


async def get_kisaan_info_weather_response(lat: float, lon: float, days: int = 1, user_id: str = "weather_user") -> str:
    """Get summarized weather response from kisaan_info_agent for given lat/lon/days."""
    from google.genai.types import Content, Part
    from google.adk.runners import Runner

    runner = Runner(
        app_name=APP_NAME,
        session_service=session_service,
        agent=kisaan_info_agent,
    )
    
    # Get or create session
    session = session_service.get_session(app_name=APP_NAME, user_id=user_id)
    if session is None:
        session = session_service.create_session(app_name=APP_NAME, user_id=user_id, state={})

    # Run the agent with structured input
    response = await kisaan_info_agent.run(
        session=session,
        user_input={"lat": lat, "lon": lon, "days": days}
    )

    return response.text

class KisaanWeatherRequest(BaseModel):
    lat: float
    lon: float
    days: int = 1

@app.post("/kisaan_info/weather")
async def kisaan_info_weather(request: KisaanWeatherRequest = Body(...)):
    """
    Get summarized weather info for a given latitude and longitude using kisaan_info_agent.
    """
    summary = await get_kisaan_info_weather_response(request.lat, request.lon, request.days)
    return {"summary": summary}

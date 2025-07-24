# Expo Voice Chat Assistant

A React Native voice chat application that integrates with the ADK Voice Agent server.

## Features

- **Text Chat**: Send and receive text messages
- **Voice Chat**: Enable voice mode for audio conversations
- **Real-time Streaming**: Live audio streaming to AI agent
- **Audio Responses**: Play audio responses from the AI
- **Connection Management**: Automatic reconnection with retry limits

## Setup

### Prerequisites

1. **Node.js** (v14 or higher)
2. **Expo CLI**: `npm install -g @expo/cli`
3. **Expo Go** app on your mobile device
4. **ADK Voice Agent Server** running on localhost:8000

### Installation

1. Install dependencies:
   ```bash
   cd Expo-Record-Audio
   npm install
   ```

2. Start the development server:
   ```bash
   npx expo start
   ```

3. Scan the QR code with Expo Go app

### Server Setup

Make sure your ADK Voice Agent server is running:

```bash
cd ../adk-voice-agent
source .venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Important**: The server must be started with `--host 0.0.0.0` to allow connections from mobile devices on the same network.

## Usage

1. **Text Mode**: Type messages in the input field and press Send
2. **Voice Mode**: 
   - Tap "Enable Voice" to activate microphone
   - Tap "Record" to start recording
   - Speak your message
   - Tap "Stop" to send the audio to the AI
   - Listen to the AI's audio response

## Troubleshooting

### Connection Issues
- Ensure the ADK Voice Agent server is running on `192.168.29.136:8000`
- Check that your device and computer are on the same WiFi network
- Make sure the server was started with `--host 0.0.0.0` flag
- If you're using a different network, update the IP address in `App.js`

### Audio Issues
- Grant microphone permissions when prompted
- Ensure your device's microphone is working
- Check that the server supports audio streaming

### Duplicate Key Warnings
- These have been fixed in the latest version
- If you still see warnings, restart the Expo development server

## Development

The app uses:
- **React Native** with Expo
- **expo-av** for audio recording and playback
- **WebSocket** for real-time communication
- **Async/await** for audio operations

## File Structure

```
Expo-Record-Audio/
├── App.js              # Main application component
├── app.json            # Expo configuration
├── package.json        # Dependencies
├── assets/             # Static assets
└── README.md           # This file
``` 
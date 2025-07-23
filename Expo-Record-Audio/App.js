import React from 'react';
import { StyleSheet, Text, View, Button, TextInput, ScrollView, Alert } from 'react-native';
import { Audio } from 'expo-av';

export default function App() {
  const [recording, setRecording] = React.useState();
  const [recordings, setRecordings] = React.useState([]);
  
  // Chat functionality
  const [messages, setMessages] = React.useState([]);
  const [inputText, setInputText] = React.useState('');
  const [isConnected, setIsConnected] = React.useState(false);
  const [isTyping, setIsTyping] = React.useState(false);
  const [websocket, setWebsocket] = React.useState(null);
  const [sessionId] = React.useState(Math.random().toString().substring(10));

  // Connect to WebSocket server
  const connectWebSocket = () => {
    try {
      // Replace with your actual server URL
      const wsUrl = `ws://192.168.29.17:8000/ws/${sessionId}?is_audio=false`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        addMessage('system', 'Connected to Jarvis! Ask me anything! 🤖');
      };

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        console.log('Received:', message);

        if (message.turn_complete) {
          setIsTyping(false);
          return;
        }

        if (message.mime_type === 'text/plain') {
          setIsTyping(false);
          addMessage('assistant', message.data);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        addMessage('system', 'Connection lost. Trying to reconnect...');
        // Auto-reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
      };

      ws.onerror = (error) => {
        console.log('WebSocket error:', error);
        setIsConnected(false);
        addMessage('system', 'Connection error. Please check your server.');
      };

      setWebsocket(ws);
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      Alert.alert('Connection Error', 'Failed to connect to chat server. Make sure the server is running.');
    }
  };

  // Add message to chat
  const addMessage = (role, content) => {
    setMessages(prev => [...prev, { id: Date.now(), role, content }]);
  };

  // Send message to server
  const sendMessage = (text) => {
    if (!websocket || websocket.readyState !== WebSocket.OPEN) {
      Alert.alert('Not Connected', 'Please wait for connection to establish.');
      return;
    }

    const message = {
      mime_type: 'text/plain',
      data: text,
      role: 'user'
    };

    websocket.send(JSON.stringify(message));
    addMessage('user', text);
    setInputText('');
    setIsTyping(true);
  };

  // Connect on component mount
  React.useEffect(() => {
    connectWebSocket();
    return () => {
      if (websocket) {
        websocket.close();
      }
    };
  }, []);

  async function startRecording() {
    try {
      const perm = await Audio.requestPermissionsAsync();
      if (perm.status === "granted") {
        await Audio.setAudioModeAsync({
          allowsRecordingIOS: true,
          playsInSilentModeIOS: true,
          staysActiveInBackground: true,
          shouldDuckAndroid: true,
          playThroughEarpieceAndroid: false
        });
        const { recording } = await Audio.Recording.createAsync(Audio.RECORDING_OPTIONS_PRESET_HIGH_QUALITY);
        setRecording(recording);
      }
    } catch (err) {}
  }

  async function stopRecording() {
    setRecording(undefined);

    await recording.stopAndUnloadAsync();
    let allRecordings = [...recordings];
    const { sound, status } = await recording.createNewLoadedSoundAsync();
    
    // Configure audio mode for playback - will automatically use headphones if connected
    await Audio.setAudioModeAsync({
      allowsRecordingIOS: false,
      playsInSilentModeIOS: true,
      staysActiveInBackground: true,
      shouldDuckAndroid: true,
      playThroughEarpieceAndroid: false
    });
    
    allRecordings.push({
      sound: sound,
      duration: getDurationFormatted(status.durationMillis),
      file: recording.getURI()
    });

    setRecordings(allRecordings);
  }

  async function playRecording(sound) {
    // Configure audio mode for playback
    // The system will automatically route to headphones if connected
    // Otherwise it will use the main speaker (not earpiece)
    await Audio.setAudioModeAsync({
      allowsRecordingIOS: false,
      playsInSilentModeIOS: true,
      staysActiveInBackground: true,
      shouldDuckAndroid: true,
      playThroughEarpieceAndroid: false
    });
    
    // Set volume to ensure good audio output
    await sound.setVolumeAsync(1.0);
    await sound.replayAsync();
  }

  function getDurationFormatted(milliseconds) {
    const minutes = milliseconds / 1000 / 60;
    const seconds = Math.round((minutes - Math.floor(minutes)) * 60);
    return seconds < 10 ? `${Math.floor(minutes)}:0${seconds}` : `${Math.floor(minutes)}:${seconds}`
  }

  function getRecordingLines() {
    return recordings.map((recordingLine, index) => {
      return (
        <View key={index} style={styles.row}>
          <Text style={styles.fill}>
            Recording #{index + 1} | {recordingLine.duration}
          </Text>
          <Button onPress={() => playRecording(recordingLine.sound)} title="Play"></Button>
        </View>
      );
    });
  }

  function clearRecordings() {
    setRecordings([])
  }

  return (
    <View style={styles.container}>
      {/* Chat Section */}
      <View style={styles.chatContainer}>
        <Text style={styles.header}>Jarvis Chat Assistant 🤖</Text>
        
        {/* Connection Status */}
        <View style={styles.statusContainer}>
          <View style={[styles.statusDot, { backgroundColor: isConnected ? '#4CAF50' : '#f44336' }]} />
          <Text style={styles.statusText}>
            {isConnected ? 'Connected' : 'Disconnected'}
          </Text>
        </View>

        {/* Messages */}
        <ScrollView style={styles.messagesContainer} showsVerticalScrollIndicator={false}>
          {messages.map((message) => (
            <View key={message.id} style={[
              styles.messageBubble,
              message.role === 'user' ? styles.userMessage : 
              message.role === 'assistant' ? styles.assistantMessage : 
              styles.systemMessage
            ]}>
              <Text style={[
                styles.messageText,
                message.role === 'user' ? styles.userMessageText : 
                message.role === 'assistant' ? styles.assistantMessageText : 
                styles.systemMessageText
              ]}>
                {message.content}
              </Text>
            </View>
          ))}
          {isTyping && (
            <View style={[styles.messageBubble, styles.assistantMessage]}>
              <Text style={[styles.messageText, styles.assistantMessageText]}>
                Jarvis is typing... 🤔
              </Text>
            </View>
          )}
        </ScrollView>

        {/* Input Section */}
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.textInput}
            value={inputText}
            onChangeText={setInputText}
            placeholder="Type your message..."
            multiline
            maxLength={500}
          />
          <Button
            title="Send"
            onPress={() => inputText.trim() && sendMessage(inputText.trim())}
            disabled={!isConnected || !inputText.trim()}
          />
        </View>
      </View>

      {/* Audio Recording Section */}
      <View style={styles.audioContainer}>
        <Text style={styles.sectionHeader}>Audio Recording</Text>
        <Button 
          title={recording ? 'Stop Recording' : 'Start Recording'} 
          onPress={recording ? stopRecording : startRecording} 
        />
        {getRecordingLines()}
        {recordings.length > 0 && (
          <Button title="Clear Recordings" onPress={clearRecordings} />
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 10,
  },
  chatContainer: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 15,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    fontSize: 20,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 10,
    color: '#333',
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10,
  },
  statusDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginRight: 8,
  },
  statusText: {
    fontSize: 14,
    color: '#666',
  },
  messagesContainer: {
    flex: 1,
    marginBottom: 10,
  },
  messageBubble: {
    padding: 12,
    borderRadius: 15,
    marginVertical: 4,
    maxWidth: '80%',
  },
  userMessage: {
    backgroundColor: '#007AFF',
    alignSelf: 'flex-end',
  },
  assistantMessage: {
    backgroundColor: '#E9E9EB',
    alignSelf: 'flex-start',
  },
  systemMessage: {
    backgroundColor: '#FFE4B5',
    alignSelf: 'center',
    maxWidth: '90%',
  },
  messageText: {
    fontSize: 16,
  },
  userMessageText: {
    color: '#fff',
  },
  assistantMessageText: {
    color: '#333',
  },
  systemMessageText: {
    color: '#8B4513',
    textAlign: 'center',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  textInput: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 20,
    padding: 12,
    fontSize: 16,
    maxHeight: 100,
  },
  audioContainer: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  sectionHeader: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 10,
    textAlign: 'center',
    color: '#333',
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 10,
    marginRight: 40
  },
  fill: {
    flex: 1,
    margin: 15
  }
});

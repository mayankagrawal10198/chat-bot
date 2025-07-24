import React from 'react';
import { StyleSheet, Text, View, Button, TextInput, ScrollView, Alert, TouchableOpacity, KeyboardAvoidingView, SafeAreaView, Platform } from 'react-native';
import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';

// Helper function to convert base64 to an ArrayBuffer
function base64ToArrayBuffer(base64) {
  const binaryString = atob(base64);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
}

export default function App() {
  // Chat functionality
  const [messages, setMessages] = React.useState([]);
  const [userInput, setUserInput] = React.useState('');
  const [isConnected, setIsConnected] = React.useState(false);
  const [websocket, setWebsocket] = React.useState(null);
  const [sessionId] = React.useState(Math.random().toString().substring(10));
  const [currentMessageId, setCurrentMessageId] = React.useState(null);

  // Audio functionality
  const [isAudioEnabled, setIsAudioEnabled] = React.useState(false);
  const [isRecording, setIsRecording] = React.useState(false);
  const [recording, setRecording] = React.useState(null);
  
  // Connect to WebSocket server
  const connectWebSocket = () => {
    try {
      if (websocket && websocket.readyState === WebSocket.OPEN) {
        console.log('WebSocket already connected, skipping new connection');
        return;
      }
      if (websocket && websocket.readyState !== WebSocket.CLOSED) {
        console.log('Closing existing WebSocket connection');
        websocket.close();
      }

      const ws_url = `wss://adk-voice-agent-449756804964.us-central1.run.app/ws/${sessionId}?is_audio=${isAudioEnabled}`;
      console.log('Connecting to WebSocket:', ws_url);
      const ws = new WebSocket(ws_url);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
      };
      
      let audioBuffer = []; // Create a buffer for this connection
      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);

        // If it's audio, buffer it
        if (message.mime_type === 'audio/pcm' && message.data) {
          audioBuffer.push(message.data);
        }
        
        // If it's text, update the message content
        if (message.mime_type === 'text/plain') {
            addMessage('model', message.data, currentMessageId);
        }

        // If the turn is complete, play the buffered audio and finalize the message
        if (message.turn_complete) {
          if (audioBuffer.length > 0) {
            const completeAudioData = audioBuffer.join('');
            playAudioResponse(completeAudioData);
            audioBuffer = []; // Clear the buffer for the next turn
          }
          setCurrentMessageId(null); // End the current message turn
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        Alert.alert('Connection Error', 'Could not connect to the server.');
      };

      setWebsocket(ws);
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      Alert.alert('Connection Failed', 'An error occurred while trying to connect.');
    }
  };
  
  // Function to add a new message or update an existing one
  const addMessage = (role, text, messageId = null) => {
    if (messageId) {
      setMessages(prev => prev.map(msg => msg.id === messageId ? { ...msg, text: msg.text + text } : msg));
    } else {
      const newMessage = {
        id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        role,
        text,
      };
      if (role === 'model') {
        setCurrentMessageId(newMessage.id);
      }
      setMessages(prev => [...prev, newMessage]);
    }
  };

  // Send text message to server
  const sendMessage = () => {
    if (!userInput.trim()) return;
    if (!websocket || websocket.readyState !== WebSocket.OPEN) {
      Alert.alert('Not Connected', 'Please wait for connection to establish.');
      return;
    }

    const message = {
      mime_type: 'text/plain',
      data: userInput,
      role: 'user',
    };

    websocket.send(JSON.stringify(message));
    addMessage('user', userInput);
    setUserInput('');
  };

  // Enable voice mode
  const enableAudio = () => {
    if (!isAudioEnabled) {
      setIsAudioEnabled(true);
    }
  };

  // Disable voice mode
  const disableAudio = () => {
    setIsAudioEnabled(false);
  };
  
  // Start and Stop Audio Recording
  const startRecording = async () => {
    try {
      console.log('Requesting permissions..');
      await Audio.requestPermissionsAsync();
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      console.log('Starting recording..');
      const { recording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );
      setRecording(recording);
      setIsRecording(true);
      console.log('Audio streaming started - will send complete file when recording stops');
    } catch (err) {
      console.error('Failed to start recording', err);
    }
  };

  const stopRecording = async () => {
    console.log('Stopping recording..');
    setIsRecording(false);
    await recording.stopAndUnloadAsync();
    const uri = recording.getURI();
    if (uri && websocket && websocket.readyState === WebSocket.OPEN) {
      await sendAudioFile(uri);
    }
    setRecording(null);
  };

  const sendAudioFile = async (uri) => {
    try {
      console.log('=== SENDING AUDIO FILE ===');
      console.log('Audio file URI:', uri);
      
      const response = await fetch(uri);
      const blob = await response.blob();
      
      console.log('Audio blob size:', blob.size, 'bytes');
      console.log('Audio blob type:', blob.type);
      
      const reader = new FileReader();
      reader.onload = () => {
        const base64Data = reader.result.split(',')[1];
        
        console.log('Base64 audio data length:', base64Data.length);
        console.log('WebSocket state:', websocket?.readyState);
        
        if (websocket && websocket.readyState === WebSocket.OPEN) {
          const message = {
            mime_type: 'audio/m4a',
            data: base64Data,
            role: 'user'
          };
          
          console.log('🚀 Sending audio/m4a message to server...');
          websocket.send(JSON.stringify(message));
          console.log('✅ Audio data sent to server successfully');
          
        } else {
          console.error('❌ WebSocket not ready for audio transmission');
          addMessage('system', 'Error: Could not send audio. Please check your connection.');
        }
      };
      
      reader.onerror = (error) => {
        console.error('Error reading audio file:', error);
      };
      
      reader.readAsDataURL(blob);
    } catch (err) {
      console.error('❌ Error sending audio file:', err);
      addMessage('system', 'Error: Could not send audio file.');
    }
  };

  const playAudioResponse = async (audioData) => {
    try {
      console.log('🎵 Playing audio response, data length:', audioData.length);
      
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
        playsInSilentModeIOS: true,
        staysActiveInBackground: true,
        shouldDuckAndroid: true,
        playThroughEarpieceAndroid: false
      });
      
      const arrayBuffer = base64ToArrayBuffer(audioData);
      
      const sampleRate = 16000;
      const numChannels = 1;
      const bitsPerSample = 16;
      const byteRate = sampleRate * numChannels * bitsPerSample / 8;
      const blockAlign = numChannels * bitsPerSample / 8;
      const dataSize = arrayBuffer.byteLength;
      
      const wavHeader = new ArrayBuffer(44);
      const view = new DataView(wavHeader);
      
      view.setUint32(0, 0x52494646, false); // "RIFF"
      view.setUint32(4, 36 + dataSize, true); // ChunkSize
      view.setUint32(8, 0x57415645, false); // "WAVE"
      view.setUint32(12, 0x666d7420, false); // "fmt "
      view.setUint32(16, 16, true); // Subchunk1Size
      view.setUint16(20, 1, true); // AudioFormat
      view.setUint16(22, numChannels, true); // NumChannels
      view.setUint32(24, sampleRate, true); // SampleRate
      view.setUint32(28, byteRate, true); // ByteRate
      view.setUint16(32, blockAlign, true); // BlockAlign
      view.setUint16(34, bitsPerSample, true); // BitsPerSample
      view.setUint32(36, 0x64617461, false); // "data"
      view.setUint32(40, dataSize, true); // Subchunk2Size
      
      const wavBlob = new Blob([wavHeader, arrayBuffer], { type: 'audio/wav' });
      
      const reader = new FileReader();
      reader.onload = async (e) => {
        const audioUri = e.target.result;
        try {
          const { sound } = await Audio.Sound.createAsync(
            { uri: audioUri },
            { shouldPlay: true, volume: 1.0 }
          );
          console.log('✅ Audio playback started successfully');
          sound.setOnPlaybackStatusUpdate((status) => {
            if (status.didJustFinish) {
              console.log('🎵 Audio playback finished');
              sound.unloadAsync();
            }
          });
        } catch (err) {
          console.error('❌ Audio playback failed:', err);
          addMessage('system', '❌ Audio playback failed.');
        }
      };
      reader.readAsDataURL(wavBlob);
      console.log('🎵 Created WAV audio with header');
      
    } catch (err) {
      console.error('Error playing audio:', err);
      addMessage('system', 'Error playing audio response.');
    }
  };

  const testAudio = async () => {
    try {
      console.log('🔊 Testing audio playback...');
      
      const sampleRate = 16000;
      const duration = 1.0;
      const frequency = 440;
      
      const samples = sampleRate * duration;
      const audioData = new Int16Array(samples);
      
      for (let i = 0; i < samples; i++) {
        audioData[i] = Math.sin(2 * Math.PI * frequency * i / sampleRate) * 16384;
      }
      
      const base64Data = btoa(String.fromCharCode(...new Uint8Array(audioData.buffer)));
      
      await playAudioResponse(base64Data);
      
    } catch (err) {
      console.error('❌ Test audio failed:', err);
      addMessage('system', '❌ Audio test failed');
    }
  };

  React.useEffect(() => {
    if (!websocket || websocket.readyState === WebSocket.CLOSED) {
      connectWebSocket();
    }
    return () => {
      if (websocket) {
        websocket.close();
      }
    };
  }, [isAudioEnabled]);

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={90}
      >
        <ScrollView style={styles.messagesContainer}>
          {messages.map((msg) => (
            <View key={msg.id} style={[styles.message, styles[msg.role]]}>
              <Text style={styles.messageText}>{msg.text}</Text>
            </View>
          ))}
        </ScrollView>

        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            placeholder="Type a message..."
            value={userInput}
            onChangeText={setUserInput}
            editable={!isAudioEnabled}
          />
          <TouchableOpacity style={styles.sendButton} onPress={sendMessage} disabled={isAudioEnabled}>
            <Text style={styles.sendButtonText}>Send</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.audioControlsContainer}>
          {!isAudioEnabled ? (
            <View style={styles.audioButtonRow}>
              <TouchableOpacity 
                style={[styles.audioButton, styles.enableAudioButton]} 
                onPress={enableAudio}
                disabled={!isConnected}
              >
                <Text style={styles.audioButtonText}>🎤 Enable Voice</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={[styles.audioButton, styles.testButton]} 
                onPress={testAudio}
              >
                <Text style={styles.audioButtonText}>🔊 Test Audio</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <View style={styles.audioButtonRow}>
              <TouchableOpacity 
                style={[styles.audioButton, styles.disableAudioButton]} 
                onPress={disableAudio}
              >
                <Text style={styles.audioButtonText}>✖️ Disable Voice</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.audioButton,
                  isRecording ? styles.stopButton : styles.recordButton,
                ]}
                onPress={isRecording ? stopRecording : startRecording}
              >
                <Text style={styles.audioButtonText}>
                  {isRecording ? '■ Stop' : '● Record'}
                </Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  container: {
    flex: 1,
    padding: 10,
  },
  messagesContainer: {
    flex: 1,
    marginBottom: 10,
  },
  message: {
    padding: 10,
    borderRadius: 10,
    marginBottom: 10,
    maxWidth: '80%',
  },
  user: {
    alignSelf: 'flex-end',
    backgroundColor: '#DCF8C6',
  },
  model: {
    alignSelf: 'flex-start',
    backgroundColor: '#FFFFFF',
  },
  system: {
    alignSelf: 'center',
    backgroundColor: '#E0E0E0',
    padding: 5,
  },
  messageText: {
    fontSize: 16,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderTopWidth: 1,
    borderColor: '#ccc',
    paddingTop: 10,
  },
  input: {
    flex: 1,
    height: 40,
    borderColor: '#ccc',
    borderWidth: 1,
    borderRadius: 20,
    paddingHorizontal: 15,
  },
  sendButton: {
    marginLeft: 10,
    backgroundColor: '#2196F3',
    padding: 10,
    borderRadius: 20,
  },
  sendButtonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  audioControlsContainer: {
    marginTop: 10,
    alignItems: 'center',
  },
  audioButtonRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
  },
  audioButton: {
    padding: 15,
    borderRadius: 30,
    minWidth: 120,
    alignItems: 'center',
  },
  audioButtonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  enableAudioButton: {
    backgroundColor: '#4CAF50',
  },
  disableAudioButton: {
    backgroundColor: '#f44336',
  },
  recordButton: {
    backgroundColor: '#2196F3',
  },
  stopButton: {
    backgroundColor: '#f44336',
  },
  testButton: {
    backgroundColor: '#FF9800',
  },
});


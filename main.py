"""
Real-time Speech-to-Speech Chat Application.
"""

import streamlit as st
import json
import os
import websocket
import threading
import pyaudio
import base64
import time
import numpy as np
from dotenv import load_dotenv
import queue
from datetime import datetime
from pathlib import Path
from src.vocabulary_analyzer import VocabularyAnalyzer

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Voice Chat - 日本語会話 with Vocabulary",
    page_icon="📚",
    layout="wide"
)

# Load personas
@st.cache_data
def load_personas():
    personas_path = Path("config/personas.json")
    if personas_path.exists():
        with open(personas_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'connected' not in st.session_state:
    st.session_state.connected = False
if 'conversation_mode' not in st.session_state:
    st.session_state.conversation_mode = False
if 'last_update' not in st.session_state:
    st.session_state.last_update = time.time()
if 'app' not in st.session_state:
    st.session_state.app = None
if 'api_key' not in st.session_state:
    st.session_state.api_key = os.getenv("OPENAI_API_KEY", "")
if 'clear_counter' not in st.session_state:
    st.session_state.clear_counter = 0
if 'message_version' not in st.session_state:
    st.session_state.message_version = 0
if 'selected_persona' not in st.session_state:
    personas_data = load_personas()
    if personas_data:
        st.session_state.selected_persona = personas_data.get('default_persona', 'yuki_sensei')
    else:
        st.session_state.selected_persona = None
if 'personas' not in st.session_state:
    st.session_state.personas = load_personas()
if 'vocabulary_analyzer' not in st.session_state:
    st.session_state.vocabulary_analyzer = None
if 'show_vocabulary' not in st.session_state:
    st.session_state.show_vocabulary = True
if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = False
if 'vocab_filter_level' not in st.session_state:
    st.session_state.vocab_filter_level = 'All'

class VoiceChatApp:
    def __init__(self, api_key=None, persona_config=None):
        # Use provided key or fall back to environment variable
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            return
            
        # Store persona configuration
        self.persona_config = persona_config
            
        # WebSocket
        self.ws = None
        self.ws_thread = None
        self.is_connected = False
        self.is_running = True  # Flag to control threads
        
        # Audio settings
        self.sample_rate = 24000
        self.chunk_size = 1024
        self.channels = 1
        self.format = pyaudio.paInt16
        
        # Continuous listening
        self.continuous_stream = None
        self.continuous_thread = None
        self.is_listening = False
        self.audio_buffer = []
        self.silence_threshold = 500
        self.silence_duration = 1.0
        self.last_sound_time = time.time()
        self.has_sound = False
        
        # Audio playback
        self.audio_queue = queue.Queue()
        self.playback_thread = None
        self.playback_stream = None
        self.response_audio_buffer = []
        self.is_receiving_audio = False
        self.min_buffer_size = 4096
        
        # Message queue
        self.message_queue = queue.Queue()
        
        # PyAudio instance
        self.pyaudio = None
    
    def connect_websocket(self):
        """Connect to OpenAI Realtime API"""
        # Check if already connected
        if self.is_connected:
            if st.session_state.debug_mode:
                print("[CONNECT] Already connected, skipping")
            return True
            
        # Clean up any existing connection first
        if self.ws:
            if st.session_state.debug_mode:
                print("[CONNECT] Cleaning up existing WebSocket")
            try:
                self.ws.close()
            except:
                pass
            self.ws = None
            time.sleep(0.5)
        
        if st.session_state.debug_mode:
            print("[CONNECT] Starting connection to OpenAI Realtime API")
        ws_url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview"
        headers = [
            f"Authorization: Bearer {self.api_key}",
            "OpenAI-Beta: realtime=v1"
        ]
        
        try:
            self.ws = websocket.WebSocketApp(
                ws_url,
                header=headers,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )
            
            # Run WebSocket in thread only if not already running
            if not self.ws_thread or not self.ws_thread.is_alive():
                self.ws_thread = threading.Thread(target=self.ws.run_forever)
                self.ws_thread.daemon = True
                self.ws_thread.start()
            else:
                if st.session_state.debug_mode:
                    print("[CONNECT] WebSocket thread already running")
            
            # Start audio playback thread only if not already running
            if not self.playback_thread or not self.playback_thread.is_alive():
                self.playback_thread = threading.Thread(target=self._audio_playback_loop)
                self.playback_thread.daemon = True
                self.playback_thread.start()
            else:
                if st.session_state.debug_mode:
                    print("[AUDIO] Playback thread already running")
            
            # Wait for connection
            for i in range(10):
                if self.is_connected:
                    print("[CONNECT] Successfully connected!")
                    # Initialize PyAudio after connection
                    if not self.pyaudio:
                        self.pyaudio = pyaudio.PyAudio()
                    return True
                time.sleep(0.5)
            
            print("[CONNECT] Connection timeout")
            return False
            
        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            return False
    
    def on_open(self, ws):
        """WebSocket opened"""
        if st.session_state.debug_mode:
            print("[WEBSOCKET] Connection opened")
        self.is_connected = True
        
        # Default instructions
        instructions = "You are a Japanese conversation partner. Always respond in Japanese."
        voice = "alloy"
        
        # Use persona if available
        if self.persona_config:
            instructions = self.persona_config.get('prompt', instructions)
            voice = self.persona_config.get('voice', voice)
            print(f"[PERSONA] Using {self.persona_config.get('name', 'default')} with voice {voice}")
        
        # Configure for natural conversation with server VAD
        config = {
            "type": "session.update",
            "session": {
                "model": "gpt-4o-realtime-preview",
                "voice": voice,
                "instructions": instructions,
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                },
                "temperature": 0.7,
                "max_response_output_tokens": 4096
            }
        }
        ws.send(json.dumps(config))
        if st.session_state.debug_mode:
            print("[CONFIG] Session configured")
    
    def on_message(self, ws, message):
        """Handle WebSocket messages"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            # Log important events
            if msg_type not in ["response.audio.delta", "response.audio_transcript.delta"]:
                if st.session_state.debug_mode:
                    print(f"[MESSAGE] {msg_type}")
            
            if msg_type == "session.created":
                if st.session_state.debug_mode:
                    print("[SESSION] Created successfully")
                
            elif msg_type == "input_audio_buffer.speech_started":
                if st.session_state.debug_mode:
                    print("[SPEECH] User started speaking")
                
            elif msg_type == "input_audio_buffer.speech_stopped":
                if st.session_state.debug_mode:
                    print("[SPEECH] User stopped speaking")
                
            elif msg_type == "conversation.item.input_audio_transcription.completed":
                transcript = data.get("transcript", "")
                if transcript:
                    print(f"[USER] {transcript}")
                    self.message_queue.put({
                        "role": "user",
                        "content": transcript
                    })
                    
            elif msg_type == "response.audio.delta":
                audio_base64 = data.get("delta", "")
                if audio_base64:
                    audio_bytes = base64.b64decode(audio_base64)
                    self.response_audio_buffer.append(audio_bytes)
                    self.is_receiving_audio = True
                    
                    # Buffer before playback
                    buffer_size = sum(len(chunk) for chunk in self.response_audio_buffer)
                    if buffer_size >= self.min_buffer_size:
                        if st.session_state.debug_mode:
                            print(f"[AUDIO] Queueing {len(self.response_audio_buffer)} chunks, total size: {buffer_size}")
                        for chunk in self.response_audio_buffer:
                            self.audio_queue.put(chunk)
                        self.response_audio_buffer = []
                    
            elif msg_type == "response.audio_transcript.done":
                transcript = data.get("transcript", "")
                if transcript:
                    print(f"[ASSISTANT] {transcript}")
                    self.message_queue.put({
                        "role": "assistant",
                        "content": transcript
                    })
                
                # Flush remaining audio
                if self.response_audio_buffer:
                    buffer_size = sum(len(chunk) for chunk in self.response_audio_buffer)
                    if st.session_state.debug_mode:
                        print(f"[AUDIO] Flushing {len(self.response_audio_buffer)} remaining chunks, size: {buffer_size}")
                    for chunk in self.response_audio_buffer:
                        self.audio_queue.put(chunk)
                    self.response_audio_buffer = []
                self.is_receiving_audio = False
                    
            elif msg_type == "response.done":
                if st.session_state.debug_mode:
                    print("[RESPONSE] Complete")
                if self.response_audio_buffer:
                    for chunk in self.response_audio_buffer:
                        self.audio_queue.put(chunk)
                    self.response_audio_buffer = []
                self.is_receiving_audio = False
                
            elif msg_type == "error":
                error = data.get("error", {})
                print(f"[ERROR] {error.get('message', 'Unknown')}")
                
        except Exception as e:
            print(f"[ERROR] Message processing: {e}")
    
    def on_error(self, ws, error):
        print(f"[ERROR] WebSocket: {error}")
        self.is_connected = False
    
    def on_close(self, ws, close_status_code, close_msg):
        if st.session_state.debug_mode:
            print(f"[CLOSE] {close_status_code} - {close_msg}")
        self.is_connected = False
    
    def start_continuous_listening(self):
        """Start continuous audio streaming"""
        # Check if already listening
        if self.is_listening:
            if st.session_state.debug_mode:
                print("[LISTEN] Already listening, skipping start")
            return
            
        if not self.is_connected:
            print("[LISTEN] Not connected, cannot start listening")
            return
            
        # Clean up any existing stream first
        if self.continuous_stream:
            if st.session_state.debug_mode:
                print("[LISTEN] Cleaning up existing stream")
            try:
                self.continuous_stream.stop_stream()
                self.continuous_stream.close()
            except:
                pass
            self.continuous_stream = None
            
        if st.session_state.debug_mode:
            print("[LISTEN] Starting continuous listening mode")
        
        try:
            if not self.pyaudio:
                self.pyaudio = pyaudio.PyAudio()
            
            # Open stream for continuous capture
            self.continuous_stream = self.pyaudio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            self.is_listening = True
            
            # Start listening thread only if not already running
            if not self.continuous_thread or not self.continuous_thread.is_alive():
                self.continuous_thread = threading.Thread(target=self._continuous_listening_loop)
                self.continuous_thread.daemon = True
                self.continuous_thread.start()
            
            if st.session_state.debug_mode:
                print("[LISTEN] Continuous listening started")
            
        except Exception as e:
            print(f"[ERROR] Failed to start continuous listening: {e}")
            self.is_listening = False
    
    def _continuous_listening_loop(self):
        """Continuous listening with real-time streaming to OpenAI"""
        if st.session_state.debug_mode:
            print("[LISTEN] Listening loop started")
        
        while self.is_listening and self.continuous_stream:
            try:
                if self.continuous_stream.is_active():
                    # Read audio chunk
                    data = self.continuous_stream.read(self.chunk_size, exception_on_overflow=False)
                    
                    # Send to OpenAI immediately for server-side VAD
                    if self.is_connected and self.ws:
                        audio_base64 = base64.b64encode(data).decode('utf-8')
                        message = {
                            "type": "input_audio_buffer.append",
                            "audio": audio_base64
                        }
                        self.ws.send(json.dumps(message))
                    
            except Exception as e:
                if self.is_listening:
                    print(f"[ERROR] Continuous listening: {e}")
                time.sleep(0.01)
        
        if st.session_state.debug_mode:
            print("[LISTEN] Listening loop stopped")
    
    def stop_continuous_listening(self):
        """Stop continuous listening"""
        if st.session_state.debug_mode:
            print("[LISTEN] Stopping continuous listening")
        self.is_listening = False
        
        if self.continuous_thread:
            self.continuous_thread.join(timeout=1)
        
        if self.continuous_stream:
            try:
                self.continuous_stream.stop_stream()
                self.continuous_stream.close()
            except:
                pass
            self.continuous_stream = None
    
    def _audio_playback_loop(self):
        """Play audio from queue with persistent stream"""
        if st.session_state.debug_mode:
            print("[AUDIO] Playback thread started")
        
        if not self.pyaudio:
            self.pyaudio = pyaudio.PyAudio()
        
        # Clean up any existing stream first
        if self.playback_stream:
            try:
                self.playback_stream.stop_stream()
                self.playback_stream.close()
            except:
                pass
            self.playback_stream = None
        
        while self.is_running:  # Keep running while app is active
            try:
                    
                audio_data = self.audio_queue.get(timeout=0.1)
                
                # Check for sentinel value to stop thread
                if audio_data is None:
                    if st.session_state.debug_mode:
                        print("[AUDIO] Received stop signal")
                    break
                
                if not self.playback_stream or not self.playback_stream.is_active():
                    if st.session_state.debug_mode:
                        print("[AUDIO] Opening playback stream")
                    try:
                        self.playback_stream = self.pyaudio.open(
                            format=self.format,
                            channels=self.channels,
                            rate=self.sample_rate,
                            output=True,
                            frames_per_buffer=2048
                        )
                    except Exception as e:
                        print(f"[ERROR] Failed to open playback stream: {e}")
                        continue
                
                # Play audio
                try:
                    self.playback_stream.write(audio_data)
                    if st.session_state.debug_mode:
                        print(f"[AUDIO] Played {len(audio_data)} bytes")
                except Exception as e:
                    print(f"[ERROR] Failed to play audio: {e}")
                
            except queue.Empty:
                if self.playback_stream and not self.is_receiving_audio:
                    if self.audio_queue.empty():
                        time.sleep(0.5)
                        if self.audio_queue.empty() and self.playback_stream:
                            if st.session_state.debug_mode:
                                print("[AUDIO] Closing playback stream")
                            self.playback_stream.stop_stream()
                            self.playback_stream.close()
                            self.playback_stream = None
                continue
                
            except Exception as e:
                print(f"[ERROR] Playback: {e}")
                if self.playback_stream:
                    try:
                        self.playback_stream.close()
                    except:
                        pass
                    self.playback_stream = None
        
        # Cleanup when thread exits
        if st.session_state.debug_mode:
            print("[AUDIO] Playback thread stopping")
        if self.playback_stream:
            try:
                self.playback_stream.stop_stream()
                self.playback_stream.close()
            except:
                pass
            self.playback_stream = None
        if st.session_state.debug_mode:
            print("[AUDIO] Playback thread stopped")
    
    def send_text_message(self, text):
        """Send text message"""
        if self.is_connected and self.ws:
            if st.session_state.debug_mode:
                print(f"[TEXT] Sending: {text}")
            
            self.message_queue.put({
                "role": "user",
                "content": text
            })
            
            message = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": text
                        }
                    ]
                }
            }
            self.ws.send(json.dumps(message))
            
            time.sleep(0.1)
            self.ws.send(json.dumps({"type": "response.create"}))
    
    def get_pending_messages(self):
        """Get all pending messages from queue"""
        messages = []
        while not self.message_queue.empty():
            try:
                messages.append(self.message_queue.get_nowait())
            except queue.Empty:
                break
        return messages
    
    def cleanup(self):
        """Cleanup resources"""
        if st.session_state.debug_mode:
            print("[CLEANUP] Starting cleanup")
        
        # Flag to stop all threads
        self.is_running = False
        self.is_connected = False
        self.is_listening = False
        self.is_receiving_audio = False
        
        # Stop listening first
        self.stop_continuous_listening()
        
        # Stop playback thread by setting a flag
        if self.playback_thread and self.playback_thread.is_alive():
            if st.session_state.debug_mode:
                print("[CLEANUP] Stopping playback thread")
            # Clear audio queue and wait for thread to finish
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except:
                    break
            # Add a sentinel value to stop the thread
            self.audio_queue.put(None)
            self.playback_thread.join(timeout=2)
        
        # Stop playback stream
        if self.playback_stream:
            try:
                if st.session_state.debug_mode:
                    print("[CLEANUP] Closing playback stream")
                self.playback_stream.stop_stream()
                self.playback_stream.close()
            except:
                pass
            self.playback_stream = None
        
        # Clear queues
        while not self.message_queue.empty():
            try:
                self.message_queue.get_nowait()
            except:
                break
        
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except:
                break
        
        # Close WebSocket
        if self.ws:
            try:
                if st.session_state.debug_mode:
                    print("[CLEANUP] Closing WebSocket")
                self.ws.close()
            except:
                pass
            self.ws = None
            
        # Wait for WebSocket thread to finish
        if self.ws_thread and self.ws_thread.is_alive():
            self.ws_thread.join(timeout=2)
        
        # Terminate PyAudio last
        if self.pyaudio:
            try:
                if st.session_state.debug_mode:
                    print("[CLEANUP] Terminating PyAudio")
                self.pyaudio.terminate()
            except:
                pass
            self.pyaudio = None
        
        # Reset all threads
        self.playback_thread = None
        self.continuous_thread = None
        self.ws_thread = None
        
        if st.session_state.debug_mode:
            print("[CLEANUP] Cleanup complete")

def display_vocabulary_panel():
    """Display vocabulary panel as single table with level filter"""
    if st.session_state.vocabulary_analyzer:
        analyzer = st.session_state.vocabulary_analyzer
        vocabulary = analyzer.get_session_vocabulary()
        
        if vocabulary:
            st.header("📚 Today's Vocabulary")
            
            # Level filter options
            col1, col2 = st.columns([1, 1])
            with col1:
                filter_options = {
                    'All': 'All Levels',
                    'N5': 'N5 only',
                    'N4+': 'N4 and above',
                    'N3+': 'N3 and above',
                    'N2+': 'N2 and above',
                    'N1': 'N1 only'
                }
                selected_filter = st.selectbox(
                    "Filter by Level:",
                    options=list(filter_options.keys()),
                    format_func=lambda x: filter_options[x],
                    index=list(filter_options.keys()).index(st.session_state.vocab_filter_level),
                    key="vocab_level_filter"
                )
                st.session_state.vocab_filter_level = selected_filter
            
            # Apply filter
            level_order = {'N5': 1, 'N4': 2, 'N3': 3, 'N2': 4, 'N1': 5}
            filtered_vocabulary = []
            
            if selected_filter == 'All':
                filtered_vocabulary = vocabulary
            elif selected_filter == 'N5':
                filtered_vocabulary = [w for w in vocabulary if w.get('level') == 'N5']
            elif selected_filter == 'N1':
                filtered_vocabulary = [w for w in vocabulary if w.get('level') == 'N1']
            elif selected_filter.endswith('+'):
                min_level = selected_filter[:-1]  # Remove '+'
                min_level_num = level_order.get(min_level, 0)
                filtered_vocabulary = [
                    w for w in vocabulary 
                    if level_order.get(w.get('level', 'N3'), 0) >= min_level_num
                ]
            
            # Show count
            with col2:
                if len(filtered_vocabulary) == 0:
                    st.warning(f"No words at this level (Total: {len(vocabulary)})")
                else:
                    st.info(f"Showing {len(filtered_vocabulary)} / {len(vocabulary)} words")
            
            # Create table data for filtered words
            table_data = []
            for word in filtered_vocabulary:
                table_data.append({
                    '日本語': word['word'],
                    'よみがな': word.get('reading', ''),
                    '한국어': word.get('meaning_kr', ''),
                    '품사': word.get('pos', ''),
                    'Level': word.get('level', '')
                })
            
            # Display as dataframe
            if table_data:
                import pandas as pd
                df = pd.DataFrame(table_data)
                
                # Sort by level (higher level first)
                df['Level_Num'] = df['Level'].map(level_order)
                df = df.sort_values('Level_Num', ascending=False)
                df = df.drop('Level_Num', axis=1)
                
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    height=min(400, len(table_data) * 35 + 50)
                )
                
                # Show examples and notes in expander if available (filtered)
                filtered_words_with_details = [w for w in filtered_vocabulary if w.get('example') or w.get('notes')]
                if filtered_words_with_details:
                    with st.expander(f"💡 Examples & Notes ({len(filtered_words_with_details)} words)"):
                        for word in filtered_words_with_details:
                            st.write(f"**{word['word']}** ({word.get('reading', '')})")
                            if word.get('example'):
                                st.write(f"• 예문: {word['example']}")
                            if word.get('notes'):
                                st.write(f"• 메모: {word['notes']}")
                            st.divider()
            
            # Export and clear buttons
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Export", use_container_width=True, key="export_vocab"):
                    export_text = analyzer.export_vocabulary()
                    st.download_button(
                        label="Download",
                        data=export_text,
                        file_name=f"vocabulary_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                        mime="text/plain",
                        key="download_vocab"
                    )
            with col2:
                if st.button("🗑️ Clear", use_container_width=True, key="clear_vocab"):
                    analyzer.clear_session()
                    st.rerun()
        else:
            st.info("No vocabulary yet. Start a conversation to see words here!")

def main():
    # Display title with current persona (only once at the top)
    if st.session_state.personas and st.session_state.selected_persona:
        personas = st.session_state.personas['personas']
        current_persona = personas.get(st.session_state.selected_persona, {})
        if current_persona:
            st.title(f"🎙️ AI Voice Chat - {current_persona['emoji']} {current_persona['name']}")
        else:
            st.title("🎙️ AI Voice Chat")
    else:
        st.title("🎙️ AI Voice Chat")
    
    # Create two columns for layout
    col1, col2 = st.columns([2, 1])
    
    # Initialize vocabulary analyzer
    if st.session_state.vocabulary_analyzer is None and st.session_state.api_key:
        st.session_state.vocabulary_analyzer = VocabularyAnalyzer(st.session_state.api_key)
    
    # Track message version for forced refresh
    current_version = st.session_state.message_version
    
    # Initialize app with API key and persona
    if st.session_state.app is None and st.session_state.api_key:
        persona_config = None
        if st.session_state.personas and st.session_state.selected_persona:
            personas = st.session_state.personas.get('personas', {})
            persona_config = personas.get(st.session_state.selected_persona)
        st.session_state.app = VoiceChatApp(st.session_state.api_key, persona_config)
    
    app = st.session_state.app
    
    # Process pending messages and analyze vocabulary
    if app:
        new_messages = app.get_pending_messages()
        if new_messages:
            if st.session_state.debug_mode:
                print(f"[MAIN] Processing {len(new_messages)} new messages")
            for msg in new_messages:
                st.session_state.messages.append(msg)
                if st.session_state.debug_mode:
                    print(f"[MAIN] Added message: {msg['role']}: {msg['content'][:50]}...")
                
                # Analyze vocabulary for assistant messages
                if st.session_state.vocabulary_analyzer and msg['role'] == 'assistant':
                    st.session_state.vocabulary_analyzer.analyze_conversation(
                        msg['content'], 
                        msg['role']
                    )
            
            st.session_state.last_update = time.time()
    
    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ Controls")
        
        # API Key input
        api_key_input = st.text_input(
            "OpenAI API Key",
            value=st.session_state.api_key,
            type="password",
            help="Enter your OpenAI API key or set it in .env file"
        )
        
        if api_key_input != st.session_state.api_key:
            st.session_state.api_key = api_key_input
            st.session_state.app = None
            st.session_state.vocabulary_analyzer = None
            st.rerun()
        
        if not st.session_state.api_key:
            st.error("Please enter your OpenAI API key")
            st.stop()
        
        st.divider()
        
        # Connection
        if not st.session_state.connected:
            if st.button("🔌 Connect", type="primary", use_container_width=True):
                with st.spinner("Connecting..."):
                    # Clean up any existing app first
                    if st.session_state.app:
                        if st.session_state.debug_mode:
                            print("[CONNECT] Cleaning up existing app instance")
                        try:
                            st.session_state.app.cleanup()
                        except Exception as e:
                            print(f"[ERROR] Cleanup failed: {e}")
                        finally:
                            st.session_state.app = None
                            time.sleep(0.5)  # Give time for cleanup
                    
                    # Create new app instance with persona config
                    persona_config = None
                    if st.session_state.personas and st.session_state.selected_persona:
                        personas = st.session_state.personas.get('personas', {})
                        persona_config = personas.get(st.session_state.selected_persona)
                    
                    if st.session_state.debug_mode:
                        print("[CONNECT] Creating new app instance")
                    st.session_state.app = VoiceChatApp(st.session_state.api_key, persona_config)
                    app = st.session_state.app
                    
                    if app and app.connect_websocket():
                        st.session_state.connected = True
                        st.success("✅ Connected!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Connection failed")
                        st.session_state.app = None
        else:
            # Conversation toggle with status integrated
            if not st.session_state.conversation_mode:
                if st.button("🎙️ Start Conversation", type="primary", use_container_width=True):
                    app.start_continuous_listening()
                    st.session_state.conversation_mode = True
                    st.rerun()
            else:
                if st.button("⏸️ Pause Conversation", type="primary", use_container_width=True):
                    app.stop_continuous_listening()
                    st.session_state.conversation_mode = False
                    st.rerun()
            
            # Disconnect
            if st.button("🔌 Disconnect", use_container_width=True):
                if st.session_state.debug_mode:
                    print("[DISCONNECT] User clicked disconnect")
                # Stop conversation mode first
                if st.session_state.conversation_mode:
                    st.session_state.conversation_mode = False
                    if app:
                        app.stop_continuous_listening()
                
                # Cleanup app thoroughly
                if app:
                    if st.session_state.debug_mode:
                        print("[DISCONNECT] Cleaning up app")
                    app.cleanup()
                    time.sleep(1)  # Give time for cleanup
                
                # Reset state
                st.session_state.connected = False
                st.session_state.app = None
                st.rerun()
        
        st.divider()
        
        # Persona selection
        if st.session_state.personas:
            st.header("🎭 Character")
            personas = st.session_state.personas['personas']
            
            # Create persona options with emoji and name
            persona_options = {}
            for pid, persona in personas.items():
                label = f"{persona['emoji']} {persona['name']}"
                persona_options[label] = pid
            
            # Persona selector
            selected_label = st.selectbox(
                "Select conversation partner:",
                options=list(persona_options.keys()),
                index=list(persona_options.values()).index(st.session_state.selected_persona) if st.session_state.selected_persona in persona_options.values() else 0,
                help="Each character has a unique personality and speaking style",
                label_visibility="collapsed"
            )
            
            new_persona_id = persona_options[selected_label]
            
            # If persona changed and connected, need to reconnect
            if new_persona_id != st.session_state.selected_persona:
                st.session_state.selected_persona = new_persona_id
                if st.session_state.connected:
                    st.warning("⚠️ Reconnect to apply change")
        
        st.divider()
        
        # Clear chat
        clear_key = f"clear_button_{st.session_state.clear_counter}"
        if st.button("🗑️ Clear Chat", use_container_width=True, key=clear_key):
            if st.session_state.debug_mode:
                print("[CLEAR] Starting chat clear")
            
            # Stop conversation first if active
            if st.session_state.conversation_mode and app:
                app.stop_continuous_listening()
                st.session_state.conversation_mode = False
            
            # Clear messages
            st.session_state.messages.clear()
            
            # Clear vocabulary
            if st.session_state.vocabulary_analyzer:
                st.session_state.vocabulary_analyzer.clear_session()
            
            # Clear any pending messages in the app
            if app:
                app.message_queue = queue.Queue()
                app.audio_queue = queue.Queue()
                app.response_audio_buffer = []
                app.is_receiving_audio = False
                
                # Stop any audio playback
                if app.playback_stream:
                    try:
                        app.playback_stream.stop_stream()
                        app.playback_stream.close()
                    except:
                        pass
                    app.playback_stream = None
            
            # Increment counters to force refresh
            st.session_state.clear_counter += 1
            st.session_state.message_version += 1
            
            if st.session_state.debug_mode:
                print(f"[CLEAR] Messages cleared. Count: {len(st.session_state.messages)}")
            
            # Force immediate rerun
            st.rerun()
        
        
        # Vocabulary panel toggle
        st.divider()
        st.checkbox(
            "📚 Show Vocabulary Panel",
            value=st.session_state.show_vocabulary,
            key="vocab_toggle",
            on_change=lambda: setattr(st.session_state, 'show_vocabulary', st.session_state.vocab_toggle)
        )
        
        # Debug mode toggle (smaller, less prominent)
        with st.expander("Developer Options"):
            st.checkbox(
                "🐛 Debug Mode",
                value=st.session_state.debug_mode,
                key="debug_toggle",
                on_change=lambda: setattr(st.session_state, 'debug_mode', st.session_state.debug_toggle),
                help="Enable verbose logging for debugging"
            )
    
    # Main chat area
    with col1:
        # Chat messages area
        message_container = st.container(height=600)
        with message_container:
            if len(st.session_state.messages) > 0:
                for i, message in enumerate(st.session_state.messages):
                    with st.chat_message(message["role"]):
                        st.write(message["content"])
            else:
                # Empty state
                if not st.session_state.connected:
                    st.info("Enter your API key and click Connect to start")
                elif not st.session_state.conversation_mode:
                    st.info("Click 'Start Conversation' to begin")
                else:
                    st.info("Start speaking! I'm listening...")
        
        # Text input
        if st.session_state.connected:
            if prompt := st.chat_input("Type a message..."):
                if app:
                    app.send_text_message(prompt)
                    time.sleep(1)
                    st.rerun()
    
    # Vocabulary panel
    with col2:
        if st.session_state.show_vocabulary:
            with st.container():
                display_vocabulary_panel()
    
    # Auto-refresh for new messages
    if st.session_state.connected and app:
        time.sleep(1)
        st.rerun()

if __name__ == "__main__":
    main()
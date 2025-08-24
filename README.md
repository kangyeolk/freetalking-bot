# 🗾 AI Voice Chat - Japanese Conversation Learning with Vocabulary Tracking

Practice speaking Japanese with AI native speakers and build your vocabulary through real conversations.  

**Core Purpose**: Have natural conversations with Japanese-speaking AI characters while the app automatically extracts and saves vocabulary words that appear during your chat. Review these words later as flashcards to reinforce your learning.

Powered by OpenAI's Realtime API for authentic, low-latency voice interactions.

## ✨ Key Features

### 🎤 Real-time Voice Conversation
- Low-latency voice chat powered by OpenAI Realtime API
- Natural turn detection with Server VAD
- High-quality 24kHz audio
- Continuous conversation mode

### 📚 Japanese Learning Features
- **Automatic Vocabulary Extraction**: Real-time word analysis during conversations
- **JLPT Level Classification**: Automatic N5-N1 difficulty classification
- **Korean Translations**: Korean meanings for all vocabulary
- **Filtering Options**: View words by JLPT level
- **Export Learning Materials**: Download vocabulary lists

### 🎭 Diverse AI Characters
- **Yuki Sensei** (雪先生): Professional Japanese teacher
- **Tanaka San** (田中さん): Business professional
- **Sakura Chan** (さくらちゃん): Friendly student
- **Kenji Kun** (健二くん): Casual friend
- **Yamada Sensei** (山田先生): Academic professor
- **AI Assistant**: Helpful AI companion

## 🚀 Quick Start

### Requirements

- **Python 3.8+**
- **OpenAI API Key** with Realtime API access
- **Microphone** for voice input

### Installation

#### Option 1: Quick Setup with uv (Recommended) ⚡️

```bash
# Clone repository
git clone [repository-url]
cd conversation-bot

# Install uv if you don't have it (ultra-fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install packages
uv venv --python 3.11
source .venv/bin/activate
uv pip install -r requirements.txt
```

#### Option 2: Standard Setup with pip

```bash
# Clone repository
git clone [repository-url]
cd conversation-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

#### Option 3: Using Makefile (Simplest)

```bash
# Setup and install
make setup       # Creates virtual environment
source .venv/bin/activate
make install     # Installs packages
```

### Configure API Key

```bash
# Create .env file
cp .env.example .env

# Edit .env and add your OpenAI API key
OPENAI_API_KEY=your-api-key-here
```

### Run the App

```bash
# Basic run
streamlit run main.py
```

Or use helper scripts:
```bash
./run_dev.sh   # Development mode (auto-reload, debug logs)
./run_prod.sh  # Production mode
```

Open browser at http://localhost:8501

## 💬 How to Use

1. **Connect**: Enter your OpenAI API key and click "Connect"
2. **Choose Your Partner**: Select an AI character that matches your learning style
3. **Start Speaking**: Click "Start Conversation" and speak naturally in Japanese
4. **Build Vocabulary**: As you converse, new words automatically appear in the vocabulary panel with:
   - Furigana (reading hints)
   - Korean translations
   - JLPT level indicators
5. **Filter by Level**: Use the dropdown to focus on words at your level
6. **Review Later**: Export your vocabulary list as a study sheet for flashcard review

## 🎯 Vocabulary Filter Options

- **All Levels**: Show all vocabulary
- **N5 only**: Beginner words only
- **N4+**: N4 and above (intermediate-advanced)
- **N3+**: N3 and above (upper-intermediate-advanced)
- **N2+**: N2 and above (advanced-expert)
- **N1 only**: Expert level only

## 🛠 Tech Stack

- **Frontend**: Streamlit (Wide Layout)
- **Voice API**: OpenAI Realtime API (GPT-4)
- **Audio**: PyAudio, WebSocket
- **Vocabulary Analysis**: GPT-4 context-aware analysis
- **TTS Voices**: Alloy, Echo, Shimmer

## 📝 Project Structure

```
conversation-bot/
├── main.py                     # Main application
├── src/
│   └── vocabulary_analyzer.py  # Vocabulary analysis module
├── config/
│   └── personas.json           # AI character configurations
├── run_dev.sh                  # Development script
├── run_prod.sh                 # Production script
└── requirements.txt            # Dependencies
```

## ⚠️ Important Notes

- Requires stable internet connection
- Microphone permissions required
- OpenAI API usage incurs costs
- Realtime API beta access required
- Chrome/Edge browser recommended

## 🐛 Troubleshooting

<details>
<summary><strong>No Audio Output</strong></summary>

- Verify PyAudio installation: `pip install pyaudio`
- Check speaker settings and volume
- Review console logs for audio errors
- Try refreshing the browser page
- On macOS: `brew install portaudio` then reinstall pyaudio
</details>

<details>
<summary><strong>Connection Issues</strong></summary>

- Verify your OpenAI API key is correct
- Check you have Realtime API beta access
- Confirm stable internet connection
- Try disconnecting and reconnecting
- Check browser console for WebSocket errors
</details>

<details>
<summary><strong>Vocabulary Not Showing</strong></summary>

- Ensure you're having a Japanese conversation
- Verify GPT-4 API access (required for analysis)
- Check the vocabulary panel is enabled (checkbox in sidebar)
- Wait a moment after speaking - analysis takes 1-2 seconds
- Check browser console for errors
</details>

<details>
<summary><strong>Microphone Not Working</strong></summary>

- Allow microphone permissions in browser
- Check microphone is selected correctly in system settings
- Try using Chrome or Edge browser
- Test microphone in other apps first
- Restart browser if permissions were recently changed
</details>

<details>
<summary><strong>Debug Mode</strong></summary>

- Enable debug mode in sidebar's "Developer Options" for verbose logging
- Check console output for detailed connection and audio information
- Useful for reporting issues with specific error messages
</details>

## ⚠️ Known Issues

- **Clear Chat Button**: Due to Streamlit's state management, the Clear Chat button may not immediately clear messages from the display. Messages will be cleared when the next interaction occurs. This is a known Streamlit limitation.
- **Multiple Voice Sessions**: Occasionally, multiple voice responses may overlap. If this happens, disconnect and reconnect.
- **Voice Recognition Delay**: There may be a 1-2 second delay before your speech is recognized and processed.
- **Browser Compatibility**: Best performance on Chrome and Edge. Safari and Firefox may have audio issues.

## 🤝 Contributing

Please submit bug reports and feature requests via Issues.

## 📄 License

MIT License
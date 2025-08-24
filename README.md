# 🗾 AI Voice Chat - Japanese Conversation Learning with Vocabulary Tracking

Real-time voice conversation app for Japanese language learning using OpenAI's Realtime API.  
Practice Japanese through natural conversations while automatically analyzing and tracking vocabulary.

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

1. **Connect**: Enter OpenAI API key and click "Connect"
2. **Select Character**: Choose an AI conversation partner
3. **Start Conversation**: Click "Start Conversation"
4. **Speak Naturally**: Have a conversation in Japanese
5. **Track Vocabulary**: View real-time vocabulary in the right panel
6. **Export**: Download your vocabulary list for study

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
│   ├── personas.json           # AI character configurations
│   └── settings.json           # App settings
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

### No Audio Output
- Verify PyAudio installation: `pip install pyaudio`
- Check speaker settings
- Review console logs

### Connection Issues
- Verify API key
- Check Realtime API access
- Confirm network connectivity

### Vocabulary Not Showing
- Ensure Japanese conversation
- Verify GPT-4 API access
- Check browser console for errors

### Debug Mode
- Enable debug mode in sidebar's "Developer Options" for verbose logging

## 🤝 Contributing

Please submit bug reports and feature requests via Issues.

## 📄 License

MIT License
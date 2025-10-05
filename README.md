# Real-time Meeting Transcription with AI Analysis

A comprehensive web application that demonstrates real-time meeting transcription using the [Attendee](https://github.com/attendee-labs/attendee) open-source meeting bot API, enhanced with AI-powered conversation analysis and automatic diagram generation. This app launches a bot that joins online meetings (Google Meet, Microsoft Teams, Zoom), transcribes conversations in real-time, analyzes them using Google's Gemini AI, and creates visual diagrams in Miro.

## Features

- 🤖 Launch meeting bots with a single click
- 📝 Real-time transcription with speaker identification
- 📹 Support for Google Meet, Microsoft Teams, and Zoom meetings
- 🧠 AI-powered conversation analysis using Google Gemini
- 📊 Automatic diagram generation in Miro
- 📋 Key topics, decisions, and action items extraction
- 👥 Speaker engagement analysis
- 🔄 Real-time conversation buffering and analysis

## Prerequisites

1. **Attendee Instance**: You need a running instance of [Attendee](https://github.com/attendee-labs/attendee). This can be the hosted instance at https://app.attendee.dev or an instance hosted on your local machine.

2. **Ngrok** (If using the cloud instance of Attendee): Since Attendee needs to send webhooks to your local application, you'll need [ngrok](https://ngrok.com/) to create a secure tunnel to your localhost. Ngrok is free for basic usage.

3. **Python 3.7+**: This demo uses Flask and requires Python 3.7 or higher.

4. **API Keys**: You'll need to create:
   - An API key from your Attendee dashboard
   - A webhook URL that points to your locally running instance of this application via ngrok
   - A Google Gemini API key for conversation analysis
   - A Miro access token for diagram creation

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/attendee-labs/realtime-transcription-example
cd realtime-transcription-example
```

### 2. Install virtual environment and dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Install and Run Ngrok

1. **Install ngrok**: Download from [ngrok.com](https://ngrok.com/) or install via package manager:
   ```bash
   # On macOS with Homebrew
   brew install ngrok
   
   # On Ubuntu/Debian
   snap install ngrok
   ```

2. **Start ngrok tunnel**: In a separate terminal, run:
   ```bash
   ngrok http 5005
   ```
   
3. **Copy the public URL**: Ngrok will display something like:
   ```
   Forwarding    https://abc123.ngrok.io -> http://localhost:5005
   ```
   Copy the `https://abc123.ngrok.io` URL - you'll need this for webhook configuration.

### 4. Configure Attendee

1. Sign into your Attendee account
2. Navigate to the API Keys section and create a new API key
3. Set up a webhook endpoint:
   - Go to Settings -> Webhooks
   - Add a new webhook with URL: `https://your-ngrok-url.ngrok.io/webhook` (replace with your actual ngrok URL)
   - Subscribe to these events:
     - `transcript.update` - For real-time transcription
     - `bot.state_change` - For bot status updates
   - Copy the webhook secret

### 5. Set Environment Variables

Create a `config.env` file in the project root (copy from `config.env.example`):

```bash
cp config.env.example config.env
```

Then edit `config.env` with your actual API keys:

```bash
# Attendee API Configuration
ATTENDEE_API_KEY=your_attendee_api_key_here
WEBHOOK_SECRET=your_webhook_secret_here
ATTENDEE_API_BASE=https://app.attendee.dev

# Gemini API Configuration (for conversation analysis)
GEMINI_API_KEY=your_gemini_api_key_here

# Miro API Configuration (for diagram creation)
MIRO_ACCESS_TOKEN=your_miro_access_token_here
```

#### Getting API Keys:

1. **Attendee API Key**: 
   - Sign up at https://app.attendee.dev
   - Go to API Keys section and create a new key

2. **Gemini API Key**:
   - Go to https://makersuite.google.com/app/apikey
   - Create a new API key

3. **Miro Access Token**:
   - Go to https://developers.miro.com/
   - Create a new app and generate an access token

### 6. Run the Application

```bash
python app.py
```

The server will start on `http://localhost:5005`. You can access it locally, but webhooks will be received via the ngrok tunnel.

## Usage

1. **Open the Web Interface**: Navigate to `http://localhost:5005` in your browser

2. **Enter Meeting URL**: Paste a meeting URL from:
   - Google Meet: `https://meet.google.com/xxx-xxxx-xxx`
   - Microsoft Teams: `https://teams.microsoft.com/...`
   - Zoom: `https://zoom.us/j/...` (requires Zoom credentials in Attendee)

3. **Launch Bot**: Click "Launch Bot & Start Transcribing"
   - The bot will join the meeting (may take up to 1 minute)
   - Status updates will show the bot's progress

4. **View Transcripts**: Real-time transcripts appear in the transcript area with:
   - Timestamp
   - Speaker name
   - Transcribed text

5. **Analyze Conversation**: Click "Analyze Conversation" to:
   - Extract key topics and their importance
   - Identify decisions made during the meeting
   - Find action items and assignees
   - Analyze speaker engagement levels

6. **Create Miro Diagram**: Click "Create Miro Diagram" to:
   - Generate a visual diagram in Miro
   - Display topics as sticky notes
   - Color-code by importance
   - Get a direct link to the Miro board

7. **Leave Meeting**: Click "Leave Meeting" to make the bot exit

## Architecture

### Frontend (`index.html`)
- Single-page application with vanilla JavaScript
- Server-Sent Events (SSE) for real-time updates
- LocalStorage for persisting meeting URLs
- Real-time status indicators and transcript display

### Backend (`app.py`)
- **Flask** web framework with AI integration
- **Core Endpoints**:
  - `POST /launch` - Creates a bot via Attendee API
  - `POST /webhook` - Receives Attendee webhooks (verified with HMAC-SHA256)
  - `GET /stream` - SSE endpoint for real-time updates to browsers
  - `POST /leave/<bot_id>` - Makes bot leave the meeting
  - `GET /` - Serves the web interface
- **AI Analysis Endpoints**:
  - `POST /analyze-conversation/<bot_id>` - Analyzes conversation using Gemini AI
  - `POST /create-diagram/<bot_id>` - Creates Miro diagram from analysis
  - `GET /conversation-status/<bot_id>` - Gets conversation buffer status
- **Features**:
  - Conversation buffering system (stores last 50 transcripts)
  - Thread-safe analysis with locks
  - Gemini AI integration for conversation analysis
  - Miro API integration for diagram creation

## Bot States

The bot progresses through these states:
- `ready` - Bot created, preparing to join
- `joining` - Attempting to join the meeting
- `waiting_room` - In meeting waiting room (if enabled)
- `joined_not_recording` - In meeting but not recording yet
- `joined_recording` - Actively recording and transcribing
- `leaving` - Exiting the meeting
- `post_processing` - Processing final data after leaving
- `ended` - Bot session complete
- `fatal_error` - An error occurred

## Troubleshooting

### Bot Won't Join
- Verify meeting URL is correct and active
- Check Attendee logs for errors
- Ensure bot has permission to join (not blocked by org policies)

### No Transcripts Appearing
- Verify webhook URL is accessible from Attendee instance
- Ensure `transcript.update` trigger is enabled in webhook settings
- Check Flask console for webhook receipt

### Connection Issues
- **Webhook not receiving data**: Ensure ngrok is running and pointing to port 5005:
  ```bash
  ngrok http 5005
  ```

## Acknowledgments

Built with [Attendee](https://github.com/attendee-labs/attendee) - the open-source meeting bot API.

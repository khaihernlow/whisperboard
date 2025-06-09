# Attendee Real-time Transcription Demo

A web application that demonstrates real-time meeting transcription using the [Attendee](https://github.com/attendee-labs/attendee) open-source meeting bot API. This demo allows you to launch a bot that joins online meetings (Google Meet, Microsoft Teams, Zoom) and view the transcript in real-time.

🎬 **[Watch the installation & usage video tutorial](https://www.loom.com/share/55cd2aa81b3d43f28c2cd179711b02fa#Edit)** to see the complete setup process.


## Features

- 🤖 Launch meeting bots with a single click
- 📝 Real-time transcription with speaker identification
- 📹 Support for Google Meet, Microsoft Teams, and Zoom meetings

## Prerequisites

1. **Attendee Instance**: You need a running instance of [Attendee](https://github.com/attendee-labs/attendee). This can be the hosted instance at https://app.attendee.dev or an instance hosted on your local machine.

2. **Ngrok** (If using the cloud instance of Attendee): Since Attendee needs to send webhooks to your local application, you'll need [ngrok](https://ngrok.com/) to create a secure tunnel to your localhost. Ngrok is free for basic usage.

2. **Python 3.7+**: This demo uses Flask and requires Python 3.7 or higher.

4. **Attendee Credentials**: You'll need to create:
   - An API key from your Attendee dashboard
   - A webhook URL that points to your locally running instance of this application via ngrok.

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

```bash
export ATTENDEE_API_KEY="your-api-key"
export WEBHOOK_SECRET="your-webhook-secret"
export ATTENDEE_API_BASE="https://app.attendee.dev"  # Optional, defaults to https://app.attendee.dev
```

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

5. **Leave Meeting**: Click "Leave Meeting" to make the bot exit

## Architecture

### Frontend (`index.html`)
- Single-page application with vanilla JavaScript
- Server-Sent Events (SSE) for real-time updates
- LocalStorage for persisting meeting URLs
- Real-time status indicators and transcript display

### Backend (`app.py`)
- **Flask** web framework
- **Endpoints**:
  - `POST /launch` - Creates a bot via Attendee API
  - `POST /webhook` - Receives Attendee webhooks (verified with HMAC-SHA256)
  - `GET /stream` - SSE endpoint for real-time updates to browsers
  - `POST /leave/<bot_id>` - Makes bot leave the meeting
  - `GET /` - Serves the web interface

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

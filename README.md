# Whisperboard - Meeting Transcription and Analysis

A Flask application that provides real-time meeting transcription using the Attendee API, with AI-powered conversation analysis and Miro board integration.

## Project Structure

```
whisperboard/
├── app/                          # Main application package
│   ├── __init__.py              # Package initialization
│   ├── config/                  # Configuration management
│   │   ├── __init__.py         # Config package init
│   │   └── settings.py         # Environment and app settings
│   ├── models/                  # Data models
│   │   └── __init__.py         # Data models (ConversationBuffer, BotSession, etc.)
│   ├── routes/                  # Route handlers
│   │   ├── main.py             # Main application routes
│   │   └── api.py              # API endpoints
│   └── services/               # External service integrations
│       └── __init__.py         # Service classes (Attendee, Gemini, Miro)
├── static/                     # Static assets
│   ├── css/
│   │   └── style.css           # Application styles
│   └── js/
│       ├── app.js              # Main application logic
│       ├── analysis.js         # Conversation analysis functionality
│       ├── miro.js             # Miro board integration
│       └── utils.js            # Utility functions
├── templates/                   # HTML templates
│   └── index.html              # Main application template
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
└── README.md                   # This file
```

## Features

- **Real-time Transcription**: Live meeting transcription using Attendee API
- **AI Analysis**: Conversation analysis using Google Gemini AI
- **Visual Diagrams**: Automatic Miro board creation with meeting insights
- **Modern UI**: Clean, responsive interface with organized code structure

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables in `.env`:
   ```
   ATTENDEE_API_KEY=your_attendee_api_key
   WEBHOOK_SECRET=your_webhook_secret
   GEMINI_API_KEY=your_gemini_api_key
   MIRO_ACCESS_TOKEN=your_miro_access_token
   ```

3. Run the application:
   ```bash
   python main.py
   ```

## Architecture

### Backend Structure

- **Config**: Centralized configuration management with environment-based settings
- **Models**: Data structures for conversation buffering and session management
- **Services**: External API integrations (Attendee, Gemini, Miro) with proper error handling
- **Routes**: Organized API endpoints with clear separation of concerns

### Frontend Structure

- **Modular JavaScript**: Separated into logical modules (app, analysis, miro, utils)
- **CSS Organization**: Centralized styling with clear component separation
- **Template System**: Jinja2 templates for better maintainability

### Key Improvements

1. **Separation of Concerns**: Each module has a single responsibility
2. **Error Handling**: Proper exception handling throughout the application
3. **Configuration Management**: Environment-based configuration
4. **Code Organization**: Clear directory structure and naming conventions
5. **Maintainability**: Modular code that's easy to understand and modify

## API Endpoints

- `POST /api/launch` - Launch a transcription bot
- `POST /api/leave/<bot_id>` - Make bot leave meeting
- `GET /api/transcripts/<bot_id>` - Get meeting transcripts
- `GET /api/bot-status/<bot_id>` - Get bot status
- `POST /api/analyze-conversation/<bot_id>` - Analyze conversation with AI
- `POST /api/create-diagram/<bot_id>` - Create Miro diagram from analysis
- `GET /api/miro-board-info` - Get Miro board information
- `GET /api/conversation-status/<bot_id>` - Get conversation buffer status

## Development

The application follows Flask best practices with:
- Blueprint-based routing
- Application factory pattern
- Proper error handling
- Environment-based configuration
- Modular frontend architecture

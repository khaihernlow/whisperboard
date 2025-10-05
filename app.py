"""
Flask demo that
  • POST /launch  – creates a bot in Attendee and returns its id
  • POST /webhook – receives real‑time transcript.update webhooks
  • GET  /stream  – server‑sent‑events (SSE) feed the browser listens to
Environment variables
  ATTENDEE_API_KEY   – your Attendee API key
  WEBHOOK_SECRET     – your base‑64 secret from Attendee's dashboard
  ATTENDEE_API_BASE  – default https://app.attendee.dev
Run with:  python app.py
"""
import os, json, hmac, hashlib, base64, queue, threading, time
from typing import Dict, List
from collections import deque
import google.generativeai as genai

import requests
from flask import Flask, Response, request, stream_with_context, jsonify, abort, send_from_directory
from dotenv import load_dotenv

# Load environment variables from config.env file
load_dotenv('.env')

ATTENDEE_API_KEY  = os.getenv("ATTENDEE_API_KEY")
WEBHOOK_SECRET    = os.getenv("WEBHOOK_SECRET")
ATTENDEE_API_BASE = os.getenv("ATTENDEE_API_BASE", "https://app.attendee.dev")
GEMINI_API_KEY    = os.getenv("GEMINI_API_KEY")
MIRO_ACCESS_TOKEN = os.getenv("MIRO_ACCESS_TOKEN")

if not ATTENDEE_API_KEY or not WEBHOOK_SECRET:
    raise RuntimeError("Set ATTENDEE_API_KEY and WEBHOOK_SECRET env vars first")

# Initialize Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-pro')
else:
    print("Warning: GEMINI_API_KEY not set. Conversation analysis will be disabled.")

app = Flask(
    __name__,
    static_url_path="",      # serve "index.html", "some.png" directly
    static_folder="."        # treat the current dir as the static folder
)
subscribers: List[queue.Queue] = []          # live SSE listeners

# Conversation buffering and analysis
conversation_buffers: Dict[str, deque] = {}  # bot_id -> deque of transcripts
analysis_lock = threading.Lock()

# ----------------------------------------------------------------------
# Helper: forward JSON objects to every connected SSE client
# ----------------------------------------------------------------------
def broadcast(obj: Dict):
    for q in list(subscribers):              # copy → tolerate removals
        try:
            q.put_nowait(obj)
        except queue.Full:
            pass

# ----------------------------------------------------------------------
# Conversation Analysis Functions
# ----------------------------------------------------------------------
def add_transcript_to_buffer(bot_id: str, transcript_data: Dict):
    """Add a transcript entry to the conversation buffer"""
    with analysis_lock:
        if bot_id not in conversation_buffers:
            conversation_buffers[bot_id] = deque(maxlen=50)  # Keep last 50 transcripts
        
        conversation_buffers[bot_id].append({
            'timestamp': transcript_data.get('timestamp_ms', 0),
            'speaker': transcript_data.get('speaker_name', 'Unknown'),
            'text': transcript_data.get('transcription', {}).get('transcript', ''),
            'confidence': transcript_data.get('transcription', {}).get('confidence', 0)
        })

def analyze_conversation_with_gemini(bot_id: str) -> Dict:
    """Analyze the conversation using Gemini API and return diagram data"""
    if not GEMINI_API_KEY or bot_id not in conversation_buffers:
        return {"error": "No API key or conversation data available"}
    
    with analysis_lock:
        if not conversation_buffers[bot_id]:
            return {"error": "No conversation data to analyze"}
        
        # Format conversation for analysis
        conversation_text = "\n".join([
            f"[{entry['speaker']}]: {entry['text']}" 
            for entry in conversation_buffers[bot_id]
        ])
    
    try:
        prompt = f"""
        Analyze this meeting conversation and create a structured diagram representation. 
        Focus on:
        1. Key topics discussed
        2. Decisions made
        3. Action items
        4. Relationships between speakers and topics
        5. Timeline of important points
        
        Conversation:
        {conversation_text}
        
        Return a JSON response with this structure:
        {{
            "topics": [{{"name": "topic_name", "importance": 0.8, "description": "brief description"}}],
            "decisions": [{{"title": "decision_title", "description": "details", "timestamp": "when discussed"}}],
            "action_items": [{{"task": "action description", "assignee": "person", "priority": "high/medium/low"}}],
            "speakers": [{{"name": "speaker_name", "role": "inferred role", "engagement": 0.7}}],
            "relationships": [{{"from": "speaker1", "to": "speaker2", "type": "collaboration/discussion", "strength": 0.8}}],
            "timeline": [{{"event": "description", "timestamp": "time", "importance": 0.6}}]
        }}
        """
        
        response = gemini_model.generate_content(prompt)
        
        # Try to parse the JSON response
        try:
            # Extract JSON from response (might have extra text)
            response_text = response.text
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            analysis_result = json.loads(response_text)
            analysis_result["timestamp"] = time.time()
            analysis_result["bot_id"] = bot_id
            
            return analysis_result
            
        except json.JSONDecodeError:
            return {
                "error": "Failed to parse Gemini response",
                "raw_response": response.text,
                "timestamp": time.time(),
                "bot_id": bot_id
            }
            
    except Exception as e:
        return {
            "error": f"Gemini analysis failed: {str(e)}",
            "timestamp": time.time(),
            "bot_id": bot_id
        }

def create_miro_diagram(analysis_data: Dict) -> Dict:
    """Create a Miro diagram based on conversation analysis"""
    if not MIRO_ACCESS_TOKEN:
        return {"error": "Miro access token not configured"}
    
    try:
        # Create a new Miro board
        board_response = requests.post(
            "https://api.miro.com/v2/boards",
            headers={
                "Authorization": f"Bearer {MIRO_ACCESS_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "name": f"Meeting Analysis - {time.strftime('%Y-%m-%d %H:%M')}",
                "description": "Auto-generated from meeting transcription analysis"
            }
        )
        
        if board_response.status_code != 201:
            return {"error": f"Failed to create Miro board: {board_response.text}"}
        
        board_data = board_response.json()
        board_id = board_data["id"]
        
        # Add topics as sticky notes
        topic_items = []
        if "topics" in analysis_data:
            for i, topic in enumerate(analysis_data["topics"][:10]):  # Limit to top 10
                x = (i % 3) * 300
                y = (i // 3) * 200
                
                sticky_note = requests.post(
                    f"https://api.miro.com/v2/boards/{board_id}/sticky_notes",
                    headers={
                        "Authorization": f"Bearer {MIRO_ACCESS_TOKEN}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "data": {
                            "content": f"<p><strong>{topic['name']}</strong></p><p>{topic.get('description', '')}</p>",
                            "style": {
                                "fillColor": "#ff9d48" if topic.get('importance', 0) > 0.7 else "#4c9aff"
                            }
                        },
                        "position": {
                            "x": x,
                            "y": y
                        }
                    }
                )
                
                if sticky_note.status_code == 201:
                    topic_items.append(sticky_note.json())
        
        return {
            "success": True,
            "board_id": board_id,
            "board_url": f"https://miro.com/app/board/{board_id}/",
            "items_created": len(topic_items),
            "timestamp": time.time()
        }
        
    except Exception as e:
        return {"error": f"Miro diagram creation failed: {str(e)}"}

# ----------------------------------------------------------------------
# Endpoint: Launch a bot
# ----------------------------------------------------------------------
@app.get("/welcome")
def welcome():
    return jsonify({"message": "Welcome to the Attendee API!"}), 200

@app.post("/launch")
def launch_bot():
    data = request.get_json(force=True)
    meeting_url = data.get("meeting_url")
    if not meeting_url:
        return jsonify({"error": "meeting_url is required"}), 400

    payload = {
        "meeting_url": meeting_url,
        "bot_name":   "Transcription‑Demo",
        # Note: Webhooks require HTTPS, so we'll set them up later with ngrok
    }
    resp = requests.post(
        f"{ATTENDEE_API_BASE}/api/v1/bots",
        headers={
            "Authorization": f"Token {ATTENDEE_API_KEY}",
            "Content-Type":  "application/json",
        },
        json=payload,
        timeout=30,
    )
    if resp.status_code >= 300:
        return jsonify({"error": resp.text}), resp.status_code

    bot = resp.json()
    return jsonify({"bot_id": bot["id"]}), 201

# ----------------------------------------------------------------------
# Endpoint: Make bot leave meeting
# ----------------------------------------------------------------------
@app.post("/leave/<bot_id>")
def leave_bot(bot_id):
    resp = requests.post(
        f"{ATTENDEE_API_BASE}/api/v1/bots/{bot_id}/leave",
        headers={
            "Authorization": f"Token {ATTENDEE_API_KEY}",
            "Content-Type":  "application/json",
        },
        json={},
        timeout=30,
    )
    if resp.status_code >= 300:
        return jsonify({"error": resp.text}), resp.status_code

    return jsonify({"success": True}), 200

# ----------------------------------------------------------------------
# Endpoint: Webhook receiver  (transcript.update, etc.)
# ----------------------------------------------------------------------
def _sign_payload(payload: Dict) -> str:
    """
    Return base‑64 HMAC‑SHA256 of canonical JSON payload.
    """
    payload_json = json.dumps(payload, sort_keys=True, ensure_ascii=False,
                              separators=(",", ":"))
    secret = base64.b64decode(WEBHOOK_SECRET)
    digest = hmac.new(secret, payload_json.encode(), hashlib.sha256).digest()
    return base64.b64encode(digest).decode()

@app.post("/webhook")
def webhook():
    try:
        payload = request.get_json(force=True)
    except Exception:
        abort(400, "invalid JSON")

    sig_header = request.headers.get("X-Webhook-Signature", "")
    if sig_header != _sign_payload(payload):
        abort(400, "invalid signature")

    # Forward transcript lines
    if payload.get("trigger") == "transcript.update":
        broadcast({
            "type": "transcript",
            "data": payload["data"]
        })
    
    # Forward bot status changes
    elif payload.get("trigger") == "bot.state_change":
        broadcast({
            "type": "status",
            "data": payload["data"]
        })

    return "", 200

# ----------------------------------------------------------------------
# Endpoint: Server‑Sent Events stream
# ----------------------------------------------------------------------
@app.get("/stream")
def stream():
    client_q: queue.Queue = queue.Queue()
    subscribers.append(client_q)

    @stream_with_context
    def gen():
        try:
            # Send a comment every 15 s so proxies keep the connection alive
            keepalive = time.time()
            while True:
                try:
                    msg = client_q.get(timeout=1)
                    yield f"data: {json.dumps(msg)}\n\n"
                except queue.Empty:
                    pass
                if time.time() - keepalive > 15:
                    yield ": keep‑alive\n\n"
                    keepalive = time.time()
        finally:
            subscribers.remove(client_q)

    return Response(gen(), mimetype="text/event-stream")

# ----------------------------------------------------------------------

@app.get("/transcripts/<bot_id>")
def get_transcripts(bot_id):
    """Poll the Attendee API to get transcript data for a bot"""
    try:
        # Get transcripts from Attendee API
        # Try different possible endpoints for transcripts
        endpoints_to_try = [
            f"{ATTENDEE_API_BASE}/api/v1/bots/{bot_id}/transcript",
            f"{ATTENDEE_API_BASE}/api/v1/bots/{bot_id}/transcriptions",
            f"{ATTENDEE_API_BASE}/api/v1/bots/{bot_id}/transcript-data",
            f"{ATTENDEE_API_BASE}/api/v1/transcripts?bot_id={bot_id}",
            f"{ATTENDEE_API_BASE}/api/v1/transcriptions?bot_id={bot_id}"
        ]
        
        resp = None
        for endpoint in endpoints_to_try:
            try:
                resp = requests.get(
                    endpoint,
                    headers={
                        "Authorization": f"Token {ATTENDEE_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    timeout=10,
                )
                if resp.status_code == 200:
                    break
            except:
                continue
        
        if resp is None or resp.status_code >= 300:
            print(f"All transcript endpoints failed for bot {bot_id}")
            return jsonify({"error": "No transcript endpoint found", "transcripts": []}), 404
        
        transcripts = resp.json()
        print(f"Transcript response for bot {bot_id}: {transcripts}")  # Debug output
        
        # Add new transcripts to conversation buffer
        if isinstance(transcripts, list):
            for transcript in transcripts:
                add_transcript_to_buffer(bot_id, transcript)
        
        return jsonify(transcripts)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/bot-status/<bot_id>")
def get_bot_status(bot_id):
    """Get the current status of a bot"""
    try:
        resp = requests.get(
            f"{ATTENDEE_API_BASE}/api/v1/bots/{bot_id}",
            headers={
                "Authorization": f"Token {ATTENDEE_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=10,
        )
        
        if resp.status_code >= 300:
            return jsonify({"error": resp.text}), resp.status_code
        
        bot_data = resp.json()
        print(f"Bot status response: {bot_data}")  # Debug output
        return jsonify(bot_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------------------------------------------------------------
# Endpoint: Analyze conversation with Gemini
# ----------------------------------------------------------------------
@app.post("/analyze-conversation/<bot_id>")
def analyze_conversation(bot_id):
    """Analyze the conversation using Gemini API"""
    try:
        analysis_result = analyze_conversation_with_gemini(bot_id)
        return jsonify(analysis_result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------------------------------------------------------------
# Endpoint: Create Miro diagram from analysis
# ----------------------------------------------------------------------
@app.post("/create-diagram/<bot_id>")
def create_diagram(bot_id):
    """Create a Miro diagram from conversation analysis"""
    try:
        # First analyze the conversation
        analysis_result = analyze_conversation_with_gemini(bot_id)
        
        if "error" in analysis_result:
            return jsonify(analysis_result), 400
        
        # Create the Miro diagram
        diagram_result = create_miro_diagram(analysis_result)
        
        return jsonify({
            "analysis": analysis_result,
            "diagram": diagram_result
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------------------------------------------------------------
# Endpoint: Get conversation buffer status
# ----------------------------------------------------------------------
@app.get("/conversation-status/<bot_id>")
def get_conversation_status(bot_id):
    """Get the current status of conversation buffer"""
    with analysis_lock:
        if bot_id not in conversation_buffers:
            return jsonify({
                "bot_id": bot_id,
                "transcript_count": 0,
                "has_data": False
            })
        
        buffer_data = list(conversation_buffers[bot_id])
        return jsonify({
            "bot_id": bot_id,
            "transcript_count": len(buffer_data),
            "has_data": len(buffer_data) > 0,
            "latest_transcript": buffer_data[-1] if buffer_data else None,
            "speakers": list(set(entry['speaker'] for entry in buffer_data))
        })

@app.get("/")                # ← add this route
def index():
    # send the SPA entry‑point
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, threaded=True, debug=True)

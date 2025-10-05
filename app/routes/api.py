"""
API routes for the application
"""
import json
import os
import hmac
import hashlib
import base64
import queue
import threading
import time
from typing import Dict, List
from flask import Blueprint, request, jsonify, abort, Response, stream_with_context
from app.services import AttendeeService, GeminiService, MiroService
from app.models import ConversationBuffer, BotSession, AnalysisResult
from app.config.settings import WEBHOOK_SECRET

api_bp = Blueprint('api', __name__)

# Global state
subscribers: List[queue.Queue] = []
bot_sessions: Dict[str, BotSession] = {}
sessions_lock = threading.Lock()

# Demo conversations directory
DEMO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'demo_conversations'))

# Initialize services
attendee_service = AttendeeService()
gemini_service = GeminiService()
miro_service = MiroService()

def broadcast(obj: Dict):
    """Broadcast message to all SSE subscribers"""
    for q in list(subscribers):
        try:
            q.put_nowait(obj)
        except queue.Full:
            pass

def get_or_create_bot_session(bot_id: str) -> BotSession:
    """Get existing bot session or create new one"""
    with sessions_lock:
        if bot_id not in bot_sessions:
            bot_sessions[bot_id] = BotSession(bot_id)
        return bot_sessions[bot_id]

def _sign_payload(payload: Dict) -> str:
    """Return base-64 HMAC-SHA256 of canonical JSON payload"""
    payload_json = json.dumps(payload, sort_keys=True, ensure_ascii=False,
                              separators=(",", ":"))
    secret = base64.b64decode(WEBHOOK_SECRET)
    digest = hmac.new(secret, payload_json.encode(), hashlib.sha256).digest()
    return base64.b64encode(digest).decode()

def _safe_filename(name: str) -> str:
    """Prevent path traversal; allow only basenames with .txt"""
    base = os.path.basename(name)
    if not base.endswith('.txt'):
        base = base + '.txt'
    return base

def _get_or_create_board_id() -> str:
    """Return the persistent Miro board id, creating it if missing."""
    boards = miro_service.get_boards()
    board_id = None
    for board in boards:
        if board.get('name') == 'Meeting Analysis Board':
            board_id = board['id']
            break
    if not board_id:
        board_data = miro_service.create_board()
        board_id = board_data["id"]
    return board_id

@api_bp.route('/launch', methods=['POST'])
def launch_bot():
    """Launch a bot for the meeting"""
    data = request.get_json(force=True)
    meeting_url = data.get("meeting_url")
    if not meeting_url:
        return jsonify({"error": "meeting_url is required"}), 400

    try:
        bot = attendee_service.create_bot(meeting_url)
        # New meeting: clear the board to start fresh
        try:
            board_id = _get_or_create_board_id()
            miro_service.clear_board_items(board_id)
        except Exception:
            pass
        return jsonify({"bot_id": bot["id"]}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/leave/<bot_id>', methods=['POST'])
def leave_bot(bot_id):
    """Make bot leave the meeting"""
    try:
        result = attendee_service.leave_bot(bot_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/webhook', methods=['POST'])
def webhook():
    """Receive webhook from Attendee"""
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

@api_bp.route('/stream')
def stream():
    """Server-Sent Events stream"""
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

@api_bp.route('/transcripts/<bot_id>')
def get_transcripts(bot_id):
    """Get transcripts for a bot"""
    try:
        transcripts = attendee_service.get_transcripts(bot_id)
        
        # Add transcripts to conversation buffer
        session = get_or_create_bot_session(bot_id)
        if isinstance(transcripts, list):
            for transcript in transcripts:
                session.conversation_buffer.add_transcript(transcript)
                session.update_activity()
        
        return jsonify(transcripts)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/demo/list')
def list_demo_conversations():
    """List available demo conversation files"""
    try:
        if not os.path.isdir(DEMO_DIR):
            return jsonify({"files": []})
        files = [f for f in os.listdir(DEMO_DIR) if f.endswith('.txt')]
        return jsonify({"files": sorted(files)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/demo/load/<bot_id>', methods=['POST'])
def load_demo_conversation(bot_id):
    """Load a demo conversation file into the buffer and return status"""
    try:
        data = request.get_json(force=True)
        filename = _safe_filename(data.get('filename', ''))
        path = os.path.join(DEMO_DIR, filename)
        if not os.path.isfile(path):
            return jsonify({"error": "File not found"}), 404

        session = get_or_create_bot_session(bot_id)
        # Clear the board for demo loads to start fresh
        try:
            board_id = _get_or_create_board_id()
            miro_service.clear_board_items(board_id)
        except Exception:
            pass
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()
        # Expect format: "Speaker: text" per line; fall back to single-speaker if absent
        ts = int(time.time() * 1000)
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            if ':' in line:
                speaker, text = line.split(':', 1)
                speaker = speaker.strip()
                text = text.strip()
            else:
                speaker = 'Demo'
                text = line.strip()
            transcript = {
                'timestamp_ms': ts + i * 1000,
                'speaker_name': speaker,
                'transcription': {'transcript': text, 'confidence': 1.0}
            }
            session.conversation_buffer.add_transcript(transcript)
            session.update_activity()
        return jsonify({"success": True, "lines": len(lines)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/bot-status/<bot_id>')
def get_bot_status(bot_id):
    """Get the current status of a bot"""
    try:
        bot_data = attendee_service.get_bot_status(bot_id)
        return jsonify(bot_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/analyze-conversation/<bot_id>', methods=['POST'])
def analyze_conversation(bot_id):
    """Analyze the conversation using Gemini API"""
    try:
        session = get_or_create_bot_session(bot_id)
        
        if session.conversation_buffer.is_empty():
            return jsonify({"error": "No conversation data to analyze"}), 400
        
        conversation_text = session.conversation_buffer.get_conversation_text()
        analysis_result = gemini_service.analyze_conversation(conversation_text)
        
        if "error" not in analysis_result:
            analysis_result["bot_id"] = bot_id
        
        return jsonify(analysis_result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/create-diagram/<bot_id>', methods=['POST'])
def create_diagram(bot_id):
    """Create a Miro diagram from conversation analysis"""
    try:
        # First analyze the conversation
        session = get_or_create_bot_session(bot_id)
        
        if session.conversation_buffer.is_empty():
            return jsonify({"error": "No conversation data to analyze"}), 400
        
        conversation_text = session.conversation_buffer.get_conversation_text()
        analysis_result = gemini_service.analyze_conversation(conversation_text)
        
        if "error" in analysis_result:
            return jsonify(analysis_result), 400
        
        # Get or create the persistent Miro board
        try:
            boards = miro_service.get_boards()
            board_id = None
            
            # Look for existing meeting analysis board
            for board in boards:
                if board.get('name') == 'Meeting Analysis Board':
                    board_id = board['id']
                    break
            
            # Create new board if none found
            if not board_id:
                board_data = miro_service.create_board()
                board_id = board_data["id"]
            
            # Do not clear existing items; allow upsert/merge by similarity
            diagram_result = miro_service.create_diagram_from_analysis(board_id, analysis_result)
            
            return jsonify({
                "analysis": analysis_result,
                "diagram": diagram_result
            })
            
        except Exception as e:
            return jsonify({"error": f"Miro integration failed: {str(e)}"}), 500
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/miro-board-info')
def get_miro_board_info():
    """Get information about the persistent Miro board"""
    try:
        boards = miro_service.get_boards()
        board_id = None
        
        # Look for existing meeting analysis board
        for board in boards:
            if board.get('name') == 'Meeting Analysis Board':
                board_id = board['id']
                break
        
        # Create new board if none found
        if not board_id:
            board_data = miro_service.create_board()
            board_id = board_data["id"]
        
        return jsonify({
            "board_id": board_id,
            "board_url": f"https://miro.com/app/board/{board_id}/",
            "embed_url": f"https://miro.com/app/embed/{board_id}/"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/miro/reset', methods=['POST'])
def reset_miro_board():
    """Clear the persistent board on demand"""
    try:
        board_id = _get_or_create_board_id()
        miro_service.clear_board_items(board_id)
        return jsonify({"success": True, "board_id": board_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/conversation-status/<bot_id>')
def get_conversation_status(bot_id):
    """Get the current status of conversation buffer"""
    try:
        session = get_or_create_bot_session(bot_id)
        buffer_data = session.conversation_buffer.get_buffer_data()
        
        return jsonify({
            "bot_id": bot_id,
            "transcript_count": len(buffer_data),
            "has_data": len(buffer_data) > 0,
            "latest_transcript": buffer_data[-1] if buffer_data else None,
            "speakers": session.conversation_buffer.get_speakers()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

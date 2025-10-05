"""
External API services
"""
import json
import time
import requests
from typing import Dict, Optional
from google import genai
from app.config.settings import (
    ATTENDEE_API_KEY, ATTENDEE_API_BASE, GEMINI_API_KEY, MIRO_ACCESS_TOKEN
)

class AttendeeService:
    """Service for interacting with Attendee API"""
    
    def __init__(self):
        self.api_key = ATTENDEE_API_KEY
        self.base_url = ATTENDEE_API_BASE
    
    def create_bot(self, meeting_url: str, bot_name: str = "Transcription-Demo") -> Dict:
        """Create a new bot for the meeting"""
        payload = {
            "meeting_url": meeting_url,
            "bot_name": bot_name,
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/bots",
            headers={
                "Authorization": f"Token {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        
        if response.status_code >= 300:
            raise Exception(f"Failed to create bot: {response.text}")
        
        return response.json()
    
    def leave_bot(self, bot_id: str) -> Dict:
        """Make bot leave the meeting"""
        response = requests.post(
            f"{self.base_url}/api/v1/bots/{bot_id}/leave",
            headers={
                "Authorization": f"Token {self.api_key}",
                "Content-Type": "application/json",
            },
            json={},
            timeout=30,
        )
        
        if response.status_code >= 300:
            raise Exception(f"Failed to leave bot: {response.text}")
        
        return {"success": True}
    
    def get_bot_status(self, bot_id: str) -> Dict:
        """Get the current status of a bot"""
        response = requests.get(
            f"{self.base_url}/api/v1/bots/{bot_id}",
            headers={
                "Authorization": f"Token {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=10,
        )
        
        if response.status_code >= 300:
            raise Exception(f"Failed to get bot status: {response.text}")
        
        return response.json()
    
    def get_transcripts(self, bot_id: str) -> list:
        """Get transcripts for a bot"""
        endpoints_to_try = [
            f"{self.base_url}/api/v1/bots/{bot_id}/transcript",
            f"{self.base_url}/api/v1/bots/{bot_id}/transcriptions",
            f"{self.base_url}/api/v1/bots/{bot_id}/transcript-data",
            f"{self.base_url}/api/v1/transcripts?bot_id={bot_id}",
            f"{self.base_url}/api/v1/transcriptions?bot_id={bot_id}"
        ]
        
        for endpoint in endpoints_to_try:
            try:
                response = requests.get(
                    endpoint,
                    headers={
                        "Authorization": f"Token {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=10,
                )
                if response.status_code == 200:
                    return response.json()
            except:
                continue
        
        raise Exception("No transcript endpoint found")

class GeminiService:
    """Service for interacting with Gemini AI"""
    
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
    
    def analyze_conversation(self, conversation_text: str) -> Dict:
        """Analyze conversation using Gemini AI to produce structured map."""
        if not self.client:
            return {"error": "Gemini API key not configured"}
        
        prompt = f"""
        From the conversation below, produce a conversation map suitable for a Miro board.
        Goals: Show reasoning flow: why → how → what next. Keep total nodes 8–15.

        STRICT JSON OUTPUT ONLY with this schema:
        {{
          "topics": [
            {{"id": "t1", "label": "Offline mode feature", "description": "central idea", "importance": 0.0_to_1.0 }}
          ],
          "insights": [
            {{"id": "i1", "label": "Users have poor connectivity", "evidence": ["quotes", "metrics"], "confidence": 0.0_to_1.0, "supports": ["t1"] }}
          ],
          "decisions": [
            {{"id": "d1", "label": "Pilot with 20 users", "rationale": ["why"], "confidence": 0.0_to_1.0, "based_on": ["t1","i1"] }}
          ],
          "actions": [
            {{"id": "a1", "label": "Alice – implement API caching", "owner": "Alice", "due": "YYYY-MM-DD or null", "depends_on": ["d1"], "confidence": 0.0_to_1.0 }}
          ],
          "relationships": [
            {{"from": "t1", "to": "i1", "type": "leads_to|supports|results_in|blocks", "strength": 0.0_to_1.0 }}
          ],
          "summary": {{
            "frame_name": "<Meeting/Conversation Name> – <Time>",
            "blurb": "1-2 sentence summary of what was achieved"
          }}
        }}

        Behavioral rules:
        - Merge duplicates; prefer single canonical labels.
        - Every decision must have at least one incoming relationship from a topic/insight.
        - Prefer concise labels; put details into description/rationale/evidence.
        - Keep nodes 8–15 max total.

        Conversation:
        {conversation_text}
        """
        
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            # Extract JSON from response
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
            
            return analysis_result
            
        except json.JSONDecodeError:
            return {
                "error": "Failed to parse Gemini response",
                "raw_response": response.text,
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "error": f"Gemini analysis failed: {str(e)}",
                "timestamp": time.time()
            }

class MiroService:
    """Service for interacting with Miro API"""
    
    def __init__(self):
        self.access_token = MIRO_ACCESS_TOKEN
        self.base_url = "https://api.miro.com/v2"
    
    def create_board(self, name: str = "Meeting Analysis Board", description: str = "Persistent board for meeting transcription analysis") -> Dict:
        """Create a new Miro board"""
        if not self.access_token:
            raise Exception("Miro access token not configured")
        
        response = requests.post(
            f"{self.base_url}/boards",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            },
            json={
                "name": name,
                "description": description
            }
        )
        
        if response.status_code != 201:
            raise Exception(f"Failed to create Miro board: {response.text}")
        
        return response.json()
    
    def get_boards(self) -> list:
        """Get all Miro boards"""
        if not self.access_token:
            raise Exception("Miro access token not configured")
        
        response = requests.get(
            f"{self.base_url}/boards",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get boards: {response.text}")
        
        return response.json().get('data', [])
    
    def get_board_items(self, board_id: str) -> list:
        """Get all items from a board (single page)."""
        if not self.access_token:
            raise Exception("Miro access token not configured")
        
        response = requests.get(
            f"{self.base_url}/boards/{board_id}/items",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get board items: {response.text}")
        
        return response.json().get('data', [])
    
    def clear_board_items(self, board_id: str) -> None:
        """Clear all items from a board. Handles pagination by looping until empty."""
        while True:
            items = self.get_board_items(board_id)
            if not items:
                break
            for item in items:
                item_id = item.get('id')
                if not item_id:
                    continue
                resp = requests.delete(
                    f"{self.base_url}/boards/{board_id}/items/{item_id}",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    }
                )
                # Best-effort; continue even on non-2xx
    
    def create_sticky_note(self, board_id: str, content: str, position: Dict, style: Dict = None) -> Dict:
        """Create a sticky note on the board"""
        if not self.access_token:
            raise Exception("Miro access token not configured")
        
        payload = {
            "data": {
                "content": content,
                "shape": "square"
            },
            "position": position
        }
        
        if style:
            payload["style"] = style
        
        response = requests.post(
            f"{self.base_url}/boards/{board_id}/sticky_notes",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        if response.status_code != 201:
            raise Exception(f"Failed to create sticky note: {response.text}")
        
        return response.json()
    
    def create_connector(self, board_id: str, start_item_id: str, end_item_id: str, 
                        style: Dict = None, caption: str = None) -> Dict:
        """Create a connector (arrow) between two items"""
        if not self.access_token:
            raise Exception("Miro access token not configured")
        
        payload = {
            "start": {
                "item": {"id": start_item_id}
            },
            "end": {
                "item": {"id": end_item_id}
            }
        }
        
        if style:
            payload["style"] = style
        
        if caption:
            payload["caption"] = caption
        
        response = requests.post(
            f"{self.base_url}/boards/{board_id}/connectors",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        if response.status_code != 201:
            raise Exception(f"Failed to create connector: {response.text}")
        
        return response.json()
    
    def create_shape(self, board_id: str, shape_type: str, content: str, position: Dict, 
                    style: Dict = None) -> Dict:
        """Create a shape (rectangle, circle, etc.) on the board"""
        if not self.access_token:
            raise Exception("Miro access token not configured")
        
        # Extract width and height from position if they exist
        width = position.pop('width', 100)  # Default width
        height = position.pop('height', 100)  # Default height
        
        payload = {
            "data": {
                "content": content,
                "shape": shape_type
            },
            "position": position,
            "geometry": {
                "width": width,
                "height": height
            }
        }
        
        if style:
            payload["style"] = style
        
        response = requests.post(
            f"{self.base_url}/boards/{board_id}/shapes",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        if response.status_code != 201:
            raise Exception(f"Failed to create shape: {response.text}")
        
        return response.json()
    
    def create_diagram_from_analysis(self, board_id: str, analysis_data: Dict) -> Dict:
        """Create a Miro conversation map using lanes and upsert semantics."""
        items_created = []
        connectors_created = []

        def _normalize_label(text: str) -> str:
            return (text or "").strip().lower()

        def _similar(a: str, b: str) -> float:
            a_tokens = set(_normalize_label(a).split())
            b_tokens = set(_normalize_label(b).split())
            if not a_tokens or not b_tokens:
                return 0.0
            inter = len(a_tokens & b_tokens)
            union = len(a_tokens | b_tokens)
            return inter / union

        existing_items = self.get_board_items(board_id)

        def _find_similar(content_text: str, threshold: float = 0.7) -> Optional[Dict]:
            for it in existing_items:
                it_text = (it.get('data') or {}).get('content') or ''
                # crude strip HTML tags
                if _similar(content_text, it_text) >= threshold:
                    return it
            return None

        def _html(text: str) -> str:
            return f"<p><strong>{text}</strong></p>"

        # Lanes X positions
        lane_x = {
            'topics': 0,
            'insights': 800,
            'decisions': 1600,
            'actions': 2400,
        }

        # Headers
        headers = [
            ('topics', '📋 Topics', 'light_yellow'),
            ('insights', '🧠 Insights', 'light_blue'),
            ('decisions', '✅ Decisions', 'light_green'),
            ('actions', '📝 Actions', 'red'),
        ]
        for key, title, color in headers:
            header_html = _html(title)
            found = _find_similar(title, threshold=0.9)
            if not found:
                items_created.append(self.create_sticky_note(
                    board_id, header_html, {"x": lane_x[key], "y": -200}, {"fillColor": color, "textAlign": "center"}
                ))

        # Helper to upsert sticky note
        def upsert_sticky(label: str, details_html: str, color: str, x: int, y: int) -> Dict:
            content = f"<p><strong>{label}</strong></p>{details_html}"
            existing = _find_similar(label)
            if existing:
                # Update existing item content
                try:
                    return self.update_item(board_id, existing['id'], {
                        "data": {"content": content},
                        "position": {"x": x, "y": y},
                        "style": {"fillColor": color, "textAlign": "left"}
                    })
                except Exception:
                    pass
            created = self.create_sticky_note(board_id, content, {"x": x, "y": y}, {"fillColor": color, "textAlign": "left"})
            items_created.append(created)
            return created

        # Upsert methods
        def color_for(kind: str) -> str:
            return {
                'topic': 'light_yellow',
                'insight': 'light_blue',
                'decision': 'light_green',
                'action': 'red',
            }.get(kind, 'gray')

        id_to_item = {}

        # Topics
        for i, t in enumerate(analysis_data.get('topics', [])[:6]):
            x = lane_x['topics']
            y = 100 + i * 220
            details = f"<p>{t.get('description','')}</p>"
            node = upsert_sticky(t.get('label', t.get('name', 'Topic')), details, color_for('topic'), x, y)
            id_to_item[t.get('id', f't{i}')] = node

        # Insights
        for i, ins in enumerate(analysis_data.get('insights', [])[:6]):
            x = lane_x['insights']
            y = 100 + i * 220
            evidence = ins.get('evidence') or []
            details = ""
            if evidence:
                details = f"<p><small>Evidence: {', '.join(evidence[:3])}</small></p>"
            node = upsert_sticky(ins.get('label', 'Insight'), details, color_for('insight'), x, y)
            id_to_item[ins.get('id', f'i{i}')] = node

        # Decisions
        for i, dec in enumerate(analysis_data.get('decisions', [])[:5]):
            x = lane_x['decisions']
            y = 100 + i * 220
            rationale = dec.get('rationale') or []
            details = ""
            if rationale:
                details = f"<p><small>Why: {', '.join(rationale[:3])}</small></p>"
            node = upsert_sticky(dec.get('label', 'Decision'), details, color_for('decision'), x, y)
            id_to_item[dec.get('id', f'd{i}')] = node

        # Actions
        for i, act in enumerate(analysis_data.get('actions', [])[:6]):
            x = lane_x['actions']
            y = 100 + i * 220
            owner = act.get('owner') or 'TBD'
            due = act.get('due') or 'TBD'
            details = f"<p><small>Owner: {owner} · Due: {due}</small></p>"
            node = upsert_sticky(act.get('label', 'Action'), details, color_for('action'), x, y)
            id_to_item[act.get('id', f'a{i}')] = node

        # Relationships to connectors
        for rel in analysis_data.get('relationships', [])[:20]:
            src = id_to_item.get(rel.get('from'))
            dst = id_to_item.get(rel.get('to'))
            if not src or not dst:
                continue
            strength = rel.get('strength', 0.5)
            style = {
                "strokeColor": "#333333",
                "strokeWidth": 2 + int(2 * strength),
                "strokeStyle": "dashed" if strength < 0.5 else "normal"
            }
            try:
                connectors_created.append(self.create_connector(board_id, src['id'], dst['id'], style=style, caption=rel.get('type')))
            except Exception:
                pass

        # Summary / frame label
        summary = analysis_data.get('summary', {})
        blurb = summary.get('blurb') or ""
        frame_name = summary.get('frame_name') or "Conversation – Now"
        title_note = self.create_sticky_note(
            board_id,
            f"<p><strong>🎯 {frame_name}</strong></p><p>{blurb}</p>",
            {"x": -200, "y": -400},
            {"fillColor": "dark_blue", "textAlign": "left"}
        )
        items_created.append(title_note)

        return {
            "success": True,
            "board_id": board_id,
            "board_url": f"https://miro.com/app/board/{board_id}/",
            "embed_url": f"https://miro.com/app/embed/{board_id}/",
            "items_created": len(items_created),
            "connectors_created": len(connectors_created),
            "timestamp": time.time()
        }

    def update_item(self, board_id: str, item_id: str, payload: Dict) -> Dict:
        """Update a generic board item (used for upsert)."""
        if not self.access_token:
            raise Exception("Miro access token not configured")
        response = requests.patch(
            f"{self.base_url}/boards/{board_id}/items/{item_id}",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        if response.status_code not in (200, 201):
            raise Exception(f"Failed to update item: {response.text}")
        return response.json()

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
        """Analyze conversation using Gemini AI"""
        if not self.client:
            return {"error": "Gemini API key not configured"}
        
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
        """Get all items from a board"""
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
        """Clear all items from a board"""
        items = self.get_board_items(board_id)
        
        for item in items:
            item_id = item.get('id')
            if item_id:
                requests.delete(
                    f"{self.base_url}/boards/{board_id}/items/{item_id}",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    }
                )
    
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
    
    def create_diagram_from_analysis(self, board_id: str, analysis_data: Dict) -> Dict:
        """Create a Miro diagram from conversation analysis"""
        items_created = []
        
        # Add topics as sticky notes
        if "topics" in analysis_data:
            for i, topic in enumerate(analysis_data["topics"][:15]):  # Limit to top 15
                x = (i % 5) * 400  # 5 columns
                y = (i // 5) * 300  # rows
                
                content = f"<p><strong>{topic['name']}</strong></p><p>{topic.get('description', '')}</p>"
                position = {"x": x, "y": y}
                style = {
                    "fillColor": "light_yellow" if topic.get('importance', 0) > 0.7 else "light_blue",
                    "textAlign": "center",
                    "textAlignVertical": "top"
                }
                
                try:
                    sticky_note = self.create_sticky_note(board_id, content, position, style)
                    items_created.append(sticky_note)
                except Exception as e:
                    print(f"Failed to create topic sticky note: {e}")
        
        # Add action items as sticky notes (offset to the right)
        if "action_items" in analysis_data:
            action_start_x = 2500  # Start action items to the right
            for i, action in enumerate(analysis_data["action_items"][:10]):
                x = action_start_x + (i % 3) * 400
                y = (i // 3) * 300
                
                priority_color = "light_red" if action.get('priority') == 'high' else "light_green"
                content = f"<p><strong>Action:</strong> {action.get('task', '')}</p><p><strong>Assignee:</strong> {action.get('assignee', 'TBD')}</p>"
                position = {"x": x, "y": y}
                style = {
                    "fillColor": priority_color,
                    "textAlign": "center",
                    "textAlignVertical": "top"
                }
                
                try:
                    sticky_note = self.create_sticky_note(board_id, content, position, style)
                    items_created.append(sticky_note)
                except Exception as e:
                    print(f"Failed to create action sticky note: {e}")
        
        return {
            "success": True,
            "board_id": board_id,
            "board_url": f"https://miro.com/app/board/{board_id}/",
            "embed_url": f"https://miro.com/app/embed/{board_id}/",
            "items_created": len(items_created),
            "timestamp": time.time()
        }

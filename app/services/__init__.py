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
        """Create a comprehensive Miro diagram with arrows, flow, and useful visualizations"""
        items_created = []
        connectors_created = []
        
        # Create main title
        title = self.create_sticky_note(
            board_id,
            "<p><strong>🎯 MEETING ANALYSIS DASHBOARD</strong></p><p>Generated from conversation insights</p>",
            {"x": 0, "y": -400},
            {"fillColor": "dark_blue", "textAlign": "center", "textAlignVertical": "top"}
        )
        items_created.append(title)
        
        # Create section headers with visual separators
        sections = {
            'topics': {'x': 0, 'y': -200, 'title': '📋 KEY TOPICS', 'color': 'violet'},
            'decisions': {'x': 1500, 'y': -200, 'title': '✅ DECISIONS', 'color': 'light_green'},
            'actions': {'x': 3000, 'y': -200, 'title': '📝 ACTION ITEMS', 'color': 'orange'},
            'speakers': {'x': 4500, 'y': -200, 'title': '👥 PARTICIPANTS', 'color': 'light_blue'}
        }
        
        section_headers = {}
        for section_id, config in sections.items():
            header = self.create_sticky_note(
                board_id,
                f"<p><strong>{config['title']}</strong></p>",
                {"x": config['x'], "y": config['y']},
                {"fillColor": config['color'], "textAlign": "center", "textAlignVertical": "top"}
            )
            items_created.append(header)
            section_headers[section_id] = header
        
        # Create visual separators between sections
        separator_positions = [750, 2250, 3750]
        for i, x in enumerate(separator_positions):
            separator = self.create_shape(
                board_id,
                "rectangle",
                "",
                {"x": x, "y": -100, "width": 8, "height": 2000},
                {"fillColor": "#808080", "borderColor": "#808080"}
            )
            items_created.append(separator)
        
        # Add topics with importance-based sizing and positioning
        topic_items = []
        if "topics" in analysis_data:
            # Sort topics by importance
            sorted_topics = sorted(analysis_data["topics"][:12], 
                                key=lambda x: x.get('importance', 0), reverse=True)
            
            for i, topic in enumerate(sorted_topics):
                importance = topic.get('importance', 0)
                
                # Size based on importance
                size_multiplier = 1 + (importance * 0.5)  # 1.0 to 1.5x size
                
                x = (i % 3) * 500 + 100
                y = 100 + (i // 3) * 400
                
                # Color based on importance
                if importance > 0.8:
                    color = "red"
                    emoji = "🔥"
                elif importance > 0.6:
                    color = "light_yellow"
                    emoji = "⭐"
                else:
                    color = "light_blue"
                    emoji = "💡"
                
                content = f"<p><strong>{emoji} {topic['name']}</strong></p><p>{topic.get('description', '')}</p><p><small>Importance: {int(importance * 100)}%</small></p>"
                position = {"x": x, "y": y}
                style = {
                    "fillColor": color,
                    "textAlign": "center",
                    "textAlignVertical": "top"
                }
                
                try:
                    sticky_note = self.create_sticky_note(board_id, content, position, style)
                    items_created.append(sticky_note)
                    topic_items.append(sticky_note)
                except Exception as e:
                    print(f"Failed to create topic sticky note: {e}")
        
        # Add decisions with timeline flow
        decision_items = []
        if "decisions" in analysis_data:
            for i, decision in enumerate(analysis_data["decisions"][:8]):
                x = 1500 + (i % 2) * 600
                y = 100 + (i // 2) * 350
                
                # Add decision number for flow
                decision_num = i + 1
                content = f"<p><strong>✅ Decision #{decision_num}</strong></p><p><strong>{decision.get('title', 'Decision')}</strong></p><p>{decision.get('description', '')}</p>"
                position = {"x": x, "y": y}
                style = {
                    "fillColor": "light_green",
                    "textAlign": "center",
                    "textAlignVertical": "top"
                }
                
                try:
                    sticky_note = self.create_sticky_note(board_id, content, position, style)
                    items_created.append(sticky_note)
                    decision_items.append(sticky_note)
                except Exception as e:
                    print(f"Failed to create decision sticky note: {e}")
        
        # Add action items with priority clustering and visual indicators
        action_items = []
        if "action_items" in analysis_data:
            # Group by priority
            high_priority = [a for a in analysis_data["action_items"] if a.get('priority') == 'high']
            medium_priority = [a for a in analysis_data["action_items"] if a.get('priority') == 'medium']
            low_priority = [a for a in analysis_data["action_items"] if a.get('priority') == 'low']
            
            priority_groups = [
                (high_priority, "🔴 HIGH PRIORITY", "red", 3000),
                (medium_priority, "🟡 MEDIUM PRIORITY", "light_yellow", 3000),
                (low_priority, "🟢 LOW PRIORITY", "light_green", 3000)
            ]
            
            for group_items, group_title, group_color, start_x in priority_groups:
                if not group_items:
                    continue
                
                # Add priority group header
                group_header = self.create_sticky_note(
                    board_id,
                    f"<p><strong>{group_title}</strong></p>",
                    {"x": start_x, "y": 50},
                    {"fillColor": group_color, "textAlign": "center"}
                )
                items_created.append(group_header)
                
                # Add items in this priority group
                for i, action in enumerate(group_items[:4]):  # Max 4 per group
                    x = start_x + (i % 2) * 500
                    y = 200 + (i // 2) * 300
                    
                    assignee = action.get('assignee', 'TBD')
                    due_date = action.get('due_date', 'TBD')
                    
                    content = f"<p><strong>📋 {action.get('task', '')}</strong></p><p><strong>👤 Assignee:</strong> {assignee}</p><p><strong>📅 Due:</strong> {due_date}</p>"
                    position = {"x": x, "y": y}
                    style = {
                        "fillColor": group_color,
                        "textAlign": "center",
                        "textAlignVertical": "top"
                    }
                    
                    try:
                        sticky_note = self.create_sticky_note(board_id, content, position, style)
                        items_created.append(sticky_note)
                        action_items.append(sticky_note)
                    except Exception as e:
                        print(f"Failed to create action sticky note: {e}")
        
        # Add speaker participation visualization
        speaker_items = []
        if "speakers" in analysis_data:
            # Sort by engagement level
            sorted_speakers = sorted(analysis_data["speakers"], 
                                   key=lambda x: x.get('engagement', 0), reverse=True)
            
            for i, speaker in enumerate(sorted_speakers[:6]):
                engagement = speaker.get('engagement', 0)
                role = speaker.get('role', 'Participant')
                
                # Visual representation of engagement
                engagement_bars = "█" * int(engagement * 10) + "░" * (10 - int(engagement * 10))
                
                x = 4500 + (i % 2) * 400
                y = 100 + (i // 2) * 300
                
                content = f"<p><strong>👤 {speaker['name']}</strong></p><p><strong>Role:</strong> {role}</p><p><strong>Engagement:</strong> {int(engagement * 100)}%</p><p><small>{engagement_bars}</small></p>"
                position = {"x": x, "y": y}
                
                # Color based on engagement
                if engagement > 0.8:
                    color = "light_green"
                elif engagement > 0.5:
                    color = "light_yellow"
                else:
                    color = "gray"
                
                style = {
                    "fillColor": color,
                    "textAlign": "center",
                    "textAlignVertical": "top"
                }
                
                try:
                    sticky_note = self.create_sticky_note(board_id, content, position, style)
                    items_created.append(sticky_note)
                    speaker_items.append(sticky_note)
                except Exception as e:
                    print(f"Failed to create speaker sticky note: {e}")
        
        # Create flow arrows and connections
        try:
            # Connect topics to decisions (showing logical flow)
            if topic_items and decision_items:
                for i in range(min(3, len(topic_items), len(decision_items))):
                    connector = self.create_connector(
                        board_id,
                        topic_items[i]['id'],
                        decision_items[i]['id'],
                        style={"strokeColor": "#007bff", "strokeWidth": 3, "strokeStyle": "normal"},
                        caption="leads to"
                    )
                    connectors_created.append(connector)
            
            # Connect decisions to action items
            if decision_items and action_items:
                for i in range(min(2, len(decision_items), len(action_items))):
                    connector = self.create_connector(
                        board_id,
                        decision_items[i]['id'],
                        action_items[i]['id'],
                        style={"strokeColor": "#28a745", "strokeWidth": 3, "strokeStyle": "normal"},
                        caption="requires"
                    )
                    connectors_created.append(connector)
            
            # Connect section headers to their content
            for section_id, header in section_headers.items():
                target_items = []
                if section_id == 'topics' and topic_items:
                    target_items = topic_items[:1]
                elif section_id == 'decisions' and decision_items:
                    target_items = decision_items[:1]
                elif section_id == 'actions' and action_items:
                    target_items = action_items[:1]
                elif section_id == 'speakers' and speaker_items:
                    target_items = speaker_items[:1]
                
                if target_items:
                    connector = self.create_connector(
                        board_id,
                        header['id'],
                        target_items[0]['id'],
                        style={"strokeColor": "#6c757d", "strokeWidth": 2, "strokeStyle": "dashed"}
                    )
                    connectors_created.append(connector)
            
            # Create a main flow arrow from topics → decisions → actions
            if topic_items and decision_items and action_items:
                # Create a curved flow line
                flow_connector = self.create_connector(
                    board_id,
                    topic_items[0]['id'],
                    action_items[0]['id'],
                    style={"strokeColor": "#dc3545", "strokeWidth": 4, "strokeStyle": "curved"},
                    caption="Meeting Flow"
                )
                connectors_created.append(flow_connector)
                
        except Exception as e:
            print(f"Failed to create connectors: {e}")
        
        # Add summary statistics box
        total_topics = len(analysis_data.get("topics", []))
        total_decisions = len(analysis_data.get("decisions", []))
        total_actions = len(analysis_data.get("action_items", []))
        total_speakers = len(analysis_data.get("speakers", []))
        
        summary = self.create_sticky_note(
            board_id,
            f"<p><strong>📊 MEETING SUMMARY</strong></p><p>Topics: {total_topics}</p><p>Decisions: {total_decisions}</p><p>Actions: {total_actions}</p><p>Speakers: {total_speakers}</p>",
            {"x": 0, "y": 2000},
            {"fillColor": "gray", "textAlign": "center", "textAlignVertical": "top"}
        )
        items_created.append(summary)
        
        return {
            "success": True,
            "board_id": board_id,
            "board_url": f"https://miro.com/app/board/{board_id}/",
            "embed_url": f"https://miro.com/app/embed/{board_id}/",
            "items_created": len(items_created),
            "connectors_created": len(connectors_created),
            "visualization_features": [
                "Section headers with visual separators",
                "Importance-based topic sizing and coloring",
                "Priority-clustered action items",
                "Speaker engagement visualization",
                "Flow arrows showing logical progression",
                "Meeting summary statistics"
            ],
            "timestamp": time.time()
        }

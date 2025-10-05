"""
Data models for the application
"""
from typing import Dict, List, Optional
from collections import deque
import threading
import time

class ConversationBuffer:
    """Manages conversation transcripts for analysis"""
    
    def __init__(self, max_size: int = 50):
        self.buffer = deque(maxlen=max_size)
        self.lock = threading.Lock()
    
    def add_transcript(self, transcript_data: Dict) -> None:
        """Add a transcript entry to the buffer"""
        with self.lock:
            self.buffer.append({
                'timestamp': transcript_data.get('timestamp_ms', 0),
                'speaker': transcript_data.get('speaker_name', 'Unknown'),
                'text': transcript_data.get('transcription', {}).get('transcript', ''),
                'confidence': transcript_data.get('transcription', {}).get('confidence', 0)
            })
    
    def get_conversation_text(self) -> str:
        """Get formatted conversation text for analysis"""
        with self.lock:
            return "\n".join([
                f"[{entry['speaker']}]: {entry['text']}" 
                for entry in self.buffer
            ])
    
    def get_buffer_data(self) -> List[Dict]:
        """Get a copy of the buffer data"""
        with self.lock:
            return list(self.buffer)
    
    def get_speakers(self) -> List[str]:
        """Get unique speakers from the buffer"""
        with self.lock:
            return list(set(entry['speaker'] for entry in self.buffer))
    
    def is_empty(self) -> bool:
        """Check if buffer is empty"""
        with self.lock:
            return len(self.buffer) == 0

class BotSession:
    """Represents a bot session with its conversation buffer"""
    
    def __init__(self, bot_id: str):
        self.bot_id = bot_id
        self.conversation_buffer = ConversationBuffer()
        self.created_at = time.time()
        self.last_activity = time.time()
    
    def update_activity(self) -> None:
        """Update the last activity timestamp"""
        self.last_activity = time.time()

class AnalysisResult:
    """Represents the result of conversation analysis"""
    
    def __init__(self, bot_id: str, analysis_data: Dict):
        self.bot_id = bot_id
        self.timestamp = time.time()
        self.topics = analysis_data.get('topics', [])
        self.decisions = analysis_data.get('decisions', [])
        self.action_items = analysis_data.get('action_items', [])
        self.speakers = analysis_data.get('speakers', [])
        self.relationships = analysis_data.get('relationships', [])
        self.timeline = analysis_data.get('timeline', [])
        self.error = analysis_data.get('error')
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'bot_id': self.bot_id,
            'timestamp': self.timestamp,
            'topics': self.topics,
            'decisions': self.decisions,
            'action_items': self.action_items,
            'speakers': self.speakers,
            'relationships': self.relationships,
            'timeline': self.timeline,
            'error': self.error
        }

"""
AudioAgent - Text-to-Speech conversion for NewsNexus articles
Converts daily intelligence brief into an MP3 audio file using gTTS (Google Translate TTS)
"""

import os
from datetime import date
from gtts import gTTS


class AudioAgent:
    """
    Simple audio generation agent.
    One job: Convert articles to MP3. No overengineering.
    Uses gTTS - free, no API key needed.
    """
    
    def __init__(self, db_conn):
        """
        Initialize AudioAgent with database connection.
        
        Args:
            db_conn: SQLite database connection
        """
        self.conn = db_conn
    
    def run(self, session_id: int, articles: list[dict]) -> str | None:
        """
        Main entry point. Generate audio for session articles.
        
        Args:
            session_id: Session ID
            articles: List of article dictionaries
            
        Returns:
            str: Path to generated MP3 file, or None on failure
        """
        try:
            script = self._build_script(articles)
            path = self._synthesise(script, session_id)
            self._save_audio_path(session_id, path)
            print(f"[AudioAgent] Audio saved: {path}")
            return path
        except Exception as e:
            print(f"[AudioAgent] Failed: {e}")
            return None
    
    def _build_script(self, articles: list[dict]) -> str:
        """
        Build plain reading script from articles.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            str: Plain text script for TTS
        """
        # Get date info
        today = date.today()
        weekday = today.strftime("%A")
        date_str = today.strftime("%B %d, %Y")
        
        # Start script
        script = f"NewsNexus Intelligence Brief. {weekday}, {date_str}.\n"
        script += f"Today's brief covers {len(articles)} articles.\n\n"
        
        # Add each article
        for i, article in enumerate(articles, 1):
            article_text = f"Article {i}. {article.get('category', 'General')}. {article.get('title', 'Untitled')}.\n"
            article_text += f"Exam Angle. {article.get('exam_angle', 'Not specified')}.\n"
            
            # Add key points if available
            key_points = article.get('key_points', '')
            if key_points:
                article_text += f"Key Points. {key_points}.\n"
            
            article_text += f"Prelims importance: {article.get('prelims_score', 0)} out of 10.\n"
            article_text += f"Mains importance: {article.get('mains_score', 0)} out of 10.\n\n"
            
            script += article_text
        
        # Clean the script
        script = self._clean_script(script)
        
        # Truncate if too long (gTTS has limits)
        if len(script) > 5000:
            script = script[:4997] + "..."
        
        return script
    
    def _clean_script(self, text: str) -> str:
        """
        Clean script for TTS - simple string replacements.
        
        Args:
            text: Raw script text
            
        Returns:
            str: Cleaned script
        """
        # Simple replacements
        text = text.replace("&", "and")
        text = text.replace("%", "percent")
        text = text.replace("/", " or ")
        text = text.replace("*", "")
        text = text.replace("#", "")
        text = text.replace("•", "")
        text = text.replace("·", "")
        text = text.replace("–", "-")
        text = text.replace("—", "-")
        
        # Remove extra whitespace
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        # Remove multiple spaces
        while "  " in text:
            text = text.replace("  ", " ")
        
        return text
    
    def _synthesise(self, script: str, session_id: int) -> str:
        """
        Convert script to MP3 using gTTS.
        
        Args:
            script: Plain text script
            session_id: Session ID for filename
            
        Returns:
            str: Path to generated MP3 file
        """
        # Create audio directory
        os.makedirs("audio", exist_ok=True)
        output_path = f"audio/session_{session_id}_{date.today()}.mp3"
        
        # Generate audio using gTTS
        # Using Indian English accent, slow=False for normal speed
        tts = gTTS(text=script, lang='en', tld='co.in', slow=False)
        tts.save(output_path)
        
        return output_path
    
    def _save_audio_path(self, session_id: int, path: str):
        """
        Save audio path to database.
        
        Args:
            session_id: Session ID
            path: Path to audio file
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE sessions SET audio_path = ? WHERE id = ?",
            (path, session_id)
        )
        self.conn.commit()


if __name__ == "__main__":
    # Test script
    import sqlite3
    from src.utils.database import get_connection, init_db
    
    conn = get_connection()
    init_db(conn)
    
    # Test articles
    test_articles = [
        {
            'title': 'India Launches New Digital Public Infrastructure',
            'category': 'Science & Tech',
            'exam_angle': 'Important for understanding digital governance initiatives',
            'key_points': 'DPI for healthcare, Ayushman Bharat integration, telemedicine in rural areas',
            'prelims_score': 8,
            'mains_score': 7
        },
        {
            'title': 'Economic Growth Projections Revised',
            'category': 'Economy',
            'exam_angle': 'Relevant for economic development questions',
            'key_points': 'GDP growth at 6.5%, inflation concerns, fiscal policy changes',
            'prelims_score': 9,
            'mains_score': 9
        }
    ]
    
    agent = AudioAgent(conn)
    script = agent._build_script(test_articles)
    print("Generated Script:")
    print("=" * 60)
    print(script)
    print("=" * 60)
    print(f"Script length: {len(script)} characters")
    
    # Test audio generation
    print("\nGenerating audio...")
    path = agent.run(1, test_articles)
    if path:
        print(f"Audio generated successfully: {path}")
    else:
        print("Audio generation failed")
    
    conn.close()

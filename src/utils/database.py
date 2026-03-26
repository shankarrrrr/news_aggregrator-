"""
NewsNexus Database Module
SQLite database schema and CRUD operations for UPSC news intelligence app
"""

import sqlite3
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any


def get_connection(db_path: str = "newsnexus.db") -> sqlite3.Connection:
    """
    Get a connection to the NewsNexus database.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        sqlite3.Connection: Database connection
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """
    Initialize the database by creating all tables if they don't exist.
    
    Args:
        conn: SQLite database connection
    """
    cursor = conn.cursor()
    
    # Create sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_date DATE NOT NULL,
            email_sent_at DATETIME,
            dashboard_token TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            CHECK (status IN ('pending', 'ready', 'completed'))
        )
    """)
    
    # Create articles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            source TEXT NOT NULL,
            category TEXT NOT NULL,
            summary TEXT,
            exec_summary TEXT,
            exam_angle TEXT,
            key_points TEXT,
            prelims_score INTEGER CHECK (prelims_score BETWEEN 1 AND 10),
            mains_score INTEGER CHECK (mains_score BETWEEN 1 AND 10),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
            CHECK (source IN ('PIB', 'The Hindu', 'Indian Express')),
            CHECK (category IN ('Economy', 'Security & Defence', 'Science & Tech', 'Environment', 
                               'Polity', 'International Relations', 'History & Culture', 'Social Issues'))
        )
    """)
    
    # Create mcqs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mcqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            session_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_option TEXT NOT NULL,
            explanation TEXT,
            difficulty TEXT NOT NULL DEFAULT 'medium',
            gs_paper TEXT,
            learning_insight TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
            CHECK (correct_option IN ('A', 'B', 'C', 'D')),
            CHECK (difficulty IN ('easy', 'medium', 'hard'))
        )
    """)
    
    # Create user_attempts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            article_id INTEGER NOT NULL,
            mcq_id INTEGER NOT NULL,
            selected_option TEXT NOT NULL,
            is_correct BOOLEAN NOT NULL,
            time_taken_seconds INTEGER,
            attempted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
            FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
            FOREIGN KEY (mcq_id) REFERENCES mcqs(id) ON DELETE CASCADE,
            CHECK (selected_option IN ('A', 'B', 'C', 'D'))
        )
    """)
    
    # Create user_performance table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT UNIQUE NOT NULL,
            total_attempted INTEGER DEFAULT 0,
            total_correct INTEGER DEFAULT 0,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create feedback_profile table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            priority_categories TEXT,
            deprioritise_categories TEXT,
            suggested_difficulty TEXT,
            focus_note TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
            CHECK (suggested_difficulty IN ('easy', 'medium', 'hard', NULL))
        )
    """)
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create user_interests table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_interests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, category)
        )
    """)
    
    # Create user_sessions table (tracks which users accessed which sessions)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id INTEGER NOT NULL,
            accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        )
    """)
    
    # Create indexes for better query performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(dashboard_token)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_session ON articles(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mcqs_article ON mcqs(article_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mcqs_session ON mcqs(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attempts_session ON user_attempts(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attempts_mcq ON user_attempts(mcq_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_session ON feedback_profile(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_interests_user ON user_interests(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_sessions_session ON user_sessions(session_id)")
    
    conn.commit()


# ==================== SESSIONS ====================

def insert_session(conn: sqlite3.Connection, session_date: str, status: str = 'pending') -> int:
    """
    Insert a new session.
    
    Args:
        conn: Database connection
        session_date: Date of the session (YYYY-MM-DD)
        status: Session status (default: 'pending')
        
    Returns:
        int: ID of the inserted session
    """
    cursor = conn.cursor()
    dashboard_token = str(uuid.uuid4())
    
    cursor.execute("""
        INSERT INTO sessions (session_date, dashboard_token, status)
        VALUES (?, ?, ?)
    """, (session_date, dashboard_token, status))
    
    conn.commit()
    return cursor.lastrowid


def get_session_by_token(conn: sqlite3.Connection, token: str) -> Optional[Dict[str, Any]]:
    """
    Get session by dashboard token.
    
    Args:
        conn: Database connection
        token: Dashboard token (UUID)
        
    Returns:
        Dict or None: Session data
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE dashboard_token = ?", (token,))
    row = cursor.fetchone()
    return dict(row) if row else None


def get_session_by_id(conn: sqlite3.Connection, session_id: int) -> Optional[Dict[str, Any]]:
    """
    Get session by ID.
    
    Args:
        conn: Database connection
        session_id: Session ID
        
    Returns:
        Dict or None: Session data
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def update_session_status(conn: sqlite3.Connection, session_id: int, status: str) -> None:
    """
    Update session status.
    
    Args:
        conn: Database connection
        session_id: Session ID
        status: New status ('pending', 'ready', 'completed')
    """
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE sessions 
        SET status = ?, email_sent_at = CASE WHEN ? = 'ready' THEN CURRENT_TIMESTAMP ELSE email_sent_at END
        WHERE id = ?
    """, (status, status, session_id))
    conn.commit()


def get_all_sessions(conn: sqlite3.Connection, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get all sessions ordered by date descending.
    
    Args:
        conn: Database connection
        limit: Maximum number of sessions to return
        
    Returns:
        List of session dictionaries
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions ORDER BY session_date DESC LIMIT ?", (limit,))
    return [dict(row) for row in cursor.fetchall()]


# ==================== ARTICLES ====================

def insert_article(conn: sqlite3.Connection, session_id: int, title: str, source: str, 
                  category: str, summary: str = None, exec_summary: str = None,
                  exam_angle: str = None, key_points: str = None, 
                  prelims_score: int = None, mains_score: int = None) -> int:
    """
    Insert a new article.
    
    Args:
        conn: Database connection
        session_id: Session ID
        title: Article title
        source: Article source
        category: Article category
        summary: Article summary
        exec_summary: Executive summary
        exam_angle: Exam angle
        key_points: Key points (JSON or comma-separated)
        prelims_score: Prelims relevance score (1-10)
        mains_score: Mains relevance score (1-10)
        
    Returns:
        int: ID of the inserted article
    """
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO articles (session_id, title, source, category, summary, exec_summary, 
                            exam_angle, key_points, prelims_score, mains_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (session_id, title, source, category, summary, exec_summary, 
          exam_angle, key_points, prelims_score, mains_score))
    
    conn.commit()
    return cursor.lastrowid


def get_articles_by_session(conn: sqlite3.Connection, session_id: int) -> List[Dict[str, Any]]:
    """
    Get all articles for a session.
    
    Args:
        conn: Database connection
        session_id: Session ID
        
    Returns:
        List of article dictionaries
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM articles 
        WHERE session_id = ? 
        ORDER BY prelims_score DESC, mains_score DESC
    """, (session_id,))
    return [dict(row) for row in cursor.fetchall()]


def get_article_by_id(conn: sqlite3.Connection, article_id: int) -> Optional[Dict[str, Any]]:
    """
    Get article by ID.
    
    Args:
        conn: Database connection
        article_id: Article ID
        
    Returns:
        Dict or None: Article data
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


# ==================== MCQs ====================

def insert_mcq(conn: sqlite3.Connection, article_id: int, session_id: int, question: str,
              option_a: str, option_b: str, option_c: str, option_d: str,
              correct_option: str, explanation: str = None, difficulty: str = 'medium',
              gs_paper: str = None, learning_insight: str = None) -> int:
    """
    Insert a new MCQ.
    
    Args:
        conn: Database connection
        article_id: Article ID
        session_id: Session ID
        question: Question text
        option_a, option_b, option_c, option_d: Answer options
        correct_option: Correct option ('A', 'B', 'C', 'D')
        explanation: Explanation for the answer
        difficulty: Question difficulty ('easy', 'medium', 'hard')
        gs_paper: GS Paper mapping (e.g., 'GS Paper 2', 'GS Paper 3')
        learning_insight: Key learning insight from this question
        
    Returns:
        int: ID of the inserted MCQ
    """
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO mcqs (article_id, session_id, question, option_a, option_b, option_c, 
                         option_d, correct_option, explanation, difficulty, gs_paper, learning_insight)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (article_id, session_id, question, option_a, option_b, option_c, 
          option_d, correct_option, explanation, difficulty, gs_paper, learning_insight))
    
    conn.commit()
    return cursor.lastrowid


def get_mcqs_by_article(conn: sqlite3.Connection, article_id: int) -> List[Dict[str, Any]]:
    """
    Get all MCQs for an article.
    
    Args:
        conn: Database connection
        article_id: Article ID
        
    Returns:
        List of MCQ dictionaries
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mcqs WHERE article_id = ? ORDER BY created_at", (article_id,))
    return [dict(row) for row in cursor.fetchall()]


def get_mcqs_by_session(conn: sqlite3.Connection, session_id: int) -> List[Dict[str, Any]]:
    """
    Get all MCQs for a session.
    
    Args:
        conn: Database connection
        session_id: Session ID
        
    Returns:
        List of MCQ dictionaries
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mcqs WHERE session_id = ? ORDER BY created_at", (session_id,))
    return [dict(row) for row in cursor.fetchall()]


def get_mcq_by_id(conn: sqlite3.Connection, mcq_id: int) -> Optional[Dict[str, Any]]:
    """
    Get MCQ by ID.
    
    Args:
        conn: Database connection
        mcq_id: MCQ ID
        
    Returns:
        Dict or None: MCQ data
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mcqs WHERE id = ?", (mcq_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


# ==================== USER ATTEMPTS ====================

def insert_attempt(conn: sqlite3.Connection, session_id: int, article_id: int, mcq_id: int,
                  selected_option: str, is_correct: bool, time_taken_seconds: int = None) -> int:
    """
    Insert a user attempt.
    
    Args:
        conn: Database connection
        session_id: Session ID
        article_id: Article ID
        mcq_id: MCQ ID
        selected_option: Selected option ('A', 'B', 'C', 'D')
        is_correct: Whether the answer was correct
        time_taken_seconds: Time taken to answer
        
    Returns:
        int: ID of the inserted attempt
    """
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_attempts (session_id, article_id, mcq_id, selected_option, 
                                  is_correct, time_taken_seconds)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (session_id, article_id, mcq_id, selected_option, is_correct, time_taken_seconds))
    
    conn.commit()
    return cursor.lastrowid


def get_attempts_by_session(conn: sqlite3.Connection, session_id: int) -> List[Dict[str, Any]]:
    """
    Get all attempts for a session.
    
    Args:
        conn: Database connection
        session_id: Session ID
        
    Returns:
        List of attempt dictionaries
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM user_attempts 
        WHERE session_id = ? 
        ORDER BY attempted_at
    """, (session_id,))
    return [dict(row) for row in cursor.fetchall()]


def get_attempts_by_mcq(conn: sqlite3.Connection, mcq_id: int) -> List[Dict[str, Any]]:
    """
    Get all attempts for a specific MCQ.
    
    Args:
        conn: Database connection
        mcq_id: MCQ ID
        
    Returns:
        List of attempt dictionaries
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM user_attempts 
        WHERE mcq_id = ? 
        ORDER BY attempted_at
    """, (mcq_id,))
    return [dict(row) for row in cursor.fetchall()]


# ==================== USER PERFORMANCE ====================

def upsert_user_performance(conn: sqlite3.Connection, category: str, 
                           attempted: int = 1, correct: int = 0) -> None:
    """
    Insert or update user performance for a category.
    
    Args:
        conn: Database connection
        category: Category name
        attempted: Number of questions attempted (default: 1)
        correct: Number of correct answers (default: 0)
    """
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_performance (category, total_attempted, total_correct, last_updated)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(category) DO UPDATE SET
            total_attempted = total_attempted + ?,
            total_correct = total_correct + ?,
            last_updated = CURRENT_TIMESTAMP
    """, (category, attempted, correct, attempted, correct))
    
    conn.commit()


def get_all_performance(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """
    Get performance statistics for all categories.
    
    Args:
        conn: Database connection
        
    Returns:
        List of performance dictionaries
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT *, 
               CASE WHEN total_attempted > 0 
                    THEN ROUND(CAST(total_correct AS FLOAT) / total_attempted * 100, 2)
                    ELSE 0 
               END as accuracy_percentage
        FROM user_performance 
        ORDER BY total_attempted DESC
    """)
    return [dict(row) for row in cursor.fetchall()]


def get_performance_by_category(conn: sqlite3.Connection, category: str) -> Optional[Dict[str, Any]]:
    """
    Get performance statistics for a specific category.
    
    Args:
        conn: Database connection
        category: Category name
        
    Returns:
        Dict or None: Performance data
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT *, 
               CASE WHEN total_attempted > 0 
                    THEN ROUND(CAST(total_correct AS FLOAT) / total_attempted * 100, 2)
                    ELSE 0 
               END as accuracy_percentage
        FROM user_performance 
        WHERE category = ?
    """, (category,))
    row = cursor.fetchone()
    return dict(row) if row else None


# ==================== FEEDBACK PROFILE ====================

def insert_feedback_profile(conn: sqlite3.Connection, session_id: int, 
                           priority_categories: str = None, deprioritise_categories: str = None,
                           suggested_difficulty: str = None, focus_note: str = None) -> int:
    """
    Insert a feedback profile.
    
    Args:
        conn: Database connection
        session_id: Session ID
        priority_categories: Comma-separated priority categories
        deprioritise_categories: Comma-separated categories to deprioritize
        suggested_difficulty: Suggested difficulty level
        focus_note: Additional focus notes
        
    Returns:
        int: ID of the inserted feedback profile
    """
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO feedback_profile (session_id, priority_categories, deprioritise_categories,
                                     suggested_difficulty, focus_note)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, priority_categories, deprioritise_categories, suggested_difficulty, focus_note))
    
    conn.commit()
    return cursor.lastrowid


def get_latest_feedback_profile(conn: sqlite3.Connection) -> Optional[Dict[str, Any]]:
    """
    Get the most recent feedback profile.
    
    Args:
        conn: Database connection
        
    Returns:
        Dict or None: Feedback profile data
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM feedback_profile 
        ORDER BY created_at DESC 
        LIMIT 1
    """)
    row = cursor.fetchone()
    return dict(row) if row else None


def get_feedback_by_session(conn: sqlite3.Connection, session_id: int) -> Optional[Dict[str, Any]]:
    """
    Get feedback profile for a specific session.
    
    Args:
        conn: Database connection
        session_id: Session ID
        
    Returns:
        Dict or None: Feedback profile data
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM feedback_profile 
        WHERE session_id = ? 
        ORDER BY created_at DESC 
        LIMIT 1
    """, (session_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


# ==================== UTILITY FUNCTIONS ====================

def get_session_stats(conn: sqlite3.Connection, session_id: int) -> Dict[str, Any]:
    """
    Get comprehensive statistics for a session.
    
    Args:
        conn: Database connection
        session_id: Session ID
        
    Returns:
        Dict: Session statistics including article count, MCQ count, attempt stats
    """
    cursor = conn.cursor()
    
    # Get article count
    cursor.execute("SELECT COUNT(*) as count FROM articles WHERE session_id = ?", (session_id,))
    article_count = cursor.fetchone()['count']
    
    # Get MCQ count
    cursor.execute("SELECT COUNT(*) as count FROM mcqs WHERE session_id = ?", (session_id,))
    mcq_count = cursor.fetchone()['count']
    
    # Get attempt stats
    cursor.execute("""
        SELECT 
            COUNT(*) as total_attempts,
            SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_attempts,
            AVG(time_taken_seconds) as avg_time_seconds
        FROM user_attempts 
        WHERE session_id = ?
    """, (session_id,))
    attempt_stats = dict(cursor.fetchone())
    
    return {
        'session_id': session_id,
        'article_count': article_count,
        'mcq_count': mcq_count,
        'total_attempts': attempt_stats['total_attempts'] or 0,
        'correct_attempts': attempt_stats['correct_attempts'] or 0,
        'avg_time_seconds': attempt_stats['avg_time_seconds'] or 0,
        'accuracy': round((attempt_stats['correct_attempts'] or 0) / max(attempt_stats['total_attempts'] or 1, 1) * 100, 2)
    }


# ==================== USERS ====================

def insert_user(conn: sqlite3.Connection, email: str, password_hash: str, name: str = None) -> int:
    """
    Insert a new user.
    
    Args:
        conn: Database connection
        email: User email
        password_hash: Hashed password
        name: User name (optional)
        
    Returns:
        int: ID of the inserted user
    """
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (email, password_hash, name)
        VALUES (?, ?, ?)
    """, (email, password_hash, name))
    
    conn.commit()
    return cursor.lastrowid


def get_user_by_email(conn: sqlite3.Connection, email: str) -> Optional[Dict[str, Any]]:
    """
    Get user by email.
    
    Args:
        conn: Database connection
        email: User email
        
    Returns:
        Dict or None: User data
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    return dict(row) if row else None


def get_user_by_id(conn: sqlite3.Connection, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Get user by ID.
    
    Args:
        conn: Database connection
        user_id: User ID
        
    Returns:
        Dict or None: User data
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


# ==================== USER INTERESTS ====================

def insert_user_interest(conn: sqlite3.Connection, user_id: int, category: str) -> int:
    """
    Insert a user interest.
    
    Args:
        conn: Database connection
        user_id: User ID
        category: Interest category
        
    Returns:
        int: ID of the inserted interest
    """
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO user_interests (user_id, category)
        VALUES (?, ?)
    """, (user_id, category))
    
    conn.commit()
    return cursor.lastrowid


def get_user_interests(conn: sqlite3.Connection, user_id: int) -> List[str]:
    """
    Get all interests for a user.
    
    Args:
        conn: Database connection
        user_id: User ID
        
    Returns:
        List of category names
    """
    cursor = conn.cursor()
    cursor.execute("SELECT category FROM user_interests WHERE user_id = ?", (user_id,))
    return [row['category'] for row in cursor.fetchall()]


def delete_user_interests(conn: sqlite3.Connection, user_id: int) -> None:
    """
    Delete all interests for a user.
    
    Args:
        conn: Database connection
        user_id: User ID
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_interests WHERE user_id = ?", (user_id,))
    conn.commit()


def set_user_interests(conn: sqlite3.Connection, user_id: int, categories: List[str]) -> None:
    """
    Set user interests (replaces existing).
    
    Args:
        conn: Database connection
        user_id: User ID
        categories: List of category names
    """
    delete_user_interests(conn, user_id)
    for category in categories:
        insert_user_interest(conn, user_id, category)


# ==================== USER SESSIONS ====================

def track_user_session_access(conn: sqlite3.Connection, user_id: int, session_id: int) -> int:
    """
    Track that a user accessed a session.
    
    Args:
        conn: Database connection
        user_id: User ID
        session_id: Session ID
        
    Returns:
        int: ID of the inserted record
    """
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_sessions (user_id, session_id)
        VALUES (?, ?)
    """, (user_id, session_id))
    
    conn.commit()
    return cursor.lastrowid


def get_latest_session_for_user(conn: sqlite3.Connection, user_id: int = None) -> Optional[Dict[str, Any]]:
    """
    Get the latest session (optionally for a specific user).
    
    Args:
        conn: Database connection
        user_id: User ID (optional, if None returns latest global session)
        
    Returns:
        Dict or None: Session data
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM sessions 
        WHERE status = 'ready'
        ORDER BY session_date DESC, created_at DESC
        LIMIT 1
    """)
    row = cursor.fetchone()
    return dict(row) if row else None


# ==================== AUDIO FUNCTIONS ====================

def save_audio_path(conn: sqlite3.Connection, session_id: int, path: str) -> None:
    """
    Save audio file path to session.
    
    Args:
        conn: Database connection
        session_id: Session ID
        path: Path to audio file
    """
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE sessions SET audio_path = ? WHERE id = ?",
        (path, session_id)
    )
    conn.commit()


def get_audio_path(conn: sqlite3.Connection, session_id: int) -> Optional[str]:
    """
    Get audio file path for a session.
    
    Args:
        conn: Database connection
        session_id: Session ID
        
    Returns:
        str or None: Path to audio file
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT audio_path FROM sessions WHERE id = ?",
        (session_id,)
    )
    row = cursor.fetchone()
    return row['audio_path'] if row else None


if __name__ == "__main__":
    # Example usage and testing
    import sys
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    conn = get_connection()
    init_db(conn)
    
    print("Database initialized successfully")
    print("Tables created: sessions, articles, mcqs, user_attempts, user_performance, feedback_profile")
    
    # Test insert session
    session_id = insert_session(conn, "2026-03-27")
    print(f"Test session created with ID: {session_id}")
    
    # Get session
    session = get_session_by_id(conn, session_id)
    print(f"Session token: {session['dashboard_token']}")
    
    conn.close()
    print("Database connection closed")

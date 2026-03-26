"""
NewsNexus API - Production Ready
Integrated pipeline with background job processing
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from collections import Counter
from jose import JWTError, jwt
from passlib.context import CryptContext
import os

from src.utils.database import (
    get_connection, init_db,
    get_session_by_token, get_articles_by_session, get_article_by_id,
    get_mcqs_by_article, get_mcq_by_id,
    insert_attempt, get_attempts_by_session, get_attempts_by_mcq,
    upsert_user_performance, get_all_performance,
    get_latest_feedback_profile, update_session_status,
    insert_session, insert_article, insert_mcq, get_all_sessions,
    insert_user, get_user_by_email, get_user_by_id,
    get_user_interests, set_user_interests,
    track_user_session_access, get_latest_session_for_user,
    save_audio_path, get_audio_path
)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-please")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer()

# Agent trace storage (in-memory for now)
agent_traces = {}

# Initialize FastAPI app
app = FastAPI(
    title="NewsNexus API",
    description="UPSC Intelligence Dashboard Backend - Production Ready",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== PYDANTIC MODELS ====================

# Auth Models
class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    created_at: str


class InterestsRequest(BaseModel):
    categories: List[str]


class InterestsResponse(BaseModel):
    categories: List[str]


# Existing Models
class ArticleResponse(BaseModel):
    id: int
    title: str
    source: str
    category: str
    prelims_score: int
    mains_score: int
    attempted: bool
    is_correct: Optional[bool] = None


class SessionResponse(BaseModel):
    session_date: str
    status: str
    coverage_summary: Dict[str, int]
    focus_note: Optional[str] = None
    articles: List[ArticleResponse]


class PendingSessionResponse(BaseModel):
    status: str
    message: str


class MCQResponse(BaseModel):
    id: int
    question: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    gs_paper: Optional[str] = None
    learning_insight: Optional[str] = None


class AttemptRequest(BaseModel):
    article_id: int
    mcq_id: int
    selected_option: str = Field(..., pattern="^[A-D]$")
    time_taken_seconds: int = Field(..., ge=0)


class AttemptResponse(BaseModel):
    is_correct: bool
    correct_option: str
    explanation: str
    gs_paper: Optional[str] = None
    learning_insight: Optional[str] = None


class QuestionResult(BaseModel):
    article_title: str
    category: str
    source: str
    selected_option: str
    correct_option: str
    is_correct: bool
    time_taken_seconds: int
    gs_paper: Optional[str] = None


class ResultsResponse(BaseModel):
    total_questions: int
    total_correct: int
    score_percent: float
    time_taken_total: int
    per_question: List[QuestionResult]
    weak_topics: List[str]


class PerformanceItem(BaseModel):
    category: str
    total_attempted: int
    total_correct: int
    accuracy_percent: float


class TriggerPipelineResponse(BaseModel):
    message: str
    session_id: int
    dashboard_token: str
    status: str


# ==================== AUTH HELPERS ====================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    conn = get_connection()
    user = get_user_by_id(conn, int(user_id))
    conn.close()
    
    if user is None:
        raise credentials_exception
    return user


# ==================== BACKGROUND PIPELINE ====================

def run_pipeline_background(session_id: int):
    """
    Background task to run the complete pipeline for a session.
    """
    from src.agents import fetch_articles, analyse_article, generate_mcqs, send_digest, AudioAgent
    import time
    import asyncio
    
    start_time = time.time()
    
    # Initialize trace
    agent_traces[session_id] = {
        "session_id": session_id,
        "status": "in_progress",
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "duration": None,
        "steps": [],
        "summary": {}
    }
    
    def add_step(name, description, status="in_progress", details=None, reasoning=None, articles=None):
        step = {
            "name": name,
            "description": description,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "duration": None,
            "details": details or {},
            "reasoning": reasoning,
            "articles": articles or [],
            "error": None
        }
        agent_traces[session_id]["steps"].append(step)
        return len(agent_traces[session_id]["steps"]) - 1
    
    def update_step(step_idx, status, duration=None, details=None, error=None, articles=None):
        if step_idx < len(agent_traces[session_id]["steps"]):
            agent_traces[session_id]["steps"][step_idx]["status"] = status
            if duration:
                agent_traces[session_id]["steps"][step_idx]["duration"] = duration
            if details:
                agent_traces[session_id]["steps"][step_idx]["details"].update(details)
            if error:
                agent_traces[session_id]["steps"][step_idx]["error"] = error
            if articles:
                agent_traces[session_id]["steps"][step_idx]["articles"] = articles
    
    conn = get_connection()
    
    try:
        print(f"[PIPELINE] Starting for session {session_id}")
        
        # Step 1: Fetch articles
        step_start = time.time()
        step_idx = add_step(
            "Fetch Articles",
            "Scraping latest news from PIB, The Hindu, and Indian Express",
            reasoning="Gathering diverse sources to ensure comprehensive coverage of current affairs relevant to UPSC"
        )
        
        print("[PIPELINE] Fetching articles...")
        articles = fetch_articles()
        
        step_duration = f"{time.time() - step_start:.1f}s"
        update_step(step_idx, "completed", step_duration, {"articles_fetched": len(articles)})
        
        if not articles:
            update_step(step_idx, "failed", error="No articles fetched from sources")
            agent_traces[session_id]["status"] = "failed"
            update_session_status(conn, session_id, 'completed')
            return
        
        print(f"[PIPELINE] Fetched {len(articles)} articles")
        
        # Step 2: Analyze articles
        step_start = time.time()
        step_idx = add_step(
            "Analyze Articles",
            "Using AI to evaluate UPSC relevance, categorize, and extract exam angles",
            reasoning="Each article is scored for Prelims (0-10) and Mains (0-10) relevance. Articles with score >= 5 are considered high-quality and worth studying."
        )
        
        analyzed_articles = []
        article_ids = []
        
        for article in articles:
            try:
                print(f"[PIPELINE] Analyzing: {article['title'][:60]}...")
                analysis = analyse_article(article['title'], article['content'])
                
                display_title = analysis.get('title_english', article['title'])
                
                analyzed_article = {
                    'title': display_title,
                    'title_original': article['title'],
                    'source': article['source'],
                    'url': article.get('url', '#'),
                    'published': article.get('published', 'Recently'),
                    'category': analysis['category'],
                    'prelims_score': analysis['prelims_score'],
                    'mains_score': analysis['mains_score'],
                    'exam_angle': analysis['exam_angle'],
                    'summary': analysis['summary']
                }
                
                analyzed_articles.append(analyzed_article)
                
                # Save to database
                article_id = insert_article(
                    conn,
                    session_id=session_id,
                    title=display_title,
                    source=article['source'],
                    category=analysis['category'],
                    summary=analysis['summary'],
                    exam_angle=analysis['exam_angle'],
                    prelims_score=analysis['prelims_score'],
                    mains_score=analysis['mains_score']
                )
                article_ids.append(article_id)
                
                print(f"[PIPELINE] Saved article {article_id}")
                
            except Exception as e:
                print(f"[PIPELINE] Error analyzing article: {e}")
                continue
        
        step_duration = f"{time.time() - step_start:.1f}s"
        update_step(step_idx, "completed", step_duration, {"articles_analyzed": len(analyzed_articles)})
        
        if not analyzed_articles:
            print("[PIPELINE] No articles analyzed successfully")
            update_step(step_idx, "failed", error="Failed to analyze any articles")
            agent_traces[session_id]["status"] = "failed"
            update_session_status(conn, session_id, 'completed')
            return
        
        print(f"[PIPELINE] Analyzed {len(analyzed_articles)} articles")
        
        # Step 3: Filter high-quality articles
        step_start = time.time()
        step_idx = add_step(
            "Filter Quality Articles",
            "Selecting only articles with Prelims score >= 5 OR Mains score >= 5",
            reasoning="Low-scoring articles (< 5) are not UPSC-relevant and waste study time. We focus only on high-quality, exam-relevant content."
        )
        
        high_quality_articles = [
            article for article in analyzed_articles 
            if article['prelims_score'] >= 5 or article['mains_score'] >= 5
        ]
        
        step_duration = f"{time.time() - step_start:.1f}s"
        filtered_articles_data = [
            {
                "title": a['title'],
                "source": a['source'],
                "category": a['category'],
                "prelims_score": a['prelims_score'],
                "mains_score": a['mains_score'],
                "reasoning": f"Prelims: {a['prelims_score']}/10, Mains: {a['mains_score']}/10 - {a['exam_angle'][:100]}..."
            }
            for a in high_quality_articles
        ]
        
        update_step(
            step_idx, 
            "completed", 
            step_duration, 
            {
                "articles_filtered": len(high_quality_articles),
                "articles_removed": len(analyzed_articles) - len(high_quality_articles)
            },
            articles=filtered_articles_data
        )
        
        if not high_quality_articles:
            print("[PIPELINE] No high-quality articles (score >= 5) found")
            update_step(step_idx, "failed", error="No articles met quality threshold (score >= 5)")
            agent_traces[session_id]["status"] = "failed"
            update_session_status(conn, session_id, 'completed')
            return
        
        print(f"[PIPELINE] Filtered to {len(high_quality_articles)} high-quality articles (score >= 5)")
        
        # Step 4: Generate MCQs and Audio in parallel
        step_start = time.time()
        mcq_step_idx = add_step(
            "Generate MCQs",
            f"Creating 3 UPSC-style MCQs for each of {len(high_quality_articles)} articles",
            reasoning="Each MCQ is mapped to UPSC GS Paper 1/2/3/4, tests conceptual understanding, and includes detailed explanations. 3 MCQs per article ensures comprehensive coverage."
        )
        
        audio_step_idx = add_step(
            "Generate Audio",
            f"Converting {len(high_quality_articles)} articles to audio brief",
            reasoning="Audio brief allows users to listen to the intelligence brief on-the-go. Uses Google Cloud TTS with Indian English voice."
        )
        
        print("[PIPELINE] Generating MCQs and Audio in parallel...")
        
        # MCQ Generation
        total_mcqs = 0
        for article in high_quality_articles:
            try:
                # Get the article_id from the database
                article_db_id = article_ids[analyzed_articles.index(article)]
                
                # Generate 3 MCQs per article for better coverage
                mcqs = generate_mcqs(
                    article_title=article['title'],
                    article_summary=article['summary'],
                    category=article['category'],
                    exam_angle=article['exam_angle'],
                    difficulty='medium',
                    count=3  # 3 MCQs per article
                )
                
                for mcq in mcqs:
                    insert_mcq(
                        conn,
                        article_id=article_db_id,
                        session_id=session_id,
                        question=mcq['question'],
                        option_a=mcq['option_a'],
                        option_b=mcq['option_b'],
                        option_c=mcq['option_c'],
                        option_d=mcq['option_d'],
                        correct_option=mcq['correct_option'],
                        explanation=mcq['explanation'],
                        difficulty=mcq['difficulty'],
                        gs_paper=mcq.get('gs_paper'),
                        learning_insight=mcq.get('learning_insight')
                    )
                    total_mcqs += 1
                
                print(f"[PIPELINE] Generated {len(mcqs)} MCQs for article {article_db_id} (Prelims: {article['prelims_score']}, Mains: {article['mains_score']})")
                
            except Exception as e:
                print(f"[PIPELINE] Error generating MCQs for article: {e}")
                # Continue even if MCQ generation fails for one article
        
        mcq_duration = f"{time.time() - step_start:.1f}s"
        update_step(mcq_step_idx, "completed", mcq_duration, {"mcqs_generated": total_mcqs})
        print(f"[PIPELINE] Generated {total_mcqs} total MCQs for {len(high_quality_articles)} articles")
        
        # Audio Generation
        audio_agent = AudioAgent(conn)
        audio_path = audio_agent.run(session_id, high_quality_articles)
        
        audio_duration = f"{time.time() - step_start:.1f}s"
        if audio_path:
            update_step(audio_step_idx, "completed", audio_duration, {"audio_generated": True, "audio_path": audio_path})
        else:
            update_step(audio_step_idx, "failed", audio_duration, {"audio_generated": False}, error="Audio generation failed")
        
        # Update session to ready
        update_session_status(conn, session_id, 'ready')
        print(f"[PIPELINE] Session {session_id} ready")
        
        # Step 5: Send email digest
        step_start = time.time()
        step_idx = add_step(
            "Send Email Digest",
            "Composing and sending daily intelligence brief with dashboard link",
            reasoning="Email includes article summaries, exam angles, and a personalized dashboard link for MCQ practice."
        )
        
        try:
            session = get_session_by_id(conn, session_id)
            send_digest(high_quality_articles, dashboard_token=session['dashboard_token'], audio_path=audio_path)
            step_duration = f"{time.time() - step_start:.1f}s"
            update_step(step_idx, "completed", step_duration, {"email_sent": True})
            print(f"[PIPELINE] Email sent for session {session_id} with {len(high_quality_articles)} articles")
        except Exception as e:
            step_duration = f"{time.time() - step_start:.1f}s"
            update_step(step_idx, "failed", step_duration, {"email_sent": False}, error=str(e))
            print(f"[PIPELINE] Error sending email: {e}")
        
        # Update trace summary
        total_duration = time.time() - start_time
        categories = list(set(a['category'] for a in high_quality_articles))
        
        agent_traces[session_id]["status"] = "completed"
        agent_traces[session_id]["completed_at"] = datetime.now().isoformat()
        agent_traces[session_id]["duration"] = f"{total_duration:.1f}s"
        agent_traces[session_id]["summary"] = {
            "total_articles": len(articles),
            "high_quality_articles": len(high_quality_articles),
            "total_mcqs": total_mcqs,
            "categories": len(categories)
        }
        
        print(f"[PIPELINE] Completed for session {session_id}")
        
    except Exception as e:
        print(f"[PIPELINE] Fatal error: {e}")
        agent_traces[session_id]["status"] = "failed"
        agent_traces[session_id]["completed_at"] = datetime.now().isoformat()
        update_session_status(conn, session_id, 'completed')
    finally:
        conn.close()


# ==================== STARTUP EVENT ====================

@app.on_event("startup")
async def startup_event():
    """Initialize database and check for pending sessions"""
    conn = get_connection()
    init_db(conn)
    
    # Check for any pending sessions and mark them as completed
    sessions = get_all_sessions(conn, limit=100)
    for session in sessions:
        if session['status'] == 'pending':
            # Check if it has articles
            articles = get_articles_by_session(conn, session['id'])
            if len(articles) == 0:
                # No articles, mark as completed
                update_session_status(conn, session['id'], 'completed')
                print(f"Marked abandoned session {session['id']} as completed")
    
    conn.close()
    print("✓ Database initialized and cleaned up")


# ==================== ADMIN ENDPOINTS ====================

@app.post("/admin/trigger-pipeline", response_model=TriggerPipelineResponse)
async def trigger_pipeline(background_tasks: BackgroundTasks):
    """
    Trigger the pipeline to create a new session.
    This runs in the background and returns immediately.
    """
    conn = get_connection()
    
    try:
        # Create new session
        today = datetime.now().strftime('%Y-%m-%d')
        session_id = insert_session(conn, today, status='pending')
        session = get_session_by_id(conn, session_id)
        
        # Trigger background pipeline
        background_tasks.add_task(run_pipeline_background, session_id)
        
        return TriggerPipelineResponse(
            message="Pipeline started in background",
            session_id=session_id,
            dashboard_token=session['dashboard_token'],
            status="pending"
        )
        
    finally:
        conn.close()


@app.get("/admin/sessions")
async def list_sessions(limit: int = 10):
    """List recent sessions"""
    conn = get_connection()
    try:
        sessions = get_all_sessions(conn, limit=limit)
        return {"sessions": sessions}
    finally:
        conn.close()


@app.get("/admin/trace/{session_id}")
async def get_agent_trace(session_id: int):
    """Get agent reasoning trace for a session"""
    if session_id not in agent_traces:
        raise HTTPException(status_code=404, detail="Trace not found for this session")
    return agent_traces[session_id]


# ==================== PUBLIC ENDPOINTS ====================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "NewsNexus API",
        "status": "running",
        "version": "2.0.0"
    }


# ==================== AUTH ENDPOINTS ====================

@app.post("/auth/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignUpRequest):
    """Register a new user"""
    conn = get_connection()
    
    try:
        # Check if user already exists
        existing_user = get_user_by_email(conn, request.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password and create user
        password_hash = get_password_hash(request.password)
        user_id = insert_user(conn, request.email, password_hash, request.name)
        
        # Create access token
        access_token = create_access_token(data={"sub": str(user_id)})
        
        return TokenResponse(access_token=access_token)
        
    finally:
        conn.close()


@app.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login user"""
    conn = get_connection()
    
    try:
        # Get user by email
        user = get_user_by_email(conn, request.email)
        if not user or not verify_password(request.password, user['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Create access token
        access_token = create_access_token(data={"sub": str(user['id'])})
        
        return TokenResponse(access_token=access_token)
        
    finally:
        conn.close()


@app.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    return UserResponse(
        id=current_user['id'],
        email=current_user['email'],
        name=current_user['name'],
        created_at=current_user['created_at']
    )


# ==================== USER INTERESTS ENDPOINTS ====================

@app.post("/user/interests", response_model=InterestsResponse)
async def save_interests(
    request: InterestsRequest,
    current_user: dict = Depends(get_current_user)
):
    """Save user interests"""
    conn = get_connection()
    
    try:
        set_user_interests(conn, current_user['id'], request.categories)
        return InterestsResponse(categories=request.categories)
    finally:
        conn.close()


@app.get("/user/interests", response_model=InterestsResponse)
async def get_interests(current_user: dict = Depends(get_current_user)):
    """Get user interests"""
    conn = get_connection()
    
    try:
        categories = get_user_interests(conn, current_user['id'])
        return InterestsResponse(categories=categories)
    finally:
        conn.close()


# ==================== USER DASHBOARD ENDPOINTS ====================

@app.get("/user/dashboard")
async def get_user_dashboard(current_user: dict = Depends(get_current_user)):
    """Get latest session for user dashboard"""
    conn = get_connection()
    
    try:
        # Get latest ready session
        session = get_latest_session_for_user(conn, current_user['id'])
        
        if not session:
            return {
                "status": "no_session",
                "message": "No sessions available yet. Trigger a new session to get started."
            }
        
        # Track that user accessed this session
        track_user_session_access(conn, current_user['id'], session['id'])
        
        # Return session token so frontend can use existing session endpoint
        return {
            "status": "ready",
            "session_token": session['dashboard_token'],
            "session_date": session['session_date']
        }
        
    finally:
        conn.close()


@app.post("/user/trigger-pipeline", response_model=TriggerPipelineResponse)
async def user_trigger_pipeline(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """User triggers their own session"""
    conn = get_connection()
    
    try:
        # Create new session
        today = datetime.now().strftime('%Y-%m-%d')
        session_id = insert_session(conn, today, status='pending')
        session = get_session_by_id(conn, session_id)
        
        # Track that user triggered this session
        track_user_session_access(conn, current_user['id'], session_id)
        
        # Trigger background pipeline
        background_tasks.add_task(run_pipeline_background, session_id)
        
        return TriggerPipelineResponse(
            message="Pipeline started in background",
            session_id=session_id,
            dashboard_token=session['dashboard_token'],
            status="pending"
        )
        
    finally:
        conn.close()


# ==================== SESSION ENDPOINTS ====================


@app.get("/session/{token}", response_model=SessionResponse | PendingSessionResponse)
async def get_session(token: str):
    """Get session details by dashboard token"""
    conn = get_connection()
    
    try:
        session = get_session_by_token(conn, token)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session['status'] == 'pending':
            return PendingSessionResponse(
                status="pending",
                message="Intelligence brief being prepared..."
            )
        
        articles = get_articles_by_session(conn, session['id'])
        
        # Filter to only show articles that have MCQs (score >= 5)
        articles_with_mcqs = []
        for article in articles:
            mcqs = get_mcqs_by_article(conn, article['id'])
            if mcqs:  # Only include if article has MCQs
                articles_with_mcqs.append(article)
        
        if not articles_with_mcqs:
            raise HTTPException(status_code=404, detail="No articles with MCQs found in this session")
        
        attempts = get_attempts_by_session(conn, session['id'])
        
        attempts_by_article = {}
        for attempt in attempts:
            article_id = attempt['article_id']
            if article_id not in attempts_by_article:
                attempts_by_article[article_id] = []
            attempts_by_article[article_id].append(attempt)
        
        article_responses = []
        for article in articles_with_mcqs:
            article_attempts = attempts_by_article.get(article['id'], [])
            attempted = len(article_attempts) > 0
            is_correct = article_attempts[0]['is_correct'] if attempted else None
            
            article_responses.append(ArticleResponse(
                id=article['id'],
                title=article['title'],
                source=article['source'],
                category=article['category'],
                prelims_score=article['prelims_score'],
                mains_score=article['mains_score'],
                attempted=attempted,
                is_correct=is_correct
            ))
        
        coverage_summary = Counter(article['category'] for article in articles_with_mcqs)
        feedback = get_latest_feedback_profile(conn)
        focus_note = feedback['focus_note'] if feedback else None
        
        return SessionResponse(
            session_date=session['session_date'],
            status=session['status'],
            coverage_summary=dict(coverage_summary),
            focus_note=focus_note,
            articles=article_responses
        )
        
    finally:
        conn.close()


@app.get("/session/{token}/mcq/{article_id}", response_model=MCQResponse)
async def get_mcq(token: str, article_id: int):
    """Get MCQ for an article"""
    conn = get_connection()
    
    try:
        session = get_session_by_token(conn, token)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        article = get_article_by_id(conn, article_id)
        if not article or article['session_id'] != session['id']:
            raise HTTPException(status_code=404, detail="Article not found in this session")
        
        mcqs = get_mcqs_by_article(conn, article_id)
        if not mcqs:
            raise HTTPException(status_code=404, detail="No MCQ found for this article")
        
        mcq = mcqs[0]
        return MCQResponse(
            id=mcq['id'],
            question=mcq['question'],
            option_a=mcq['option_a'],
            option_b=mcq['option_b'],
            option_c=mcq['option_c'],
            option_d=mcq['option_d'],
            gs_paper=mcq.get('gs_paper'),
            learning_insight=mcq.get('learning_insight')
        )
        
    finally:
        conn.close()


@app.post("/session/{token}/attempt", response_model=AttemptResponse)
async def submit_attempt(token: str, attempt: AttemptRequest, background_tasks: BackgroundTasks):
    """Submit a quiz attempt"""
    conn = get_connection()
    
    try:
        session = get_session_by_token(conn, token)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        article = get_article_by_id(conn, attempt.article_id)
        if not article or article['session_id'] != session['id']:
            raise HTTPException(status_code=404, detail="Article not found in this session")
        
        mcq = get_mcq_by_id(conn, attempt.mcq_id)
        if not mcq or mcq['article_id'] != attempt.article_id:
            raise HTTPException(status_code=404, detail="MCQ not found for this article")
        
        existing_attempts = get_attempts_by_mcq(conn, attempt.mcq_id)
        if existing_attempts:
            existing = existing_attempts[0]
            return AttemptResponse(
                is_correct=existing['is_correct'],
                correct_option=mcq['correct_option'],
                explanation=mcq['explanation'],
                gs_paper=mcq.get('gs_paper'),
                learning_insight=mcq.get('learning_insight')
            )
        
        is_correct = attempt.selected_option == mcq['correct_option']
        
        insert_attempt(
            conn,
            session_id=session['id'],
            article_id=attempt.article_id,
            mcq_id=attempt.mcq_id,
            selected_option=attempt.selected_option,
            is_correct=is_correct,
            time_taken_seconds=attempt.time_taken_seconds
        )
        
        upsert_user_performance(
            conn,
            category=article['category'],
            attempted=1,
            correct=1 if is_correct else 0
        )
        
        all_attempts = get_attempts_by_session(conn, session['id'])
        all_articles = get_articles_by_session(conn, session['id'])
        attempted_articles = set(att['article_id'] for att in all_attempts)
        
        if len(attempted_articles) == len(all_articles):
            update_session_status(conn, session['id'], 'completed')
        
        return AttemptResponse(
            is_correct=is_correct,
            correct_option=mcq['correct_option'],
            explanation=mcq['explanation'],
            gs_paper=mcq.get('gs_paper'),
            learning_insight=mcq.get('learning_insight')
        )
        
    finally:
        conn.close()


@app.get("/session/{token}/results", response_model=ResultsResponse)
async def get_results(token: str):
    """Get detailed results for a completed session"""
    conn = get_connection()
    
    try:
        session = get_session_by_token(conn, token)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session['status'] != 'completed':
            raise HTTPException(status_code=400, detail="Session not yet completed")
        
        attempts = get_attempts_by_session(conn, session['id'])
        if not attempts:
            raise HTTPException(status_code=404, detail="No attempts found")
        
        per_question = []
        total_correct = 0
        total_time = 0
        category_stats = {}
        
        for attempt in attempts:
            article = get_article_by_id(conn, attempt['article_id'])
            mcq = get_mcq_by_id(conn, attempt['mcq_id'])
            
            per_question.append(QuestionResult(
                article_title=article['title'],
                category=article['category'],
                source=article['source'],
                selected_option=attempt['selected_option'],
                correct_option=mcq['correct_option'],
                is_correct=attempt['is_correct'],
                time_taken_seconds=attempt['time_taken_seconds'] or 0,
                gs_paper=mcq.get('gs_paper')
            ))
            
            if attempt['is_correct']:
                total_correct += 1
            
            total_time += attempt['time_taken_seconds'] or 0
            
            category = article['category']
            if category not in category_stats:
                category_stats[category] = {'correct': 0, 'total': 0}
            category_stats[category]['total'] += 1
            if attempt['is_correct']:
                category_stats[category]['correct'] += 1
        
        weak_topics = [
            category for category, stats in category_stats.items()
            if stats['correct'] / stats['total'] < 0.5
        ]
        
        total_questions = len(attempts)
        score_percent = round((total_correct / total_questions) * 100, 2) if total_questions > 0 else 0
        
        return ResultsResponse(
            total_questions=total_questions,
            total_correct=total_correct,
            score_percent=score_percent,
            time_taken_total=total_time,
            per_question=per_question,
            weak_topics=weak_topics
        )
        
    finally:
        conn.close()


@app.get("/performance", response_model=List[PerformanceItem])
async def get_performance():
    """Get overall performance statistics"""
    conn = get_connection()
    
    try:
        performance = get_all_performance(conn)
        
        items = []
        for perf in performance:
            accuracy = round(
                (perf['total_correct'] / perf['total_attempted'] * 100) if perf['total_attempted'] > 0 else 0,
                2
            )
            items.append(PerformanceItem(
                category=perf['category'],
                total_attempted=perf['total_attempted'],
                total_correct=perf['total_correct'],
                accuracy_percent=accuracy
            ))
        
        items.sort(key=lambda x: x.accuracy_percent)
        
        return items
        
    finally:
        conn.close()


# ==================== AUDIO ENDPOINT ====================

@app.get("/session/{token}/audio/stream")
async def stream_audio(token: str):
    """Stream audio file for a session"""
    conn = get_connection()
    
    try:
        session = get_session_by_token(conn, token)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        path = get_audio_path(conn, session['id'])
        if not path or not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Audio not available")
        
        return FileResponse(
            path,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline"}
        )
        
    finally:
        conn.close()


# ==================== HELPER FUNCTION ====================

def get_session_by_id(conn, session_id: int):
    """Helper to get session by ID"""
    from src.utils.database import get_session_by_id as db_get_session
    return db_get_session(conn, session_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

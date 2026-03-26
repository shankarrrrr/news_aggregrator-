import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from src.agents import fetch_articles, analyse_article, send_digest, generate_mcqs
from src.utils import (
    get_connection, init_db, insert_session, update_session_status,
    insert_article, insert_mcq, get_session_by_id
)

# Load environment variables
load_dotenv()

# Fix Windows console encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


def main():
    """
    Main orchestrator for the UPSC news digest pipeline with database integration.
    """
    conn = None
    session_id = None
    
    try:
        # Initialize database
        conn = get_connection()
        init_db(conn)
        print("[DATABASE] Initialized\n")
        
        # Create new session
        today = datetime.now().strftime('%Y-%m-%d')
        session_id = insert_session(conn, today, status='pending')
        session = get_session_by_id(conn, session_id)
        print(f"[SESSION] Created session #{session_id}")
        print(f"[SESSION] Dashboard token: {session['dashboard_token']}\n")
        
        # Step 1: Fetch articles from RSS feeds
        print("[SCRAPER AGENT] Fetching articles...")
        articles = fetch_articles()
        
        if not articles:
            print("[ERROR] No articles fetched. Exiting.")
            if session_id:
                update_session_status(conn, session_id, 'completed')
            return
        
        print(f"[SCRAPER AGENT] Fetched {len(articles)} articles\n")
        
        # Step 2: Analyze each article with Gemini
        analyzed_articles = []
        article_ids = []
        
        for article in articles:
            title = article['title']
            content = article['content']
            source = article['source']
            
            print(f"[ANALYSER AGENT] Analysing: {title[:80]}...")
            
            try:
                analysis = analyse_article(title, content)
                
                # Use English title if available, otherwise original
                display_title = analysis.get('title_english', title)
                
                # Combine original article data with analysis
                analyzed_article = {
                    'title': display_title,
                    'title_original': title,  # Keep original for reference
                    'source': source,
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
                    source=source,
                    category=analysis['category'],
                    summary=analysis['summary'],
                    exam_angle=analysis['exam_angle'],
                    prelims_score=analysis['prelims_score'],
                    mains_score=analysis['mains_score']
                )
                article_ids.append(article_id)
                
                print(f"  → Category: {analysis['category']}, Prelims Score: {analysis['prelims_score']}/10")
                print(f"  → Saved to database (Article ID: {article_id})\n")
                
            except Exception as e:
                print(f"  → Error analyzing article: {e}\n")
                continue
        
        if not analyzed_articles:
            print("[ERROR] No articles were successfully analyzed. Exiting.")
            if session_id:
                update_session_status(conn, session_id, 'completed')
            return
        
        print(f"[ANALYSER AGENT] Successfully analyzed {len(analyzed_articles)} articles\n")
        
        # Step 3: Generate MCQs for top articles
        print("[MCQ GENERATOR] Generating practice questions...")
        top_articles = sorted(analyzed_articles, key=lambda x: x['prelims_score'], reverse=True)[:5]
        
        total_mcqs = 0
        for idx, article in enumerate(top_articles):
            try:
                mcqs = generate_mcqs(
                    article_title=article['title'],
                    article_summary=article['summary'],
                    category=article['category'],
                    exam_angle=article['exam_angle'],
                    difficulty='medium',
                    count=2
                )
                
                # Save MCQs to database
                article_db_id = article_ids[analyzed_articles.index(article)]
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
                        difficulty=mcq['difficulty']
                    )
                    total_mcqs += 1
                
                print(f"  → Generated {len(mcqs)} MCQs for: {article['title'][:60]}...")
                
            except Exception as e:
                print(f"  → Error generating MCQs: {e}")
        
        print(f"[MCQ GENERATOR] Generated {total_mcqs} total MCQs\n")
        
        # Update session status to ready
        update_session_status(conn, session_id, 'ready')
        print(f"[SESSION] Status updated to 'ready'\n")
        
        # Step 4: Send digest email
        print("[DIGEST AGENT] Sending email digest...")
        send_digest(analyzed_articles, dashboard_token=session['dashboard_token'])
        
        # Update session status to completed
        update_session_status(conn, session_id, 'completed')
        print(f"[SESSION] Status updated to 'completed'\n")
        
        # Step 5: Success
        print("[DONE] Digest delivered successfully")
        print(f"[DONE] Session #{session_id} completed")
        print(f"[DONE] Dashboard token: {session['dashboard_token']}")
        print(f"[DONE] Total articles: {len(analyzed_articles)}")
        print(f"[DONE] Total MCQs: {total_mcqs}")
        
    except Exception as e:
        print(f"[ERROR] Pipeline failed: {e}")
        if session_id and conn:
            update_session_status(conn, session_id, 'completed')
        raise
    finally:
        if conn:
            conn.close()
            print("[DATABASE] Connection closed")


if __name__ == "__main__":
    main()

import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from dotenv import load_dotenv
from datetime import datetime
from collections import Counter
import logging
import re
from src.utils.pdf_generator import generate_pdf_analysis

# Load environment variables
load_dotenv()

# Fix Windows console encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def is_hindi(text):
    """Check if text contains Hindi characters."""
    return bool(re.search(r'[\u0900-\u097F]', text))


def send_digest(articles, dashboard_token=None, audio_path=None, save_preview=False):
    """
    Send a digest email with top 5 articles sorted by prelims_score.
    Includes detailed PDF analysis as attachment and dashboard link.
    
    Args:
        articles: List of dicts with title, category, prelims_score, mains_score, exam_angle, summary, source, url, published
        dashboard_token: Unique token for dashboard access
        audio_path: Path to audio file (optional)
        save_preview: If True, save HTML to digest_preview.html
    """
    # Sort by prelims_score descending and take top 5
    top_articles = sorted(articles, key=lambda x: x.get('prelims_score', 0), reverse=True)[:5]
    
    if not top_articles:
        logger.warning("No articles to send in digest")
        return
    
    # Count categories for summary
    category_counts = Counter(article.get('category', 'General') for article in top_articles)
    
    # Get SMTP credentials from environment
    smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', 587))
    smtp_user = os.environ.get('SMTP_USER')
    smtp_password = os.environ.get('SMTP_PASSWORD')
    from_email = os.environ.get('SMTP_FROM_EMAIL', smtp_user)
    from_name = os.environ.get('SMTP_FROM_NAME', 'UPSC News Digest')
    recipient = os.environ.get('DIGEST_RECIPIENT')
    
    if not all([smtp_user, smtp_password, recipient]):
        raise ValueError("Missing required environment variables: SMTP_USER, SMTP_PASSWORD, or DIGEST_RECIPIENT")
    
    # Generate PDF analysis
    logger.info("Generating detailed PDF analysis...")
    pdf_filename = f"output/upsc_analysis_{datetime.now().strftime('%Y%m%d')}.pdf"
    generate_pdf_analysis(top_articles, pdf_filename)
    
    # Build HTML email with dashboard link
    html_content = build_html_email(top_articles, category_counts, dashboard_token, audio_path)
    
    # Save preview if requested
    if save_preview:
        with open('output/digest_preview.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info("Preview saved to output/digest_preview.html")
    
    # Create email message with updated subject
    msg = MIMEMultipart('mixed')
    formatted_date = datetime.now().strftime('%d %B %Y')
    msg['Subject'] = f'NewsNexus Intelligence Brief · {formatted_date} · Practice Test Ready'
    msg['From'] = f'{from_name} <{from_email}>'
    msg['To'] = recipient
    
    # Attach HTML content
    html_part = MIMEText(html_content, 'html')
    msg.attach(html_part)
    
    # Attach PDF
    try:
        with open(pdf_filename, 'rb') as pdf_file:
            pdf_attachment = MIMEApplication(pdf_file.read(), _subtype='pdf')
            pdf_attachment.add_header('Content-Disposition', 'attachment', filename=pdf_filename)
            msg.attach(pdf_attachment)
        logger.info(f"PDF attached: {pdf_filename}")
    except Exception as e:
        logger.error(f"Failed to attach PDF: {e}")
    
    # Send email
    try:
        logger.info(f"Connecting to SMTP server {smtp_host}:{smtp_port}...")
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        logger.info(f"Digest email sent successfully to {recipient}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send digest email: {e}")
        raise


def build_html_email(articles, category_counts, dashboard_token=None, audio_path=None):
    """
    Build HTML email content with article cards - premium academic design.
    
    Args:
        articles: List of article dicts
        category_counts: Counter object with category distribution
        dashboard_token: Unique token for dashboard access
        audio_path: Path to audio file (optional)
        
    Returns:
        str: HTML content
    """
    # Dashboard base URL
    DASHBOARD_BASE_URL = os.environ.get('DASHBOARD_BASE_URL', 'http://localhost:3000')
    API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000')
    
    # Category color mapping - Modern vibrant palette matching PDF
    category_colors = {
        'Polity': '#3b82f6',           # Blue
        'Economy': '#10b981',          # Green
        'Environment': '#059669',      # Emerald
        'Science & Tech': '#8b5cf6',   # Purple
        'International Relations': '#f59e0b',  # Amber
        'History & Culture': '#ec4899', # Pink
        'Social Issues': '#ef4444',    # Red
        'Security & Defence': '#dc2626' # Dark Red
    }
    
    # Build category summary
    category_summary_parts = []
    for cat, count in category_counts.most_common():
        category_summary_parts.append(f'<span style="color: #1a1a2e; font-weight: bold; font-size: 12px;">{count} {cat}</span>')
    category_summary = '  <span style="color: #cccccc;">·</span>  '.join(category_summary_parts)
    
    # Get today's date
    today_date = datetime.now().strftime("%A, %d %B %Y")
    
    # Build dashboard CTA block
    dashboard_cta = ""
    if dashboard_token:
        dashboard_url = f"{DASHBOARD_BASE_URL}/dashboard/{dashboard_token}"
        audio_url = f"{API_BASE_URL}/session/{dashboard_token}/audio/stream"
        article_count = len(articles)
        
        # Audio button (only if audio exists)
        audio_button = ""
        if audio_path and os.path.exists(audio_path):
            audio_button = f"""
                <a href="{audio_url}" style="
                  display: inline-block;
                  padding: 10px 20px;
                  background-color: transparent;
                  color: #10b981;
                  border: 1px solid #10b981;
                  font-family: 'Courier New', monospace;
                  font-size: 12px;
                  letter-spacing: 0.1em;
                  text-decoration: none;
                  text-transform: uppercase;
                ">🎧 LISTEN TO BRIEF</a>
            """
        
        dashboard_cta = f"""
            <div style="
              margin: 24px 0;
              padding: 20px 24px;
              background-color: #1a2332;
              border-left: 4px solid #d4820a;
            ">
              <p style="
                margin: 0 0 4px 0;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                letter-spacing: 0.15em;
                color: #a0a8b0;
                text-transform: uppercase;
              ">TODAY'S PRACTICE TEST · READY NOW</p>
              
              <p style="
                margin: 0 0 16px 0;
                font-family: Georgia, serif;
                font-size: 16px;
                color: #f5f0e8;
                line-height: 1.5;
              ">Test your understanding of today's {article_count} articles 
              with MCQs generated by your intelligence agent.</p>
              
              <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                <a href="{dashboard_url}" style="
                  display: inline-block;
                  padding: 10px 20px;
                  background-color: #d4820a;
                  color: #ffffff;
                  font-family: 'Courier New', monospace;
                  font-size: 12px;
                  letter-spacing: 0.1em;
                  text-decoration: none;
                  text-transform: uppercase;
                ">TAKE TODAY'S TEST →</a>
                
                {audio_button}
                
                <a href="{dashboard_url}" style="
                  display: inline-block;
                  padding: 10px 20px;
                  background-color: transparent;
                  color: #d4820a;
                  border: 1px solid #d4820a;
                  font-family: 'Courier New', monospace;
                  font-size: 12px;
                  letter-spacing: 0.1em;
                  text-decoration: none;
                  text-transform: uppercase;
                ">VIEW DASHBOARD</a>
              </div>
              
              <p style="
                margin: 16px 0 0 0;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                color: #6b7c8f;
                letter-spacing: 0.05em;
              ">Dashboard Link: {dashboard_url}</p>
            </div>
        """
    
    # Build article cards
    cards_html = ""
    for idx, article in enumerate(articles):
        category = article.get('category', 'General')
        color = category_colors.get(category, '#666666')
        source = article.get('source', 'Unknown')
        title = article.get('title', 'No Title')
        title_original = article.get('title_original', title)
        url = article.get('url', '#')
        published = article.get('published', 'Recently')
        prelims_score = article.get('prelims_score', 'N/A')
        mains_score = article.get('mains_score', 'N/A')
        exam_angle = article.get('exam_angle', 'N/A')
        summary = article.get('summary', 'No summary available')
        
        # Check if original title is in Hindi/non-English
        title_html = ""
        if is_hindi(title_original) and title != title_original:
            # Show English title prominently, original in smaller italic text
            title_html = f"""
                <h2 style="color: #1a1a2e; font-size: 22px; font-family: Georgia, serif; line-height: 1.35; font-weight: bold; margin: 10px 0 4px 0;">
                    {title}
                </h2>
                <div style="color: #999999; font-size: 13px; font-family: Georgia, serif; font-style: italic; margin-top: 4px;">
                    {title_original}
                </div>
            """
        else:
            title_html = f"""
                <h2 style="color: #1a1a2e; font-size: 22px; font-family: Georgia, serif; line-height: 1.35; font-weight: bold; margin: 10px 0 4px 0;">
                    {title}
                </h2>
            """
        
        # Add separator before each article except the first
        separator = ""
        if idx > 0:
            separator = """
                <div style="position: relative; height: 1px; background: #e8e0d5; margin: 0 32px;">
                    <span style="position: absolute; left: 50%; top: -6px; transform: translateX(-50%); background: #ffffff; padding: 0 8px; color: #ccbbaa; font-size: 10px;">◆</span>
                </div>
            """
        
        cards_html += f"""
            {separator}
            <div style="padding: 28px 32px;">
                <div style="margin-bottom: 10px;">
                    <span style="font-size: 11px; letter-spacing: 2px; font-weight: bold; color: {color}; text-transform: uppercase; font-family: Arial, sans-serif;">{category}</span>
                    <span style="color: #cccccc; margin: 0 8px;">|</span>
                    <span style="color: #999999; font-size: 11px; letter-spacing: 1px; font-family: Arial, sans-serif;">{source}</span>
                    <span style="float: right; color: #bbbbbb; font-size: 11px; font-family: Arial, sans-serif;">{published}</span>
                </div>
                {title_html}
                <div style="margin: 10px 0;">
                    <span style="color: #999999; font-size: 11px; letter-spacing: 1px; font-family: Arial, sans-serif;">PRELIMS</span>
                    <span style="color: #3b82f6; font-size: 15px; font-weight: bold; font-family: Arial, sans-serif; margin-left: 6px;">{prelims_score}/10</span>
                    <span style="margin: 0 24px;"></span>
                    <span style="color: #999999; font-size: 11px; letter-spacing: 1px; font-family: Arial, sans-serif;">MAINS</span>
                    <span style="color: #f59e0b; font-size: 15px; font-weight: bold; font-family: Arial, sans-serif; margin-left: 6px;">{mains_score}/10</span>
                </div>
                <div style="height: 1px; background: #f0ebe3; margin: 12px 0;"></div>
                <div style="border-left: 3px solid {color}; padding-left: 14px; margin: 12px 0; background: #f8fafc; padding: 12px 14px;">
                    <div style="color: {color}; font-size: 11px; letter-spacing: 2px; font-weight: bold; font-family: Arial, sans-serif; margin-bottom: 6px;">EXAM ANGLE</div>
                    <div style="color: #555555; font-size: 14px; font-style: italic; font-family: Georgia, serif; line-height: 1.7;">
                        {exam_angle}
                    </div>
                </div>
                <p style="color: #333333; font-size: 14px; font-family: Georgia, serif; line-height: 1.8; margin: 10px 0 0 0;">
                    {summary}
                </p>
                <a href="{url}" style="display: inline-block; background: {color}; color: white; font-size: 12px; font-family: Arial, sans-serif; text-decoration: none; letter-spacing: 1px; margin-top: 16px; padding: 10px 24px; border-radius: 4px; font-weight: bold;">READ FULL ARTICLE →</a>
            </div>
        """
    
    # Count total articles analyzed
    total_analyzed = sum(category_counts.values())
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; background-color: #f9f6f1;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-left: 3px solid #1a1a2e; border-right: 3px solid #1a1a2e;">
            <div style="background: #1a1a2e; padding: 32px 32px 24px 32px;">
                <div style="color: white; letter-spacing: 8px; font-size: 13px; font-family: Arial, sans-serif; margin-bottom: 8px;">NEWSNEXUS</div>
                <h1 style="color: white; font-family: Georgia, serif; font-size: 32px; font-weight: normal; line-height: 1.2; margin: 8px 0 4px 0;">UPSC Daily Intelligence</h1>
                <div style="color: #8899aa; font-size: 13px; font-style: italic; font-family: Georgia, serif;">Curated by autonomous AI agents for serious aspirants</div>
                <div style="height: 1px; background: rgba(136, 153, 170, 0.2); margin-top: 16px;"></div>
                <div style="color: #8899aa; font-size: 11px; letter-spacing: 2px; padding-top: 12px; font-family: Arial, sans-serif; text-transform: uppercase;">{today_date}</div>
            </div>
            <div style="background: #f0ebe3; padding: 14px 32px; border-bottom: 1px solid #e0d8cc;">
                <span style="color: #666666; font-size: 12px; font-family: Arial, sans-serif;">Today's Coverage:</span>  {category_summary}
            </div>
            {dashboard_cta}
            {cards_html}
            <div style="background: #1a1a2e; padding: 24px 32px; text-align: center;">
                <div style="color: #8899aa; letter-spacing: 6px; font-size: 11px; font-family: Arial, sans-serif; margin-bottom: 6px;">NEWSNEXUS</div>
                <div style="color: #4a5a6a; font-size: 12px; font-family: Georgia, serif; font-style: italic; margin-top: 6px;">Generated autonomously by the NewsNexus agentic pipeline</div>
                <div style="color: #4a5a6a; font-size: 11px; letter-spacing: 1px; margin-top: 8px; font-family: Arial, sans-serif;">Sources: PIB  ·  The Hindu  ·  Indian Express</div>
                <div style="color: #3a4a5a; font-size: 11px; margin-top: 4px; font-family: Arial, sans-serif;">{total_analyzed} articles analysed  ·  Top 5 delivered</div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


if __name__ == "__main__":
    # Test with sample articles
    test_articles = [
        {
            "title": "New Digital Public Infrastructure for Healthcare Launched",
            "category": "Science & Tech",
            "prelims_score": 9,
            "mains_score": 8,
            "exam_angle": "Important for understanding government's digital governance initiatives and healthcare reforms.",
            "summary": "Government launches comprehensive DPI for healthcare under Ayushman Bharat Digital Mission. Will integrate health databases and enable telemedicine in rural areas using blockchain and AI technologies.",
            "source": "PIB",
            "url": "https://pib.gov.in/example",
            "published": "March 26, 2026"
        },
        {
            "title": "India-US Trade Agreement Negotiations Progress",
            "category": "International Relations",
            "prelims_score": 8,
            "mains_score": 9,
            "exam_angle": "Relevant for understanding bilateral trade relations and India's foreign policy priorities.",
            "summary": "Trade ministers discuss tariff reductions and market access. Focus on technology transfer and defense cooperation as part of broader strategic partnership.",
            "source": "The Hindu",
            "url": "https://thehindu.com/example",
            "published": "March 26, 2026"
        },
        {
            "title": "Supreme Court Ruling on Article 370",
            "category": "Polity",
            "prelims_score": 10,
            "mains_score": 10,
            "exam_angle": "Critical constitutional development affecting federal structure and special provisions.",
            "summary": "SC upholds abrogation of Article 370, impacting Jammu & Kashmir's special status. Landmark judgment with implications for constitutional law and center-state relations.",
            "source": "Indian Express",
            "url": "https://indianexpress.com/example",
            "published": "March 25, 2026"
        }
    ]
    
    print("Testing digest email...\n")
    
    try:
        send_digest(test_articles, save_preview=True)
        print("Digest email sent successfully!")
        print("Preview saved to digest_preview.html")
    except Exception as e:
        print(f"Error: {e}")

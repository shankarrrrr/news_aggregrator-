import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()


def analyse_article(title, content):
    """
    Analyze an article for UPSC exam relevance using Google Gemini API.
    Translates non-English content to English.
    
    Args:
        title: Article title
        content: Article content
        
    Returns:
        dict: Analysis with category, scores, exam angle, summary, and English title
    """
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""You are a UPSC exam expert. Analyze the following article and provide a structured assessment.

IMPORTANT: If the title or content is in Hindi or any non-English language, first translate it to English.

Article Title: {title}
Article Content: {content}

Think step by step:
1. If the title is in Hindi/non-English, translate it to English
2. Identify the main theme and subject area
3. Evaluate its relevance for UPSC Prelims (factual, current affairs)
4. Evaluate its relevance for UPSC Mains (analytical, essay potential)
5. Determine why this matters for UPSC preparation
6. Create a concise summary for aspirants

Now provide your analysis in this exact JSON format:
{{
    "title_english": "<English translation of title if non-English, otherwise same as original>",
    "category": "<one of: Polity, Economy, Environment, Science & Tech, International Relations, History & Culture, Social Issues, Security & Defence>",
    "prelims_score": <number 1-10>,
    "mains_score": <number 1-10>,
    "exam_angle": "<one sentence explaining UPSC relevance in English>",
    "summary": "<2-3 lines summarizing key points for UPSC aspirants in English>"
}}

Return only valid JSON, no additional text."""

    response = model.generate_content(prompt)
    result_text = response.text.strip()
    
    # Extract JSON from response (handle markdown code blocks if present)
    if result_text.startswith('```'):
        result_text = result_text.split('```')[1]
        if result_text.startswith('json'):
            result_text = result_text[4:]
        result_text = result_text.strip()
    
    return json.loads(result_text)


if __name__ == "__main__":
    # Test with a sample article
    test_title = "India Launches New Digital Public Infrastructure for Healthcare"
    test_content = """
    The Government of India has announced the launch of a comprehensive Digital Public Infrastructure (DPI) 
    for healthcare, aimed at providing universal health coverage and improving healthcare delivery across the nation. 
    The new system will integrate various health databases, enable seamless sharing of medical records, and facilitate 
    telemedicine services in rural areas. This initiative is part of the Ayushman Bharat Digital Mission and will 
    leverage technologies like blockchain for data security and AI for diagnostic support. The platform is expected 
    to benefit over 500 million citizens in its first phase, with particular focus on underserved regions.
    """
    
    print("Testing article analysis...\n")
    print(f"Title: {test_title}\n")
    
    try:
        result = analyse_article(test_title, test_content)
        print("Analysis Result:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")

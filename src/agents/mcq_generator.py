"""
MCQ Generator Agent
Generates UPSC-style multiple choice questions from analyzed articles using Gemini AI
"""

import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()


def generate_mcqs(article_title: str, article_summary: str, category: str, 
                  exam_angle: str, difficulty: str = 'medium', count: int = 3) -> list:
    """
    Generate UPSC-style MCQs from an article using Gemini AI.
    
    Args:
        article_title: Article title
        article_summary: Article summary
        category: Article category
        exam_angle: UPSC exam angle
        difficulty: Question difficulty ('easy', 'medium', 'hard')
        count: Number of MCQs to generate (default: 3)
        
    Returns:
        list: List of MCQ dictionaries with question, options, correct answer, and explanation
    """
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    difficulty_guidelines = {
        'easy': 'Focus on direct facts, definitions, and basic concepts. Suitable for beginners.',
        'medium': 'Require understanding and application of concepts. Standard UPSC Prelims level.',
        'hard': 'Require analysis, critical thinking, and connecting multiple concepts. Advanced level.'
    }
    
    prompt = f"""You are a UPSC exam question paper setter with expertise in creating high-quality Prelims questions. Generate {count} UPSC General Studies (GS) style multiple choice questions based on the following article.

Article Title: {article_title}
Category: {category}
Summary: {article_summary}
UPSC Exam Angle: {exam_angle}

Difficulty Level: {difficulty}
Guidelines: {difficulty_guidelines.get(difficulty, difficulty_guidelines['medium'])}

CRITICAL REQUIREMENTS:
1. Questions MUST be UPSC GS Prelims style - factual, clear, and unambiguous
2. Questions should test understanding of concepts, not just memory
3. All 4 options must be plausible and closely related to the topic
4. Only ONE option should be clearly correct
5. Avoid "All of the above" or "None of the above" options
6. Questions should be relevant to UPSC GS Paper 1, 2, 3, or 4
7. Include current affairs context where relevant
8. Test application of knowledge, not just recall
9. Explanation should be educational and cite facts
10. Provide GS Paper mapping and a key learning insight for retention

UPSC GS MAPPING:
- Polity → GS Paper 2 (Governance, Constitution, Polity)
- Economy → GS Paper 3 (Economic Development)
- Environment → GS Paper 3 (Environment, Biodiversity)
- Science & Tech → GS Paper 3 (Science & Technology)
- International Relations → GS Paper 2 (International Relations)
- History & Culture → GS Paper 1 (Indian Heritage and Culture)
- Social Issues → GS Paper 1 (Social Issues)
- Security & Defence → GS Paper 3 (Security)

Return your response as a JSON array with this exact structure:
[
  {{
    "question": "<UPSC-style question text>",
    "option_a": "<option A text>",
    "option_b": "<option B text>",
    "option_c": "<option C text>",
    "option_d": "<option D text>",
    "correct_option": "<A/B/C/D>",
    "explanation": "<2-3 lines explaining why the answer is correct and why other options are incorrect>",
    "difficulty": "{difficulty}",
    "gs_paper": "<GS Paper 1/2/3/4 with topic>",
    "learning_insight": "<One key takeaway or concept to remember for UPSC preparation>"
  }}
]

Generate exactly {count} high-quality UPSC GS questions. Return only valid JSON, no additional text."""

    response = model.generate_content(prompt)
    result_text = response.text.strip()
    
    # Extract JSON from response
    if result_text.startswith('```'):
        result_text = result_text.split('```')[1]
        if result_text.startswith('json'):
            result_text = result_text[4:]
        result_text = result_text.strip()
    
    mcqs = json.loads(result_text)
    
    # Validate structure
    for mcq in mcqs:
        required_fields = ['question', 'option_a', 'option_b', 'option_c', 'option_d', 
                          'correct_option', 'explanation', 'difficulty', 'gs_paper', 'learning_insight']
        if not all(field in mcq for field in required_fields):
            raise ValueError(f"Invalid MCQ structure: {mcq}")
        
        if mcq['correct_option'] not in ['A', 'B', 'C', 'D']:
            raise ValueError(f"Invalid correct_option: {mcq['correct_option']}")
    
    return mcqs


def generate_mcqs_for_session(articles: list, difficulty: str = 'medium', 
                              mcqs_per_article: int = 3) -> dict:
    """
    Generate MCQs for all articles in a session.
    
    Args:
        articles: List of article dictionaries
        difficulty: Default difficulty level
        mcqs_per_article: Number of MCQs per article
        
    Returns:
        dict: Mapping of article index to list of MCQs
    """
    all_mcqs = {}
    
    for idx, article in enumerate(articles):
        try:
            mcqs = generate_mcqs(
                article_title=article.get('title', ''),
                article_summary=article.get('summary', ''),
                category=article.get('category', 'General'),
                exam_angle=article.get('exam_angle', ''),
                difficulty=difficulty,
                count=mcqs_per_article
            )
            all_mcqs[idx] = mcqs
            print(f"Generated {len(mcqs)} MCQs for article: {article.get('title', '')[:60]}...")
        except Exception as e:
            print(f"Error generating MCQs for article {idx}: {e}")
            all_mcqs[idx] = []
    
    return all_mcqs


if __name__ == "__main__":
    # Test MCQ generation
    test_article = {
        'title': 'India Launches New Digital Public Infrastructure for Healthcare',
        'summary': 'Government launches comprehensive DPI for healthcare under Ayushman Bharat Digital Mission. Will integrate health databases and enable telemedicine in rural areas.',
        'category': 'Science & Tech',
        'exam_angle': 'Important for understanding government\'s digital governance initiatives and healthcare reforms.'
    }
    
    print("Testing MCQ generation...\n")
    
    try:
        mcqs = generate_mcqs(
            article_title=test_article['title'],
            article_summary=test_article['summary'],
            category=test_article['category'],
            exam_angle=test_article['exam_angle'],
            difficulty='medium',
            count=2
        )
        
        print(f"Generated {len(mcqs)} MCQs:\n")
        for i, mcq in enumerate(mcqs, 1):
            print(f"Question {i}: {mcq['question']}")
            print(f"A) {mcq['option_a']}")
            print(f"B) {mcq['option_b']}")
            print(f"C) {mcq['option_c']}")
            print(f"D) {mcq['option_d']}")
            print(f"Correct: {mcq['correct_option']}")
            print(f"Explanation: {mcq['explanation']}")
            print(f"Difficulty: {mcq['difficulty']}\n")
        
        print("MCQ generation test successful!")
        
    except Exception as e:
        print(f"Error: {e}")

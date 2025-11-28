import requests
import json

def get_gemini_response(message):
    """Free Google Gemini AI - 15 requests/minute"""
    try:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        # Get free API key from: https://makersuite.google.com/app/apikey
        API_KEY = os.getenv("GEMINI_API_KEY")  # Load from environment variable
        if not API_KEY:
            return get_fallback_response(message)
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"You are a movie expert. Answer this movie question: {message}"
                }]
            }]
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return get_fallback_response(message)
            
    except Exception as e:
        return get_fallback_response(message)

def get_fallback_response(message):
    """Smart movie responses without API"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['comedy', 'funny', 'laugh']):
        return "For comedy, I recommend: The Grand Budapest Hotel, Superbad, or Knives Out!"
    elif any(word in message_lower for word in ['action', 'fight', 'adventure']):
        return "Great action movies: Mad Max Fury Road, John Wick, or Mission Impossible!"
    elif any(word in message_lower for word in ['horror', 'scary', 'thriller']):
        return "For thrills: Get Out, Hereditary, or A Quiet Place are fantastic!"
    elif any(word in message_lower for word in ['romance', 'love', 'romantic']):
        return "Romantic picks: The Princess Bride, Before Sunrise, or La La Land!"
    elif any(word in message_lower for word in ['sci-fi', 'science', 'future']):
        return "Sci-fi gems: Blade Runner 2049, Arrival, or Interstellar!"
    else:
        return f"Based on your interest in '{message[:30]}...', I'd suggest exploring different genres! What mood are you in - comedy, action, or drama?"
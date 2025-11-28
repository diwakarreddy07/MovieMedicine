# Enhanced conversational movie AI assistant
import random
import re

# Conversation context to make it more interactive
conversation_context = {
    'last_genre': None,
    'user_preferences': [],
    'conversation_count': 0
}

def get_free_ai_response(message):
    """Enhanced conversational movie AI - completely free!"""
    global conversation_context
    message_lower = message.lower()
    conversation_context['conversation_count'] += 1
    
    # Greeting responses
    if any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good evening']):
        return random.choice([
            "🎬 Hey there, movie lover! I'm your personal movie assistant. What kind of films are you in the mood for today?",
            "🍿 Hello! Ready to discover some amazing movies? Tell me what you're feeling - comedy, action, drama, or something else?",
            "🎭 Hi! I'm here to help you find the perfect movie. What's your vibe today - something light and fun or deep and meaningful?"
        ])
    
    # Personal questions about the AI
    elif any(word in message_lower for word in ['who are you', 'what are you', 'about you', 'your name']):
        return "🤖 I'm your AI movie companion! I know tons about films and love helping people discover their next favorite movie. I can recommend based on mood, genre, or even specific actors you like. What would you like to explore?"
    
    # How are you responses
    elif any(word in message_lower for word in ['how are you', 'how do you feel', 'whats up']):
        return random.choice([
            "🎬 I'm doing great! Just watched some amazing trailers and I'm excited to share movie recommendations. How about you? What's your movie mood today?",
            "🍿 Fantastic! I've been analyzing the latest films and I'm ready to help you find something perfect to watch. What genre speaks to you right now?"
        ])
    
    # Thank you responses
    elif any(word in message_lower for word in ['thank', 'thanks', 'appreciate']):
        return random.choice([
            "🎬 You're so welcome! I love talking movies. Got any other questions or need more recommendations?",
            "🍿 Happy to help! That's what I'm here for. Want to explore another genre or need something specific?"
        ])
    
    # Genre-based responses with follow-up questions
    elif any(word in message_lower for word in ['comedy', 'funny', 'laugh', 'humor']):
        conversation_context['last_genre'] = 'comedy'
        return random.choice([
            "😂 Great choice! For comedy gold, I'd suggest: The Grand Budapest Hotel (quirky & stylish), Superbad (raunchy teen comedy), or What We Do in the Shadows (vampire mockumentary). Do you prefer witty dialogue or physical comedy?",
            "🎭 Comedy it is! Try: Knives Out (murder mystery comedy), The Nice Guys (buddy cop comedy), or Hunt for the Wilderpeople (heartwarming adventure). Are you watching alone or with friends?",
            "😄 Love comedies! Consider: Groundhog Day (time loop classic), The Princess Bride (fairy tale parody), or Airplane! (slapstick masterpiece). Want something recent or are classics okay?"
        ])
    
    elif any(word in message_lower for word in ['action', 'fight', 'adventure', 'explosion']):
        conversation_context['last_genre'] = 'action'
        return random.choice([
            "💥 Action time! Mad Max: Fury Road (non-stop chase), John Wick series (stylish gunplay), or Mission Impossible (death-defying stunts). Do you like realistic action or over-the-top spectacle?",
            "🔥 Adrenaline rush coming up! The Raid (martial arts masterpiece), Atomic Blonde (stylish spy thriller), or Nobody (ordinary guy goes badass). Prefer hand-to-hand combat or big explosions?",
            "⚡ Epic adventures await! Indiana Jones (classic adventure), The Matrix (mind-bending action), or Speed (non-stop thriller). Want something with a great story or pure action?"
        ])
    
    elif any(word in message_lower for word in ['horror', 'scary', 'thriller', 'suspense']):
        conversation_context['last_genre'] = 'horror'
        return random.choice([
            "😱 Scary movie night! Get Out (social thriller), Hereditary (family horror), or A Quiet Place (creature feature). How much can you handle - jump scares or psychological terror?",
            "🎃 Horror classics: The Shining (psychological masterpiece), Alien (space horror), or The Thing (paranoid thriller). Do you prefer monsters or human villains?",
            "😰 Psychological thrillers: Shutter Island (mind-bender), Gone Girl (twisted marriage), or Black Swan (ballet nightmare). Want something that messes with your head?"
        ])
    
    elif any(word in message_lower for word in ['romance', 'love', 'romantic', 'date']):
        conversation_context['last_genre'] = 'romance'
        return random.choice([
            "💕 Romance time! Before Sunrise (philosophical love), La La Land (musical romance), or The Princess Bride (adventure romance). Are you planning a date night or solo viewing?",
            "❤️ Love stories: Eternal Sunshine (sci-fi romance), Her (AI love story), or About Time (time travel romance). Do you like happy endings or bittersweet stories?",
            "🌹 Classic romance: Casablanca (wartime love), Roman Holiday (fairy tale), or When Harry Met Sally (friends to lovers). Want something timeless or modern?"
        ])
    
    elif any(word in message_lower for word in ['sci-fi', 'science', 'future', 'space', 'alien']):
        conversation_context['last_genre'] = 'sci-fi'
        return random.choice([
            "🚀 Sci-fi masterpieces! Blade Runner 2049 (cyberpunk sequel), Arrival (alien linguistics), or Interstellar (space epic). Do you like hard science or space opera?",
            "👽 Space adventures: Guardians of the Galaxy (fun space romp), Star Wars (classic saga), or The Martian (survival story). Want something serious or more fun?",
            "🤖 Mind-bending sci-fi: Inception (dream heist), Ex Machina (AI thriller), or Minority Report (future crime). Prefer action or philosophical themes?"
        ])
    
    elif any(word in message_lower for word in ['drama', 'emotional', 'deep', 'serious']):
        conversation_context['last_genre'] = 'drama'
        return random.choice([
            "🎭 Powerful dramas! Parasite (class thriller), Moonlight (coming of age), or Manchester by the Sea (grief story). Ready for something emotionally heavy?",
            "😢 Emotional journeys: The Pursuit of Happyness (inspiring struggle), Room (survival story), or Lion (lost child). Want something uplifting or more intense?",
            "🏆 Award winners: There Will Be Blood (oil baron epic), No Country for Old Men (modern western), or 12 Years a Slave (historical drama). Prefer character studies or epic stories?"
        ])
    
    # Follow-up responses based on previous genre
    elif any(word in message_lower for word in ['more', 'another', 'different', 'else']):
        if conversation_context['last_genre']:
            return f"🎬 Want more {conversation_context['last_genre']} or ready to try a different genre? I've got tons more recommendations!"
        else:
            return "🍿 What else can I help you with? Different genre, specific actor, or maybe a movie for a particular mood?"
    
    # Specific questions
    elif any(word in message_lower for word in ['recommend', 'suggest', 'what should', 'good movie']):
        return random.choice([
            "🎬 I'd love to help! What's your mood right now? Want something to make you laugh, get your heart racing, or maybe something thought-provoking?",
            "🍿 Perfect! Tell me - are you looking for something new or classic? Light entertainment or something more serious?",
            "🎯 Great question! What genre usually catches your interest? Or describe the kind of story you're in the mood for!"
        ])
    
    # Actor/director questions
    elif any(word in message_lower for word in ['actor', 'actress', 'director', 'starring']):
        return "🌟 I love talking about talent! Which actor, actress, or director are you interested in? I can recommend their best work or similar performers you might enjoy!"
    
    # Mood-based responses
    elif any(word in message_lower for word in ['sad', 'depressed', 'down']):
        return "🤗 Feeling down? Sometimes a good movie helps! Want something uplifting to cheer you up, or prefer to embrace the mood with a beautiful drama?"
    
    elif any(word in message_lower for word in ['happy', 'excited', 'great mood']):
        return "😊 Awesome mood! Perfect time for a feel-good movie. Want something fun and energetic, or maybe a heartwarming story to match your vibe?"
    
    elif any(word in message_lower for word in ['bored', 'nothing to do']):
        return "😴 Bored? Movies are the perfect cure! Want something that'll grab you immediately with action, or prefer to get lost in a great story?"
    
    # Default conversational response
    else:
        return random.choice([
            f"🎬 That's interesting! I'm always excited to talk movies. What kind of films do you usually enjoy? Action, comedy, drama, or something else?",
            f"🍿 I love chatting about movies! Based on what you're saying, what genre sounds appealing right now?",
            f"🎭 Tell me more about what you're looking for! Are you in the mood for something specific, or want me to surprise you with a recommendation?"
        ])

# Additional helper functions for enhanced conversation
def get_follow_up_question(genre):
    """Generate follow-up questions based on genre"""
    follow_ups = {
        'comedy': "Do you prefer witty dialogue or physical comedy?",
        'action': "Want realistic action or over-the-top spectacle?",
        'horror': "How much can you handle - jump scares or psychological terror?",
        'romance': "Are you planning a date night or solo viewing?",
        'sci-fi': "Do you like hard science or space opera?",
        'drama': "Ready for something emotionally heavy?"
    }
    return follow_ups.get(genre, "Want to explore this genre more?")

def extract_preferences(message):
    """Extract user preferences from message"""
    preferences = []
    if 'new' in message.lower():
        preferences.append('recent')
    if 'classic' in message.lower():
        preferences.append('classic')
    if 'short' in message.lower():
        preferences.append('short')
    return preferences
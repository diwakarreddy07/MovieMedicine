from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os, requests, base64, io, json, random
from dotenv import load_dotenv
from openai import OpenAI
import cv2
import numpy as np
from PIL import Image
try:
    import speech_recognition as sr
except ImportError:
    sr = None
    print("⚠️ speech_recognition not available (voice search will be limited)")
from free_ai import get_free_ai_response
import bcrypt
from database import (
    get_user_by_email, get_user_by_username, get_user_by_id,
    create_user, update_user_preferences,
    add_to_watchlist, remove_from_watchlist, get_watchlist,
    add_rating, get_rating, get_all_ratings
)

load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise RuntimeError("TMDB_API_KEY missing. Put it in .env")
# Temporarily disable OpenAI due to quota exceeded
openai_client = None
print("Using mock responses (OpenAI quota exceeded)")

BASE_URL = "https://api.themoviedb.org/3"

# Map moods → TMDb genre IDs
MOOD_TO_GENRES = {
    "happy": [35, 16],          # Comedy, Animation
    "sad": [18, 10749],         # Drama, Romance
    "excited": [28, 12],        # Action, Adventure
    "relaxed": [10751, 35],     # Family, Comedy
    "adventurous": [28, 878],   # Action, Sci-Fi
    "romantic": [10749],        # Romance
    "thoughtful": [18, 36],     # Drama, History
    "nostalgic": [10751, 14],   # Family, Fantasy
    "scared": [27, 53],         # Horror, Thriller
}

# Map genre buttons → TMDb genre IDs
GENRE_IDS = {
    "action": 28,
    "comedy": 35,
    "drama": 18,
    "sci-fi": 878,
    "horror": 27,
    "romance": 10749,
}

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/signin")
def signin_page():
    return render_template("signin.html")

@app.route("/signup")
def signup_page():
    return render_template("signup.html")

@app.route("/ai-dashboard")
def ai_dashboard():
    return render_template("ai_dashboard.html")

# ✅ Movie Details (with trailer + providers + similar movies)
@app.route("/movie/<int:movie_id>")
def movie_details(movie_id):
    params = {
        "api_key": API_KEY,
        "language": "en-US",
        "append_to_response": "videos,watch/providers,similar"
    }
    details = requests.get(f"{BASE_URL}/movie/{movie_id}", params=params).json()
    return jsonify(details)

# ✅ TV Series Details (with trailer + providers + similar series)
@app.route("/tv/<int:series_id>")
def tv_details(series_id):
    params = {
        "api_key": API_KEY,
        "language": "en-US",
        "append_to_response": "videos,watch/providers,similar"
    }
    details = requests.get(f"{BASE_URL}/tv/{series_id}", params=params).json()
    return jsonify(details)

@app.route("/search")
def search():
    query = request.args.get("q")
    # Support both 'type' and 'content-type' parameters
    content_type = request.args.get("type") or request.args.get("content-type", "multi")
    
    # Handle content type values from dropdown
    if content_type in ["movies", "tv"]:
        content_type = "movie" if content_type == "movies" else "tv"
    
    if not query:
        return jsonify({"results": []})

    try:
        if content_type == "multi" or content_type == "all":
            # Search both movies and TV shows
            movie_url = f"{BASE_URL}/search/movie?api_key={API_KEY}&query={query}"
            tv_url = f"{BASE_URL}/search/tv?api_key={API_KEY}&query={query}"
            
            movie_response = requests.get(movie_url, timeout=10)
            tv_response = requests.get(tv_url, timeout=10)
            
            combined_results = []
            if movie_response.status_code == 200:
                movie_data = movie_response.json()
                for movie in movie_data.get("results", []):
                    movie["type"] = "movie"
                    combined_results.append(movie)
            
            if tv_response.status_code == 200:
                tv_data = tv_response.json()
                for show in tv_data.get("results", []):
                    show["type"] = "tv"
                    show["title"] = show.get("name", "")
                    show["release_date"] = show.get("first_air_date", "")
                    combined_results.append(show)
            
            return jsonify({"results": combined_results})
        else:
            endpoint = "movie" if content_type == "movie" else "tv"
            url = f"{BASE_URL}/search/{endpoint}?api_key={API_KEY}&query={query}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                # Add type to results
                for item in data.get("results", []):
                    item["type"] = content_type
                    if content_type == "tv":
                        item["title"] = item.get("name", "")
                        item["release_date"] = item.get("first_air_date", "")
                return jsonify(data)
            else:
                return jsonify({"error": "Failed to fetch from TMDb"}), response.status_code
    
    except requests.RequestException as e:
        return jsonify({"error": f"Request failed: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Search error: {str(e)}"}), 500

@app.route("/api/content")
def content_by_mood_or_genre():
    mood = request.args.get("mood")
    genre = request.args.get("genre")
    content_type = request.args.get("type", "movie")  # movie or tv
    page = int(request.args.get("page", 1))

    params = {
        "api_key": API_KEY,
        "include_adult": "false",
        "sort_by": "popularity.desc",
        "language": "en-US",
        "vote_count.gte": 100,
        "page": page,
    }

    if mood:
        genres = MOOD_TO_GENRES.get(mood.lower(), [35])
        params["with_genres"] = ",".join(map(str, genres))
        if mood.lower() == "nostalgic":
            if content_type == "movie":
                params["primary_release_date.lte"] = "2000-12-31"
            else:
                params["first_air_date.lte"] = "2000-12-31"
    elif genre and genre.lower() != "all":
        genres = [GENRE_IDS.get(genre.lower(), 35)]
        params["with_genres"] = ",".join(map(str, genres))

    endpoint = "movie" if content_type == "movie" else "tv"
    r = requests.get(f"{BASE_URL}/discover/{endpoint}", params=params, timeout=15)
    r.raise_for_status()
    data = r.json()

    def to_card(m):
        poster = m.get("poster_path")
        return {
            "id": m.get("id"),
            "title": m.get("title") or m.get("name"),
            "overview": m.get("overview") or "",
            "poster": f"https://image.tmdb.org/t/p/w500{poster}" if poster else "",
            "year": (m.get("release_date") or m.get("first_air_date") or "N/A")[:4],
            "rating": m.get("vote_average", 0),
            "type": content_type
        }

    return jsonify({
        "page": data.get("page"),
        "total_pages": data.get("total_pages"),
        "results": [to_card(m) for m in data.get("results", [])]
    })

# Keep old endpoint for backward compatibility
@app.route("/api/movies")
def movies_by_mood_or_genre():
    return content_by_mood_or_genre()

# ✅ AI CHATBOT
@app.route("/api/chat", methods=["POST"])
def ai_chat():
    data = request.get_json()
    user_message = data.get("message", "")
    
    # If no OpenAI key, use free AI alternative
    if not openai_client:
        ai_response = get_free_ai_response(user_message)
        return jsonify({"response": ai_response})
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a movie expert AI assistant. Help users find movies, discuss films, and provide recommendations. Be conversational and helpful."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=200
        )
        return jsonify({"response": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ AI MOOD DETECTION
@app.route("/api/detect-mood", methods=["POST"])
def detect_mood():
    try:
        data = request.get_json()
        image_data = data.get("image", "")
        
        if not image_data:
            return jsonify({"error": "No image data provided"}), 400
        
        # Decode base64 image
        try:
            image_bytes = base64.b64decode(image_data.split(',')[1])
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return jsonify({"error": "Invalid image format"}), 400
                
        except Exception as img_error:
            return jsonify({"error": "Failed to decode image"}), 400
        
        # Real-time facial emotion detection
        mood, confidence = analyze_facial_emotion(img)
        
        if mood:
            return jsonify({
                "mood": mood,
                "confidence": confidence,
                "message": f"Detected {mood} emotion with {int(confidence*100)}% confidence"
            })
        else:
            return jsonify({"error": "No face detected in image"}), 400
            
    except Exception as e:
        print(f"Mood detection error: {str(e)}")
        return jsonify({"error": "Mood detection failed. Please try again."}), 500

def analyze_facial_emotion(img):
    try:
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            return None, 0
        
        face = faces[0]
        x, y, w, h = face
        face_roi = gray[y:y+h, x:x+w]
        
        # Simple smile detection
        smiles = smile_cascade.detectMultiScale(face_roi, 1.8, 20)
        
        # Basic brightness analysis
        brightness = np.mean(face_roi)
        
        # Simple emotion mapping
        if len(smiles) > 0:
            if brightness > 100:
                return 'excited', 0.85
            else:
                return 'happy', 0.80
        elif brightness < 70:
            return 'sad', 0.75
        elif brightness > 130:
            return 'excited', 0.70
        else:
            emotions = ['relaxed', 'thoughtful', 'romantic']
            return random.choice(emotions), 0.72
            
    except Exception as e:
        print(f"Analysis error: {str(e)}")
        return random.choice(['happy', 'relaxed', 'thoughtful']), 0.65

# ✅ VOICE SEARCH
@app.route("/api/voice-search", methods=["POST"])
def voice_search():
    try:
        # This would handle audio file upload and convert to text
        # For demo, return sample response
        return jsonify({"transcript": "Find me a comedy movie with Will Smith"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ AI MOVIE MATCHER
@app.route("/api/ai-match", methods=["POST"])
def ai_movie_matcher():
    data = request.get_json()
    description = data.get("description", "").lower()
    
    # Free AI movie matching using keywords
    movies = []
    
    if any(word in description for word in ['funny', 'comedy', 'laugh']):
        movies = ["The Grand Budapest Hotel", "Superbad", "Knives Out", "What We Do in the Shadows"]
    elif any(word in description for word in ['action', 'fight', 'explosion']):
        movies = ["Mad Max: Fury Road", "John Wick", "Mission: Impossible", "The Matrix"]
    elif any(word in description for word in ['scary', 'horror', 'thriller']):
        movies = ["Get Out", "Hereditary", "A Quiet Place", "The Shining"]
    elif any(word in description for word in ['love', 'romance', 'romantic']):
        movies = ["Before Sunrise", "La La Land", "The Princess Bride", "Her"]
    elif any(word in description for word in ['space', 'sci-fi', 'future']):
        movies = ["Blade Runner 2049", "Arrival", "Interstellar", "Ex Machina"]
    elif any(word in description for word in ['drama', 'emotional', 'deep']):
        movies = ["Parasite", "Moonlight", "Manchester by the Sea", "Room"]
    else:
        movies = ["The Shawshank Redemption", "Pulp Fiction", "The Dark Knight", "Forrest Gump"]
    
    return jsonify({"movies": movies})

# ✅ AI SYNOPSIS GENERATOR
@app.route("/api/generate-synopsis", methods=["POST"])
def generate_synopsis():
    data = request.get_json()
    movie_title = data.get("title", "")
    style = data.get("style", "creative")
    
    # Free synopsis generation
    if style == "funny":
        synopsis = f"In this hilarious reimagining of {movie_title}, everything goes wonderfully wrong! Expect unexpected comedy, witty dialogue, and characters who definitely didn't read the original script."
    elif style == "dark":
        synopsis = f"A darker take on {movie_title} where shadows lurk in every corner and nothing is as it seems. This psychological thriller will keep you guessing until the very end."
    else:
        synopsis = f"An innovative retelling of {movie_title} that explores new dimensions of the story. With fresh perspectives and creative twists, this version brings something entirely new to the beloved tale."
    
    return jsonify({"synopsis": synopsis})

# ✅ MOVIE MASHUP GENERATOR
@app.route("/api/movie-mashup", methods=["POST"])
def movie_mashup():
    data = request.get_json()
    movie1 = data.get("movie1", "")
    movie2 = data.get("movie2", "")
    
    mashup_templates = [
        f"What if {movie1} met {movie2}? Imagine the characters from {movie1} finding themselves in the world of {movie2}, creating an epic crossover adventure!",
        f"A thrilling mashup: {movie1} + {movie2} = The story follows the plot of {movie1} but with the visual style and atmosphere of {movie2}.",
        f"Genre-bending fusion: Take the main character from {movie1}, put them in the setting of {movie2}, and watch the magic happen!",
        f"Ultimate crossover: {movie1} meets {movie2} in a parallel universe where both stories collide in unexpected ways!"
    ]
    
    mashup = random.choice(mashup_templates)
    return jsonify({"mashup": mashup})

# ✅ MOVIE SUCCESS PREDICTOR
@app.route("/api/predict-success", methods=["POST"])
def predict_success():
    data = request.get_json()
    genre = data.get("genre", "action")
    budget = data.get("budget_range", "medium")
    cast = data.get("cast_popularity", "medium")
    
    # Simple algorithm for success prediction
    base_scores = {
        "action": 65, "comedy": 60, "drama": 55, "horror": 70, "sci-fi": 62
    }
    
    budget_multipliers = {
        "low": 0.8, "medium": 1.0, "high": 1.2
    }
    
    cast_multipliers = {
        "low": 0.7, "medium": 1.0, "high": 1.3
    }
    
    base_score = base_scores.get(genre, 60)
    budget_mult = budget_multipliers.get(budget, 1.0)
    cast_mult = cast_multipliers.get(cast, 1.0)
    
    # Add some randomness
    random_factor = random.uniform(0.9, 1.1)
    
    final_score = int(base_score * budget_mult * cast_mult * random_factor)
    final_score = min(95, max(25, final_score))  # Keep between 25-95%
    
    return jsonify({"success_probability": final_score})

# ✅ SIGN UP ENDPOINT
@app.route("/api/signup", methods=["POST"])
def signup():
    try:
        data = request.get_json()
        username = data.get("username", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        preferences = data.get("preferences", {})
        
        # Validation
        if not username or not email or not password:
            return jsonify({"error": "All fields are required"}), 400
        
        if len(username) < 3:
            return jsonify({"error": "Username must be at least 3 characters"}), 400
        
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        
        # Check if user already exists
        if get_user_by_email(email):
            return jsonify({"error": "Email already registered"}), 400
        
        if get_user_by_username(username):
            return jsonify({"error": "Username already taken"}), 400
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user
        user_id = create_user(username, email, password_hash, preferences)
        
        if user_id:
            # Set session
            session['signed_in'] = True
            session['user_id'] = user_id
            session['username'] = username
            session['email'] = email
            
            return jsonify({
                "success": True,
                "message": "Account created successfully",
                "user": {
                    "id": user_id,
                    "username": username,
                    "email": email
                }
            })
        else:
            return jsonify({"error": "Failed to create account"}), 500
            
    except Exception as e:
        print(f"Signup error: {str(e)}")
        return jsonify({"error": "An error occurred during registration"}), 500

# ✅ SIGN IN ENDPOINT
@app.route("/api/signin", methods=["POST"])
def signin():
    try:
        data = request.get_json()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        remember_me = data.get("remember_me", False)
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
        
        # Get user from database
        user = get_user_by_email(email)
        
        if not user:
            return jsonify({"error": "Invalid email or password"}), 401
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return jsonify({"error": "Invalid email or password"}), 401
        
        # Set session
        session['signed_in'] = True
        session['user_id'] = str(user['_id'])
        session['username'] = user['username']
        session['email'] = user['email']
        
        # Set permanent session if remember me
        if remember_me:
            session.permanent = True
        
        return jsonify({
            "success": True,
            "message": "Sign in successful",
            "user": {
                "id": str(user['_id']),
                "username": user['username'],
                "email": user['email'],
                "preferences": user.get('preferences', {})
            }
        })
        
    except Exception as e:
        print(f"Signin error: {str(e)}")
        return jsonify({"error": "An error occurred during sign in"}), 500

# ✅ SIGN OUT ENDPOINT
@app.route("/api/signout", methods=["POST"])
def signout():
    session.clear()
    return jsonify({"success": True, "message": "Signed out successfully"})

# ✅ GET CURRENT USER
@app.route("/api/user", methods=["GET"])
def get_current_user():
    if not session.get('signed_in'):
        return jsonify({"error": "Not authenticated"}), 401
    
    user_id = session.get('user_id')
    user = get_user_by_id(user_id)
    
    if not user:
        session.clear()
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "user": {
            "id": str(user['_id']),
            "username": user['username'],
            "email": user['email'],
            "preferences": user.get('preferences', {})
        }
    })

@app.route("/api/preferences", methods=["GET", "POST"])
def user_preferences():
    if not session.get('signed_in'):
        return jsonify({"error": "Not authenticated"}), 401
    
    user_id = session.get('user_id')
    
    if request.method == "POST":
        data = request.get_json()
        preferences = data.get("preferences", {})
        
        # Update preferences in database
        if update_user_preferences(user_id, preferences):
            session['preferences'] = preferences
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Failed to update preferences"}), 500
    else:
        # Get preferences from database
        user = get_user_by_id(user_id)
        if user:
            preferences = user.get('preferences', {})
            return jsonify({
                "genres": preferences.get("genres", ["action", "comedy", "drama"]),
                "mood_preferences": preferences.get("mood_preferences", ["happy", "excited"]),
                "content_types": preferences.get("content_types", ["movies", "series"])
            })
        else:
            return jsonify({"error": "User not found"}), 404

# ✅ WATCHLIST ENDPOINTS
@app.route("/api/watchlist", methods=["GET", "POST", "DELETE"])
def watchlist():
    if not session.get('signed_in'):
        return jsonify({"error": "Not authenticated"}), 401
    
    user_id = session.get('user_id')
    
    if request.method == "GET":
        # Get user's watchlist
        watchlist_items = get_watchlist(user_id)
        return jsonify({"watchlist": watchlist_items})
    
    elif request.method == "POST":
        # Add to watchlist
        data = request.get_json()
        tmdb_id = data.get("tmdb_id")
        content_type = data.get("content_type", "movie")
        title = data.get("title", "")
        poster_path = data.get("poster_path", "")
        
        if not tmdb_id:
            return jsonify({"error": "tmdb_id is required"}), 400
        
        if add_to_watchlist(user_id, tmdb_id, content_type, title, poster_path):
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Failed to add to watchlist"}), 500
    
    elif request.method == "DELETE":
        # Remove from watchlist
        data = request.get_json()
        tmdb_id = data.get("tmdb_id")
        content_type = data.get("content_type", "movie")
        
        if not tmdb_id:
            return jsonify({"error": "tmdb_id is required"}), 400
        
        if remove_from_watchlist(user_id, tmdb_id, content_type):
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Failed to remove from watchlist"}), 500

# ✅ RATINGS ENDPOINTS
@app.route("/api/ratings", methods=["GET", "POST"])
def ratings():
    if not session.get('signed_in'):
        return jsonify({"error": "Not authenticated"}), 401
    
    user_id = session.get('user_id')
    
    if request.method == "GET":
        # Get user's ratings
        tmdb_id = request.args.get("tmdb_id")
        content_type = request.args.get("content_type", "movie")
        
        if tmdb_id:
            rating = get_rating(user_id, tmdb_id, content_type)
            if rating:
                return jsonify({
                    "rating": rating.get("rating"),
                    "review": rating.get("review", ""),
                    "created_date": rating.get("created_date").isoformat() if rating.get("created_date") else None
                })
            else:
                return jsonify({"rating": None})
        else:
            # Get all ratings
            ratings_list = get_all_ratings(user_id)
            # Convert datetime to string for JSON serialization
            for rating in ratings_list:
                if rating.get("created_date"):
                    rating["created_date"] = rating["created_date"].isoformat()
            return jsonify({"ratings": ratings_list})
    
    elif request.method == "POST":
        # Save rating
        data = request.get_json()
        tmdb_id = data.get("tmdb_id")
        content_type = data.get("content_type", "movie")
        rating = data.get("rating")
        review = data.get("review", "")
        
        if not tmdb_id:
            return jsonify({"error": "tmdb_id is required"}), 400
        
        if not rating or rating < 1 or rating > 10:
            return jsonify({"error": "Rating must be between 1 and 10"}), 400
        
        if add_rating(user_id, tmdb_id, content_type, rating, review):
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Failed to save rating"}), 500

if __name__ == "__main__":
    app.run(debug=True)
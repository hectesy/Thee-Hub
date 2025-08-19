import streamlit as st
import random
import requests
import datetime
import base64
from gtts import gTTS
import io
import tempfile
import os
import time
if "show_scramble_feedback" not in st.session_state:
    st.session_state.show_scramble_feedback = False

if "scramble_feedback" not in st.session_state:
    st.session_state.scramble_feedback = ""

if "scramble_feedback_type" not in st.session_state:
    st.session_state.scramble_feedback_type = ""

if "word_to_scramble" not in st.session_state:
    st.session_state.word_to_scramble = ""

if "scrambled_word" not in st.session_state:
    st.session_state.scrambled_word = ""

if "revealed_answer" not in st.session_state:
    st.session_state.revealed_answer = ""
# --- Page Setup ---
st.set_page_config(page_title="Fun Hub", page_icon="🎯", layout="centered")

# --- Configuration ---
class Config:
    """Configuration class for API keys and settings"""
    GEMINI_API_KEY = "AIzaSyAnX4k7FjX1AxNWShZa_LqosieO7KyD8mk"  # Move to environment variable
    GEMINI_MODEL = "gemini-2.5-flash-preview-05-20"
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# --- Session State Initialization ---
def init_session_state():
    """Initialize all session state variables with proper error handling"""
    defaults = {
        "score": 0,
        "streak": 0,
        "badges": [],
        "current_number": random.randint(1, 100),
        "custom_bg_color": "#d6e4f0",
        "score_text_color": "#ff6600",
        "button_bg_color": "#007bff",
        "font_family": "sans-serif",
        "font_size": "28px",
        "header_emoji": "🎯",
        "subheader_emoji": "🎮",
        "padding": "20px",
        "word_to_scramble": "",
        "scrambled_word": "",
        "translated_text": "",
        "story_text": "Your story will appear here...",
        "revealed_answer": "",
        "daily_word": "",
        "daily_word_meaning": "",
        "science_fact_with_image": {},
        "refresh_counter": 0,
        "feedback_message": "",
        "feedback_type": "",
        "show_feedback": False,
        "last_request_time": 0,
        "api_request_count": 0,
        "speed_round_start_time": None,
        "speed_round_score": 0,
        "speed_round_time_left": 60,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --- Rate Limiting ---
def check_rate_limit():
    """Simple rate limiting to prevent API abuse"""
    import time
    current_time = time.time()
    
    if current_time - st.session_state.last_request_time < 2:  # 2 second cooldown
        st.warning("Please wait a moment before making another request.")
        return False
    
    if st.session_state.api_request_count > 50:  # Daily limit
        st.error("API request limit reached for today. Please try again tomorrow.")
        return False
        
    return True

# --- Error Handling Decorator ---
def handle_api_errors(func):
    """Decorator for consistent API error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.ConnectionError:
            st.error("🌐 Connection error. Please check your internet connection.")
        except requests.exceptions.Timeout:
            st.error("⏰ Request timed out. Please try again.")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                st.error("⚠️ API rate limit exceeded. Please wait before trying again.")
            else:
                st.error(f"❌ API error: {e.response.status_code}")
        except KeyError:
            st.error("❌ Invalid API response format.")
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")
    return wrapper

# --- Custom CSS Styling (Improved) ---
def apply_custom_css():
    """Apply custom CSS based on current session state"""
    bg_color = st.session_state.custom_bg_color
    
    # Background color transition for feedback
    if st.session_state.show_feedback:
        if st.session_state.feedback_type == "correct":
            bg_color = "#90EE90"  # Light green
        elif st.session_state.feedback_type == "wrong":
            bg_color = "#FFB6C1"  # Light red
    
    st.markdown(f"""
        <style>
            .stApp {{
                background: linear-gradient(135deg, {bg_color} 0%, {bg_color}cc 100%) !important;
                transition: all 0.8s ease;
            }}
            
            .main {{
                background-color: transparent !important;
                padding: {st.session_state.padding};
                font-family: {st.session_state.font_family};
                transition: all 0.8s ease;
            }}
            
            .stButton > button {{
                font-size: 18px !important;
                padding: 12px 24px;
                border-radius: 25px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
                border: none;
                cursor: pointer;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                color: white !important;
                background: linear-gradient(135deg, {st.session_state.button_bg_color} 0%, {st.session_state.button_bg_color}cc 100%) !important;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            
            .stButton > button:hover {{
                transform: translateY(-3px) scale(1.02);
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
            }}
            
            .stButton > button:active {{
                transform: translateY(-1px) scale(0.98);
            }}
            
            .badge {{
                display: inline-block;
                background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
                padding: 8px 16px;
                margin: 5px;
                border-radius: 20px;
                font-weight: bold;
                box-shadow: 0 4px 10px rgba(255, 215, 0, 0.3);
                color: #333;
                border: 2px solid #ffed4e;
                animation: shimmer 2s infinite;
            }}
            
            @keyframes shimmer {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.8; }}
            }}
            
            .score {{
                color: {st.session_state.score_text_color};
                font-size: 28px;
                font-weight: bold;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                background: linear-gradient(45deg, {st.session_state.score_text_color}, {st.session_state.score_text_color}80);
                -webkit-background-clip: text;
                background-clip: text;
            }}
            
            .daily-word-card {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 25px;
                border-radius: 20px;
                margin: 15px 0;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                border: 1px solid rgba(255,255,255,0.2);
                backdrop-filter: blur(10px);
            }}
            
            .daily-word-title {{
                font-size: 28px;
                font-weight: bold;
                margin-bottom: 15px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }}
            
            .daily-word-meaning {{
                font-size: 18px;
                opacity: 0.95;
                line-height: 1.6;
            }}
            
            .feedback-message {{
                font-size: 32px;
                font-weight: bold;
                text-align: center;
                padding: 25px;
                border-radius: 20px;
                margin: 20px 0;
                animation: feedbackPulse 1.5s ease-in-out;
                box-shadow: 0 8px 25px rgba(0,0,0,0.2);
            }}
            
            .correct-feedback {{
                background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                color: white;
                border: 3px solid #155724;
            }}
            
            .wrong-feedback {{
                background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%);
                color: white;
                border: 3px solid #721c24;
            }}
            
            @keyframes feedbackPulse {{
                0%, 100% {{ transform: scale(1); opacity: 1; }}
                25% {{ transform: scale(1.05); opacity: 0.9; }}
                50% {{ transform: scale(1.1); opacity: 0.8; }}
                75% {{ transform: scale(1.05); opacity: 0.9; }}
            }}
            
            #drawing-board-container {{
                border: 3px solid #ddd;
                border-radius: 15px;
                background: white;
                position: relative;
                margin: 15px 0;
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
                overflow: hidden;
            }}
            
            #drawing-canvas {{
                width: 100%;
                height: 400px;
                cursor: crosshair;
                background: white;
                display: block;
            }}
            
            .stTabs [data-baseweb="tab-list"] {{
                gap: 8px;
            }}
            
            .stTabs [data-baseweb="tab"] {{
                height: 50px;
                padding: 0px 20px;
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                color: #333;
                font-weight: 600;
            }}
            
            .stTabs [aria-selected="true"] {{
                background: linear-gradient(135deg, {st.session_state.button_bg_color} 0%, {st.session_state.button_bg_color}cc 100%);
                color: white;
            }}
            
            .stNumberInput > div > div > input {{
                border-radius: 10px;
                border: 2px solid #ddd;
                padding: 10px;
                font-size: 16px;
                transition: all 0.3s ease;
            }}
            
            .stNumberInput > div > div > input:focus {{
                border-color: {st.session_state.button_bg_color};
                box-shadow: 0 0 10px rgba(0, 123, 255, 0.3);
            }}
            
            .stTextInput > div > div > input {{
                border-radius: 10px;
                border: 2px solid #ddd;
                padding: 10px;
                font-size: 16px;
                transition: all 0.3s ease;
            }}
            
            .stTextInput > div > div > input:focus {{
                border-color: {st.session_state.button_bg_color};
                box-shadow: 0 0 10px rgba(0, 123, 255, 0.3);
            }}
            
            .stSelectbox > div > div {{
                border-radius: 10px;
                border: 2px solid #ddd;
                transition: all 0.3s ease;
            }}
            
            .stSelectbox > div > div:focus-within {{
                border-color: {st.session_state.button_bg_color};
                box-shadow: 0 0 10px rgba(0, 123, 255, 0.3);
            }}
        </style>
    """, unsafe_allow_html=True)

# Apply CSS styling
apply_custom_css()

# --- Helper Functions (Improved) ---
def get_new_science_fact_with_image():
    """Returns a random science fact and a placeholder image URL."""
    FACTS_WITH_IMAGES = [
        {"fact": "The Earth's core is as hot as the surface of the sun (about 5,700°C).", "image": "https://placehold.co/600x400/FF5733/ffffff?text=Earth's+Core"},
        {"fact": "A single lightning bolt contains enough energy to toast 100,000 slices of bread.", "image": "https://placehold.co/600x400/FFD700/000000?text=Lightning+Bolt"},
        {"fact": "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly edible.", "image": "https://placehold.co/600x400/F4D03F/000000?text=Ancient+Honey"},
        {"fact": "Octopuses have three hearts and blue blood.", "image": "https://placehold.co/600x400/8E44AD/ffffff?text=Octopus+Hearts"},
        {"fact": "A group of flamingos is called a 'flamboyance'.", "image": "https://placehold.co/600x400/E91E63/ffffff?text=Flamboyance"},
        {"fact": "Bananas are berries, but strawberries aren't!", "image": "https://placehold.co/600x400/FFEB3B/000000?text=Banana+Berry"},
        {"fact": "A day on Venus is longer than its year.", "image": "https://placehold.co/600x400/FFA726/000000?text=Venus+Day"},
        {"fact": "The human brain uses about 20% of the body's total energy.", "image": "https://placehold.co/600x400/9C27B0/ffffff?text=Brain+Power"}
    ]
    st.session_state.science_fact_with_image = random.choice(FACTS_WITH_IMAGES)

if not st.session_state.science_fact_with_image:
    get_new_science_fact_with_image()

def check_answer(user_choice, number):
    """Checks the user's answer with improved feedback."""
    correct = (number % 2 == 0 and user_choice == "Even") or (number % 2 != 0 and user_choice == "Odd")
    
    if correct:
        st.session_state.score += 1
        if st.session_state.score % 5 == 0:
            st.session_state.streak += 1
        
        # Varied feedback messages
        correct_messages = [
            "✅ Correct! Excellent work!",
            "🎉 Perfect! You're on fire!",
            "⭐ Outstanding! Keep it up!",
            "🏆 Brilliant! Well done!",
            "💯 Amazing! You nailed it!"
        ]
        st.session_state.feedback_message = random.choice(correct_messages)
        st.session_state.feedback_type = "correct"
    else:
        st.session_state.streak = 0
        
        # Varied incorrect messages
        wrong_messages = [
            "❌ Not quite! Try again!",
            "🤔 Oops! Give it another shot!",
            "💭 Close! Think about it again!",
            "🎯 Keep trying! You've got this!",
            "🔄 Almost there! One more try!"
        ]
        st.session_state.feedback_message = random.choice(wrong_messages)
        st.session_state.feedback_type = "wrong"
    
    st.session_state.show_feedback = True
    return correct

def award_badges():
    """Awards badges based on score milestones with improved logic."""
    BADGE_RULES = {
        "First Try! 🏅": 1,
        "Getting Started! 🌟": 5,
        "Double Digits! ✨": 10,
        "Quarter Century! 🎊": 25,
        "Even Pro! 🏆": 50,
        "Century Club! 💎": 100,
        "Odd Overlord! 👑": 200
    }
    
    new_badges = []
    for badge, score_needed in BADGE_RULES.items():
        if st.session_state.score >= score_needed and badge not in st.session_state.badges:
            st.session_state.badges.append(badge)
            new_badges.append(badge)
    
    # Show celebration for new badges
    if new_badges:
        st.balloons()
        for badge in new_badges:
            st.success(f"🎉 Badge Unlocked: {badge}!")

def next_number():
    """Generates a new random number for the game."""
    st.session_state.current_number = random.randint(1, 100)
    st.session_state.show_feedback = False

def reset_game():
    """Resets the game state, including score, streak, and badges."""
    if st.session_state.score > 0:
        st.info(f"Final Score: {st.session_state.score} points with {st.session_state.streak} streak!")
    
    st.session_state.score = 0
    st.session_state.streak = 0
    st.session_state.badges = []
    st.session_state.current_number = random.randint(1, 100)
    st.session_state.show_feedback = False

def randomize_design():
    """Generates a new random design for the app with better color combinations."""
    # Better color palette
    colors = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
        "#DDA0DD", "#98D8C8", "#F7DC6F", "#AED6F1", "#A9DFBF"
    ]
    
    st.session_state.custom_bg_color = random.choice(colors)
    st.session_state.score_text_color = random.choice(["#2C3E50", "#8E44AD", "#E74C3C", "#F39C12", "#27AE60"])
    st.session_state.button_bg_color = random.choice(["#3498DB", "#9B59B6", "#E67E22", "#1ABC9C", "#E74C3C"])
    
    FONTS = ["sans-serif", "Georgia, serif", "Monaco, monospace", "Trebuchet MS, cursive"]
    FONT_SIZES = ["24px", "28px", "32px"]
    st.session_state.font_family = random.choice(FONTS)
    st.session_state.font_size = random.choice(FONT_SIZES)
    
    EMOJIS = ["🎯", "✨", "🚀", "🎉", "🔥", "💯", "🎲", "⭐", "🌟", "💫"]
    st.session_state.header_emoji = random.choice(EMOJIS)
    SUBHEADER_EMOJIS = ["🎮", "💡", "🧠", "🤔", "💻", "🎲", "⚡", "🎨"]
    st.session_state.subheader_emoji = random.choice(SUBHEADER_EMOJIS)
    
    st.session_state.refresh_counter += 1

def get_new_scrambled_word():
    """Selects and scrambles a new word with better word selection."""
    WORDS = [
        "python", "streamlit", "computer", "challenge", "programming",
        "keyboard", "monitor", "application", "developer", "interface",
        "random", "function", "variable", "database", "network",
        "algorithm", "framework", "library", "internet", "browser",
        "scramble", "dictionary", "language", "translate", "pronounce",
        "creative", "solution", "problem", "science", "mathematics"
    ]
    
    # Ensure we get a different word
    available_words = [w for w in WORDS if w != st.session_state.word_to_scramble]
    word = random.choice(available_words) if available_words else random.choice(WORDS)
    
    # Better scrambling - ensure it's actually scrambled
    scrambled = word
    attempts = 0
    while scrambled == word and attempts < 10:
        scrambled = ''.join(random.sample(word, len(word)))
        attempts += 1
        
    st.session_state.word_to_scramble = word
    st.session_state.scrambled_word = scrambled

def get_daily_word():
    """Gets today's daily word with improved word selection."""
    DAILY_WORDS = [
        {"word": "serendipity", "meaning": "The pleasant surprise of finding something good while looking for something else"},
        {"word": "ephemeral", "meaning": "Lasting for a very short time; here one moment, gone the next"},
        {"word": "petrichor", "meaning": "The lovely, earthy smell that comes after rain"},
        {"word": "wanderlust", "meaning": "A strong, irresistible urge to travel and explore the world"},
        {"word": "mellifluous", "meaning": "Sweet-sounding; flowing like honey when spoken"},
        {"word": "solitude", "meaning": "Peaceful time alone; being by yourself by choice"},
        {"word": "eloquence", "meaning": "The art of speaking or writing beautifully and persuasively"},
        {"word": "resilience", "meaning": "The amazing ability to bounce back from tough times"},
        {"word": "curiosity", "meaning": "The driving force that makes us want to learn and discover new things"},
        {"word": "perseverance", "meaning": "Never giving up, even when things get really difficult"},
        {"word": "innovation", "meaning": "Creating new and better ways of doing things"},
        {"word": "gratitude", "meaning": "The warm feeling of being thankful for what we have"}
    ]
    
    # Use a more complex algorithm for daily word selection
    today = datetime.date.today()
    seed = (today.day * today.month * today.year) % len(DAILY_WORDS)
    daily_entry = DAILY_WORDS[seed]
    
    st.session_state.daily_word = daily_entry["word"]
    st.session_state.daily_word_meaning = daily_entry["meaning"]

@handle_api_errors
def translate_text(text, target_lang):
    """Translates text using the Gemini API with improved error handling."""
    if not text.strip():
        st.warning("Please enter some text to translate.")
        return

    if not check_rate_limit():
        return

    with st.spinner("Translating..."):
        chat_history = [{
            "role": "user",
            "parts": [{
                "text": f"Translate the following text to {target_lang}. Only provide the translation, nothing else: '{text}'"
            }]
        }]
        
        payload = {
            "contents": chat_history,
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 1000,
            }
        }
        
        api_url = f"{Config.BASE_URL}/{Config.GEMINI_MODEL}:generateContent?key={Config.GEMINI_API_KEY}"
        
        response = requests.post(
            api_url, 
            json=payload,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        result = response.json()
        
        if 'candidates' in result and len(result['candidates']) > 0:
            translated_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
            st.session_state.translated_text = translated_text
            st.session_state.last_request_time = time.time()
            st.session_state.api_request_count += 1
            st.success("Translation complete!")
        else:
            st.error("Could not translate the text. Please try again.")

def create_tts_audio(text, lang='en-au'):
    """Create TTS audio using gTTS with improved error handling."""
    if not text.strip():
        return None
        
    try:
        # Limit text length for TTS
        if len(text) > 500:
            text = text[:500] + "..."
            
        tts = gTTS(text=text, lang=lang, slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        audio_bytes = audio_buffer.read()
        audio_base64 = base64.b64encode(audio_bytes).decode()
        return audio_base64
        
    except Exception as e:
        st.error(f"Error creating audio: {str(e)}")
        return None

def display_audio_player(text, lang='en'):
    """Create and display TTS audio player with better styling."""
    if not text.strip():
        st.warning("No text to pronounce.")
        return
        
    audio_base64 = create_tts_audio(text, lang)
    if audio_base64:
        audio_html = f"""
        <div style="margin: 15px 0; padding: 15px; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 10px; border: 2px solid #dee2e6;">
            <p style="margin: 0 0 10px 0; font-weight: 600; color: #495057;">🔊 Audio Player:</p>
            <audio controls style="width: 100%; height: 40px;">
                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                Your browser does not support the audio element.
            </audio>
        </div>
        """
        st.markdown(audio_html, unsafe_allow_html=True)
    else:
        st.error("Could not generate audio. Please try again.")

@handle_api_errors
def generate_story(prompt):
    """Generates a story using the Gemini API with improved prompting."""
    if not prompt.strip():
        st.warning("Please enter a prompt to generate a story.")
        return

    if not check_rate_limit():
        return

    with st.spinner("Generating your story... this may take a moment."):
        chat_history = [{
            "role": "user",
            "parts": [{
                "text": f"""Write a captivating and creative short story (approximately 300-400 words) based on this prompt: "{prompt}"

Requirements:
- Clear beginning, middle, and end
- Engaging characters and dialogue
- Vivid descriptions
- Appropriate for all ages
- Include a meaningful message or lesson

Story prompt: {prompt}"""
            }]
        }]

        payload = {
            "contents": chat_history,
            "generationConfig": {
                "temperature": 0.8,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2000,
            }
        }
        
        api_url = f"{Config.BASE_URL}/{Config.GEMINI_MODEL}:generateContent?key={Config.GEMINI_API_KEY}"
        
        response = requests.post(
            api_url, 
            json=payload,
            timeout=15,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        result = response.json()
        
        if 'candidates' in result and len(result['candidates']) > 0:
            story = result['candidates'][0]['content']['parts'][0]['text'].strip()
            st.session_state.story_text = story
            st.session_state.last_request_time = time.time()
            st.session_state.api_request_count += 1
            st.success("Story generation complete!")
        else:
            st.error("Could not generate a story. Please try a different prompt.")
            st.session_state.story_text = "Failed to generate a story. Please try again."

# --- Settings Sidebar (Improved) ---
with st.sidebar:
    st.header("🎨 Customization")
    
    # Color pickers with better labels
    st.session_state.custom_bg_color = st.color_picker(
        "Background Color", 
        st.session_state.custom_bg_color,
        help="Choose your favorite background color"
    )
    
    st.session_state.score_text_color = st.color_picker(
        "Score Text Color", 
        st.session_state.score_text_color,
        help="Color for score display"
    )
    
    st.session_state.button_bg_color = st.color_picker(
        "Button Color", 
        st.session_state.button_bg_color,
        help="Color for all buttons"
    )

    if st.button("🎲 Randomize Design", help="Get a completely new random theme!"):
        randomize_design()
        st.rerun()

    st.markdown("---")
    
    # Game Statistics
    st.markdown("### 📊 Game Stats")
    st.metric("High Score", st.session_state.score, help="Your current score")
    st.metric("Current Streak", st.session_state.streak, help="Consecutive correct answers (every 5 points)")
    st.metric("Badges Earned", len(st.session_state.badges), help="Achievement badges collected")
    
    # Progress bar
    next_badge_score = next((score for badge, score in [
        ("First Try! 🏅", 1), ("Getting Started! 🌟", 5), ("Double Digits! ✨", 10), 
        ("Quarter Century! 🎊", 25), ("Even Pro! 🏆", 50), ("Century Club! 💎", 100), ("Odd Overlord! 👑", 200)
    ] if st.session_state.score < score), 200)
    
    if st.session_state.score < next_badge_score:
        progress = st.session_state.score / next_badge_score
        st.progress(progress, text=f"Progress to next badge: {st.session_state.score}/{next_badge_score}")

# --- Main Header (Improved) ---
st.markdown(f"""
<div style="text-align: center; padding: 20px 0;">
    <h1 style="font-size: 48px; margin: 0; background: linear-gradient(45deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; color: transparent;">
        {st.session_state.header_emoji}  Fun Hub
    </h1>
    <p style="font-size: 20px; color: #666; margin: 10px 0 0 0;">
        Welcome to your interactive learning playground! 🎉
    </p>
</div>
""", unsafe_allow_html=True)
# --- Tabbed Layout ---
tab1, tab2, tab3 = st.tabs(["🧮 Math ", "📚 Language", "🔬 Science"])

# --- Math Games Tab ---
with tab1:
    mode = st.radio(
        "Choose a Math game:",
        ["Classic Checker", "Challenge Game", "Speed Round", "Simple Calculator","Unit Conversions"],
        key="math_game_radio" 
    )
    if mode == "Classic Checker":
        st.subheader(f"{st.session_state.subheader_emoji} Classic Even or Odd Checker")
        num = st.number_input("Enter a number:", step=1, key="checker_input")
        if st.button("Check", key="check_button"):
            if num % 2 == 0:
                st.success(f"{num} is Even! 🎉")
            else:
                st.warning(f"{num} is Odd! 🤔")
                
    elif mode == "Challenge Game":
        st.subheader(f"{st.session_state.subheader_emoji} Challenge Game")
        st.write("Test your skills, collect badges, and keep your streak alive!")
        
        # Score display
        st.markdown(f"<div class='score'>Score: {st.session_state.score} | 🔥 Streak: {st.session_state.streak}</div>", unsafe_allow_html=True)
        
        # Show feedback if available
        if st.session_state.show_feedback:
            feedback_class = "correct-feedback" if st.session_state.feedback_type == "correct" else "wrong-feedback"
            st.markdown(f"<div class='feedback-message {feedback_class}'>{st.session_state.feedback_message}</div>", unsafe_allow_html=True)
        
        # Badges display
        if st.session_state.badges:
            st.write("🏆 **Your Badges:**")
            st.markdown("".join([f"<span class='badge'>{b}</span>" for b in st.session_state.badges]), unsafe_allow_html=True)
        
        st.markdown("---")
        st.header(f"Is this number Even or Odd? **{st.session_state.current_number}**")
        st.markdown("---")
        
        # Answer buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Even", key="even_button"):
                check_answer("Even", st.session_state.current_number)
                award_badges()
                st.session_state.current_number = random.randint(1, 100)
                st.rerun()
        with col2:
            if st.button("Odd", key="odd_button"):
                check_answer("Odd", st.session_state.current_number)
                award_badges()
                st.session_state.current_number = random.randint(1, 100)
                st.rerun()
        
        st.markdown("---")
        
        # Control buttons
        col3, col4 = st.columns(2)
        with col3:
            if st.button("➡ Next", key="next_number_button"):
                next_number()
                st.rerun()
        with col4:
            if st.button("🔄 Reset Game", key="reset_game_button"):
                reset_game()
                st.rerun()
    elif mode == "Speed Round":
        st.subheader("⚡ Speed Round: Even or Odd")
        st.write("How many can you get in 60 seconds?")

        if st.session_state.speed_round_start_time is None:
            if st.button("Start Speed Round", key="start_speed_round"):
                st.session_state.speed_round_start_time = time.time()
                st.session_state.speed_round_score = 0
                st.session_state.speed_round_time_left = 60
                st.session_state.current_number = random.randint(1, 100)
                st.rerun()
        else:
            time_elapsed = time.time() - st.session_state.speed_round_start_time
            time_left = max(0, 60 - time_elapsed)
            st.session_state.speed_round_time_left = int(time_left)

            if st.session_state.speed_round_time_left > 0:
                st.metric("Time Left", f"{st.session_state.speed_round_time_left}s")
                st.metric("Score", st.session_state.speed_round_score)
                st.header(f"Is this number Even or Odd? **{st.session_state.current_number}**")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Even", key="speed_even"):
                        if st.session_state.current_number % 2 == 0:
                            st.session_state.speed_round_score += 1
                            st.success("✅ Correct!")
                        else:
                            st.error("❌ Wrong!")
                        st.session_state.current_number = random.randint(1, 100)
                        st.rerun()
                with col2:
                    if st.button("Odd", key="speed_odd"):
                        if st.session_state.current_number % 2 != 0:
                            st.session_state.speed_round_score += 1
                            st.success("✅ Correct!")
                        else:
                            st.error("❌ Wrong!")
                        st.session_state.current_number = random.randint(1, 100)
                        st.rerun()
                time.sleep(1)
                st.rerun()
            else:
                st.success(f"Time's up! Your final score is: {st.session_state.speed_round_score} 🎉")
                st.session_state.speed_round_start_time = None
                if st.button("Play Again?", key="play_again_speed_round"):
                    st.session_state.speed_round_score = 0
                    st.session_state.speed_round_time_left = 60
                    st.session_state.speed_round_start_time = time.time()
                    st.session_state.current_number = random.randint(1, 100)
                    st.rerun()
    elif mode == "Simple Calculator":
        st.subheader("➕ Simple Calculator")
        st.write("Perform basic arithmetic operations.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            num1 = st.number_input("First number", value=0.0, step=0.1, key="calc_num1")
        with col2:
            operation = st.selectbox("Operation", ["+", "-", "*", "/"], key="calc_op")
        with col3:
            num2 = st.number_input("Second number", value=0.0, step=0.1, key="calc_num2")

        if st.button("Calculate", key="calculate_button"):
            result = 0
            try:
                if operation == "+":
                    result = num1 + num2
                elif operation == "-":
                    result = num1 - num2
                elif operation == "*":
                    result = num1 * num2
                elif operation == "/":
                    if num2 == 0:
                        st.error("❌ Cannot divide by zero!")
                        result = "Error"
                    else:
                        result = num1 / num2
                
                if result != "Error":
                    st.success(f"✅ Result: {num1} {operation} {num2} = {result}")
                    
                    # Check if result is even or odd (for integers)
                    if isinstance(result, (int, float)) and result.is_integer():
                        even_odd = "even" if int(result) % 2 == 0 else "odd"
                        st.info(f"🎯 Fun fact: {int(result)} is an {even_odd} number!")
                        
            except Exception as e:
                st.error(f"❌ An error occurred: {e}")
    elif mode == "Unit Conversions":
        st.subheader("Convert")
        st.write("unit to unit.")
        
        col5, col6 = st.columns(2)
# --- TIME CONVERSION ---
        with col5:
            st.subheader("⏱️ Time Conversion")

        time_value = st.number_input("Enter a value:", min_value=0.0, step=1.0, key="time_input")
        time_unit = st.selectbox("Select unit:", ["Hours", "Minutes", "Seconds"], key="time_unit")

        if st.button("Convert Time", key="convert_time"):
            if time_unit == "Hours":
                minutes = time_value * 60
                seconds = time_value * 3600
                st.success(f"{time_value} hours = {minutes} minutes = {seconds} seconds")
            elif time_unit == "Minutes":
                hours = time_value / 60
                seconds = time_value * 60
                st.success(f"{time_value} minutes = {hours:.2f} hours = {seconds} seconds")
        else:  # Seconds
            minutes = time_value / 60
            hours = time_value / 3600
            st.success(f"{time_value} seconds = {minutes:.2f} minutes = {hours:.2f} hours")

# --- WEIGHT CONVERSION ---
        with col6:
            st.subheader("⚖️ Weight Conversion")

        weight_value = st.number_input("Enter weight:", min_value=0.0, step=0.1, key="weight_input")
        weight_unit = st.selectbox("Select unit:", ["Kilograms", "Grams", "Pounds (lbs)"], key="weight_unit")

        if st.button("Convert Weight", key="convert_weight"):
            if weight_unit == "Kilograms":
                grams = weight_value * 1000
                pounds = weight_value * 2.20462
            st.success(f"{weight_value} kg = {grams} g = {pounds:.2f} lbs")
        elif weight_unit == "Grams":
            kilograms = weight_value / 1000
            pounds = weight_value * 0.00220462
            st.success(f"{weight_value} g = {kilograms:.2f} kg = {pounds:.2f} lbs")
        else:  # Pounds
            kilograms = weight_value / 2.20462
            grams = weight_value * 453.592
            st.success(f"{weight_value} lbs = {kilograms:.2f} kg = {grams:.2f} g")

# --- Language Tab ---
with tab2:
    lang_tab1, lang_tab2, lang_tab3, lang_tab4 = st.tabs(["Word Scramble", "Daily Word", "Translator", "Story Maker"])

    with lang_tab1:
        st.subheader("💡 Word Scramble")
        st.write("Unscramble the word below! Try to guess the word!")
        
        if not st.session_state.word_to_scramble:
            get_new_scrambled_word()
            
        if st.session_state.scrambled_word:
            st.header(f"Scrambled word: **{st.session_state.scrambled_word}**")
            
            # Show feedback if available
            if st.session_state.show_scramble_feedback:
                feedback_class = "correct-feedback" if st.session_state.scramble_feedback_type == "correct" else "wrong-feedback"
                st.markdown(f"<div class='feedback-message {feedback_class}'>{st.session_state.scramble_feedback}</div>", unsafe_allow_html=True)
            
            user_guess = st.text_input("Your guess:", key="word_guess").strip()
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Check Guess", key="check_guess_button"):
                    if user_guess.lower() == st.session_state.word_to_scramble.lower():
                        st.session_state.scramble_feedback = "✅ Correct! Excellent work! 🎉"
                        st.session_state.scramble_feedback_type = "correct"
                        st.session_state.show_scramble_feedback = True
                        # Auto-generate new word after a short delay
                        time.sleep(2)
                        get_new_scrambled_word()
                        st.session_state.revealed_answer = ""
                        st.rerun()
                    elif user_guess:  # Only show error if user actually entered something
                        st.session_state.scramble_feedback = f"❌ '{user_guess}' is not correct. Try again!"
                        st.session_state.scramble_feedback_type = "wrong"
                        st.session_state.show_scramble_feedback = True
                        st.rerun()
                        
            with col2:
                if st.button("Reveal Answer", key="reveal_button"):
                    st.session_state.revealed_answer = st.session_state.word_to_scramble
                    st.session_state.scramble_feedback = f"💡 The answer was: {st.session_state.word_to_scramble.upper()}"
                    st.session_state.scramble_feedback_type = "neutral"
                    st.session_state.show_scramble_feedback = True
                    st.rerun()
            
            if st.session_state.revealed_answer:
                st.info(f"The answer is: **{st.session_state.revealed_answer.upper()}**")
                if st.button("🎲 Get New Word", key="new_word_after_reveal"):
                    get_new_scrambled_word()
                    st.session_state.revealed_answer = ""
                    st.rerun()


    with lang_tab2:
        st.subheader("📅 Daily Word")
        st.write("Learn a new word every day!")
        
        if not st.session_state.daily_word:
            get_daily_word()
        
        if st.button("🔄 Get Today's Word", key="get_daily_word_button"):
            get_daily_word()
            st.rerun()
        
        if st.session_state.daily_word:
            st.markdown(f"""
            <div class="daily-word-card">
                <div class="daily-word-title">📚 Word of the Day: {st.session_state.daily_word.upper()}</div>
                <div class="daily-word-meaning">📖 Meaning: {st.session_state.daily_word_meaning}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Pronunciation section
            st.subheader("🔊 Pronunciation")
            st.write(f"Click below to hear how to pronounce: **{st.session_state.daily_word}**")
            
            if st.button(f"🔊 Pronounce '{st.session_state.daily_word}'", key="pronounce_daily_word"):
                display_audio_player(st.session_state.daily_word, 'en')

    with lang_tab3:
        st.subheader("🌐 Translator")
        st.write("Translate text to different languages!")
        
        text_to_translate = st.text_area("Enter text to translate:", key="translator_text_area")
        languages = ["Spanish", "French", "German", "Japanese", "English", "Italian", "Portuguese", "Russian", "Korean", "Chinese"]
        target_language = st.selectbox("Select a language:", languages, key="language_selectbox")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🌐 Translate", key="translate_button"):
                translate_text(text_to_translate, target_language)
        with col2:
            if st.button("🔊 Pronounce Original", key="pronounce_original"):
                if text_to_translate:
                    display_audio_player(text_to_translate, 'en')
                else:
                    st.warning("Please enter text to pronounce.")
        
        if st.session_state.translated_text:
            st.subheader("Translated Text:")
            st.info(st.session_state.translated_text)
            
            if st.button("🔊 Pronounce Translation", key="pronounce_translation"):
                lang_codes = {
                    "Spanish": "es", "French": "fr", "German": "de", "Japanese": "ja",
                    "English": "en", "Italian": "it", "Portuguese": "pt", "Russian": "ru",
                    "Korean": "ko", "Chinese": "zh"
                }
                lang_code = lang_codes.get(target_language, 'en')
                display_audio_player(st.session_state.translated_text, lang_code)

    with lang_tab4:
        st.subheader("✍️ Story Maker")
        st.write("Enter a prompt and let the AI generate a story!")
        story_prompt = st.text_input("Enter a prompt for your story:", key="story_prompt_input")
        if st.button("Generate Story", key="generate_story_button"):
            generate_story(story_prompt)
        
        st.subheader("Generated Story:")
        st.write(st.session_state.story_text)
# --- Science Tab ---
with tab3:
    science_tab1, science_tab2 = st.tabs(["Fun Facts", "World Flags"])
    
    # --- Science Facts ---
    with science_tab1:
        st.subheader("🔬 Science Facts")
        st.write("Click the button to learn a new and interesting science fact!")

        if st.button("Get a New Fact", key="new_fact_button"):
            get_new_science_fact_with_image()
            st.rerun()
        
        if st.session_state.science_fact_with_image:
            st.info(st.session_state.science_fact_with_image["fact"])
            st.image(
                st.session_state.science_fact_with_image["image"], 
                caption="Science Fact Illustration", 
                use_column_width=True
            )

    # --- World Flags Quiz ---
    with science_tab2:
        st.subheader("🌍 World Flag Quiz")

        flags = {
            "Nigeria": "https://flagcdn.com/w320/ng.png",
            "Japan": "https://flagcdn.com/w320/jp.png",
            "France": "https://flagcdn.com/w320/fr.png",
            "Brazil": "https://flagcdn.com/w320/br.png",
            "Canada": "https://flagcdn.com/w320/ca.png",
            "India": "https://flagcdn.com/w320/in.png",
            "Germany": "https://flagcdn.com/w320/de.png",
            "Italy": "https://flagcdn.com/w320/it.png",
            "South Africa": "https://flagcdn.com/w320/za.png",
            "United States": "https://flagcdn.com/w320/us.png",
            "Argentina": "https://flagcdn.com/w320/ar.png",
            "Australia": "https://flagcdn.com/w320/au.png",
            "Bangladesh": "https://flagcdn.com/w320/bd.png",
            "Belgium": "https://flagcdn.com/w320/be.png",
"Chile": "https://flagcdn.com/w320/cl.png",
"China": "https://flagcdn.com/w320/cn.png",
"Colombia": "https://flagcdn.com/w320/co.png",
"Denmark": "https://flagcdn.com/w320/dk.png",
"Egypt": "https://flagcdn.com/w320/eg.png",
"Ethiopia": "https://flagcdn.com/w320/et.png",
"Finland": "https://flagcdn.com/w320/fi.png",
"Ghana": "https://flagcdn.com/w320/gh.png",
"Greece": "https://flagcdn.com/w320/gr.png",
"Hungary": "https://flagcdn.com/w320/hu.png",
"Iceland": "https://flagcdn.com/w320/is.png",
"Indonesia": "https://flagcdn.com/w320/id.png",
    "Iran": "https://flagcdn.com/w320/ir.png",
    "Iraq": "https://flagcdn.com/w320/iq.png",
    "Israel": "https://flagcdn.com/w320/il.png",
    "Jamaica": "https://flagcdn.com/w320/jm.png",
    "Kenya": "https://flagcdn.com/w320/ke.png",
    "Lebanon": "https://flagcdn.com/w320/lb.png",
    "Malaysia": "https://flagcdn.com/w320/my.png",
    "Mexico": "https://flagcdn.com/w320/mx.png",
    "Morocco": "https://flagcdn.com/w320/ma.png",
    "Nepal": "https://flagcdn.com/w320/np.png",
    "Netherlands": "https://flagcdn.com/w320/nl.png",
    "New Zealand": "https://flagcdn.com/w320/nz.png",
    "Norway": "https://flagcdn.com/w320/no.png",
    "Pakistan": "https://flagcdn.com/w320/pk.png",
    "Peru": "https://flagcdn.com/w320/pe.png",
    "Philippines": "https://flagcdn.com/w320/ph.png",
    "Poland": "https://flagcdn.com/w320/pl.png",
    "Portugal": "https://flagcdn.com/w320/pt.png",
    "Qatar": "https://flagcdn.com/w320/qa.png",
    "Russia": "https://flagcdn.com/w320/ru.png",
    "Saudi Arabia": "https://flagcdn.com/w320/sa.png",
    "Singapore": "https://flagcdn.com/w320/sg.png",
    "South Korea": "https://flagcdn.com/w320/kr.png",
    "Spain": "https://flagcdn.com/w320/es.png",
    "Sri Lanka": "https://flagcdn.com/w320/lk.png",
    "Sweden": "https://flagcdn.com/w320/se.png",
    "Switzerland": "https://flagcdn.com/w320/ch.png",
    "Thailand": "https://flagcdn.com/w320/th.png",
    "Turkey": "https://flagcdn.com/w320/tr.png",
    "Ukraine": "https://flagcdn.com/w320/ua.png",
    "United Arab Emirates": "https://flagcdn.com/w320/ae.png",
    "United Kingdom": "https://flagcdn.com/w320/gb.png",
    "Venezuela": "https://flagcdn.com/w320/ve.png",
    "Vietnam": "https://flagcdn.com/w320/vn.png"
        }

        # --- Session State ---
        if "flag_score" not in st.session_state:
            st.session_state.flag_score = 0
        if "current_flag" not in st.session_state:
            st.session_state.current_flag = random.choice(list(flags.keys()))
        if "answered" not in st.session_state:
            st.session_state.answered = False

        # Show Flag
        st.image(flags[st.session_state.current_flag], width=300)
        st.write("Which country does this flag belong to? No abrreivations🚫(USA)")

        answer = st.text_input("Your answer:").strip()

        if st.button("Submit"):
            if answer.lower() == st.session_state.current_flag.lower():
                st.success("✅ Correct!")
                st.session_state.flag_score += 1
            else:
                st.error(f"❌ Wrong! The correct answer was {st.session_state.current_flag}")
            st.session_state.answered = True

        if st.session_state.answered:
            if st.button("Next Flag"):
                st.session_state.current_flag = random.choice(list(flags.keys()))
                st.session_state.answered = False

        st.write(f"**Score:** {st.session_state.flag_score}")





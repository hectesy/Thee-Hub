
import streamlit as st
import random
import requests
import datetime
import base64
from gtts import gTTS
import io
import tempfile
import os

# --- Page Setup ---
st.set_page_config(page_title="The Hub", page_icon="🎯", layout="centered")

# --- Session State Initialization ---
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        "score": 0,
        "streak": 0,
        "badges": [],
        "feedback_color": "#d6e4f0",
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
        "user_guess_input": "",
        "translated_text": "",
        "story_text": "Your story will appear here...",
        "revealed_answer": "",
        "daily_word": "",
        "daily_word_meaning": "",
        "science_fact_with_image": {},
        "refresh_counter": 0,
        "feedback_message": "",
        "feedback_type": "",
        "show_feedback": False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --- Custom CSS Styling ---
def apply_custom_css():
    """Apply custom CSS based on current session state"""
    bg_color = st.session_state.custom_bg_color
    if st.session_state.show_feedback:
        if st.session_state.feedback_type == "correct":
            bg_color = "#90EE90"  # Light green
        elif st.session_state.feedback_type == "wrong":
            bg_color = "#FFB6C1"  # Light red
    
    st.markdown(f"""
        <style>
            .stApp {{
                background-color: {bg_color} !important;
                transition: background-color 0.8s ease;
            }}
            .main {{
                background-color: {bg_color} !important;
                padding: {st.session_state.padding};
                font-family: {st.session_state.font_family};
                transition: background-color 0.8s ease;
            }}
            .stApp > div:first-child {{
                background-color: {bg_color} !important;
                transition: background-color 0.8s ease;
            }}
            .block-container {{
                background-color: {bg_color} !important;
                transition: background-color 0.8s ease;
            }}
            .stButton>button {{
                font-size: 20px !important;
                padding: 15px 30px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                border: none;
                cursor: pointer;
                transition: transform 0.2s ease, background-color 0.2s ease;
                color: #f5f5f5;
                background-color: {st.session_state.button_bg_color} !important;
            }}
            .stButton>button:hover {{
                transform: translateY(-2px);
            }}
            .badge {{
                display: inline-block;
                background-color: gold;
                padding: 5px 10px;
                margin: 5px;
                border-radius: 10px;
                font-weight: bold;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }}
            .score {{
                color: {st.session_state.score_text_color};
                font-size: 24px;
                font-weight: bold;
            }}
            .daily-word-card {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 15px;
                margin: 10px 0;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            }}
            .daily-word-title {{
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .daily-word-meaning {{
                font-size: 16px;
                opacity: 0.9;
            }}
            .feedback-message {{
                font-size: 28px;
                font-weight: bold;
                text-align: center;
                padding: 20px;
                border-radius: 10px;
                margin: 15px 0;
                animation: pulse 1s ease-in-out;
            }}
            .correct-feedback {{
                background-color: #28a745;
                color: white;
                border: 3px solid #155724;
            }}
            .wrong-feedback {{
                background-color: #dc3545;
                color: white;
                border: 3px solid #721c24;
            }}
            @keyframes pulse {{
                0% {{ transform: scale(1); opacity: 1; }}
                50% {{ transform: scale(1.1); opacity: 0.8; }}
                100% {{ transform: scale(1); opacity: 1; }}
            }}
            #drawing-board-container {{
                border: 2px solid #ccc;
                border-radius: 8px;
                background-color: white;
                position: relative;
                margin: 10px 0;
            }}
            #drawing-canvas {{
                width: 100%;
                height: 400px;
                cursor: crosshair;
                background-color: white;
                border-radius: 6px;
            }}
        </style>
    """, unsafe_allow_html=True)

# Apply CSS styling
apply_custom_css()

# --- Helper Functions ---
def get_new_science_fact_with_image():
    """Returns a random science fact and a placeholder image URL."""
    FACTS_WITH_IMAGES = [
        {"fact": "The Earth's core is as hot as the surface of the sun.", "image": "https://placehold.co/600x400/FF5733/ffffff?text=Earth's+Core"},
        {"fact": "A single lightning bolt contains enough energy to toast 100,000 slices of bread.", "image": "https://placehold.co/600x400/000000/ffffff?text=Lightning+Bolt"},
        {"fact": "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly edible.", "image": "https://placehold.co/600x400/F4D03F/000000?text=Ancient+Honey"},
        {"fact": "It's impossible for most people to lick their own elbow.", "image": "https://placehold.co/600x400/A9CCE3/000000?text=Try+It!"},
        {"fact": "Octopuses have three hearts and blue blood.", "image": "https://placehold.co/600x400/8E44AD/ffffff?text=Octopus+Hearts"},
        {"fact": "A group of flamingos is called a 'flamboyance'.", "image": "https://placehold.co/600x400/E91E63/ffffff?text=Flamboyance"}
    ]
    st.session_state.science_fact_with_image = random.choice(FACTS_WITH_IMAGES)

if not st.session_state.science_fact_with_image:
    get_new_science_fact_with_image()

def check_answer(user_choice, number):
    """Checks the user's answer, updates score and streak, and shows feedback with background flash."""
    correct = (number % 2 == 0 and user_choice == "Even") or (number % 2 != 0 and user_choice == "Odd")
    
    if correct:
        st.session_state.score += 1
        if st.session_state.score % 5 == 0:
            st.session_state.streak += 1
        st.session_state.feedback_message = "✅ Correct! Great job!"
        st.session_state.feedback_type = "correct"
    else:
        st.session_state.streak = 0
        st.session_state.feedback_message = "❌ Wrong! Try again!"
        st.session_state.feedback_type = "wrong"
    
    st.session_state.show_feedback = True
    return correct

def award_badges():
    """Awards badges based on score milestones."""
    BADGE_RULES = {
        "First Try! 🏅": 1,
        "Double Digits! ✨": 10,
        "Even Pro! 🏆": 20,
        "Odd Overlord! 👑": 50
    }
    for badge, score_needed in BADGE_RULES.items():
        if st.session_state.score >= score_needed and badge not in st.session_state.badges:
            st.session_state.badges.append(badge)
            st.balloons()
            st.success(f"🎉 Badge Unlocked: {badge}!")

def next_number():
    """Generates a new random number for the game."""
    st.session_state.current_number = random.randint(1, 100)
    st.session_state.show_feedback = False

def reset_game():
    """Resets the game state, including score, streak, and badges."""
    st.session_state.score = 0
    st.session_state.streak = 0
    st.session_state.badges = []
    st.session_state.current_number = random.randint(1, 100)
    st.session_state.show_feedback = False

def randomize_design():
    """Generates a new random design for the app."""
    st.session_state.custom_bg_color = f"#{random.randint(0x333333, 0xFFFFFF):06x}"
    st.session_state.score_text_color = f"#{random.randint(0x000000, 0xFFFFFF):06x}"
    st.session_state.button_bg_color = f"#{random.randint(0x000000, 0xBBBBBB):06x}"
    
    FONTS = ["sans-serif", "serif", "monospace", "cursive", "fantasy"]
    FONT_SIZES = ["24px", "28px", "32px", "36px"]
    st.session_state.font_family = random.choice(FONTS)
    st.session_state.font_size = random.choice(FONT_SIZES)
    
    EMOJIS = ["🎯", "✨", "🚀", "🎉", "🔥", "💯", "🎲"]
    st.session_state.header_emoji = random.choice(EMOJIS)
    SUBHEADER_EMOJIS = ["🎮", "💡", "🧠", "🤔", "💻"]
    st.session_state.subheader_emoji = random.choice(SUBHEADER_EMOJIS)
    
    PADDINGS = ["10px", "20px", "30px", "40px"]
    st.session_state.padding = random.choice(PADDINGS)
    
    st.session_state.refresh_counter += 1

def get_new_scrambled_word():
    """Selects and scrambles a new word, ensuring it's different from the previous one."""
    WORDS = [
        "python", "streamlit", "computer", "challenge", "programming",
        "keyboard", "monitor", "application", "developer", "interface",
        "random", "function", "variable", "database", "network",
        "algorithm", "framework", "library", "internet", "browser",
        "scramble", "dictionary", "language", "translate", "pronounce"
    ]
    
    previous_word = st.session_state.word_to_scramble
    word = previous_word
    while word == previous_word and len(WORDS) > 1:
        word = random.choice(WORDS)
        
    scrambled = ''.join(random.sample(word, len(word)))
    st.session_state.word_to_scramble = word
    st.session_state.scrambled_word = scrambled

def get_daily_word():
    """Gets today's daily word and its meaning."""
    DAILY_WORDS = [
        {"word": "serendipity", "meaning": "The occurrence and development of events by chance in a happy or beneficial way"},
        {"word": "ephemeral", "meaning": "Lasting for a very short time; transitory"},
        {"word": "petrichor", "meaning": "The pleasant smell of earth after rain"},
        {"word": "wanderlust", "meaning": "A strong desire to travel and explore the world"},
        {"word": "mellifluous", "meaning": "Sweet or musical; pleasant to hear"},
        {"word": "solitude", "meaning": "The state or situation of being alone"},
        {"word": "eloquence", "meaning": "Fluent or persuasive speaking or writing"},
        {"word": "resilience", "meaning": "The ability to recover quickly from difficulties"},
        {"word": "curiosity", "meaning": "A strong desire to know or learn something"},
        {"word": "perseverance", "meaning": "Persistence in doing something despite difficulty"},
        {"word": "innovation", "meaning": "The action or process of innovating; new methods or ideas"},
        {"word": "gratitude", "meaning": "The quality of being thankful; readiness to show appreciation"}
    ]
    
    today = datetime.date.today()
    word_index = (today.day + today.month + today.year) % len(DAILY_WORDS)
    daily_entry = DAILY_WORDS[word_index]
    
    st.session_state.daily_word = daily_entry["word"]
    st.session_state.daily_word_meaning = daily_entry["meaning"]

def translate_text(text, target_lang):
    """Translates text using the Gemini API."""
    try:
        if not text:
            st.warning("Please enter some text to translate.")
            return

        with st.spinner("Translating..."):
            chatHistory = [{ "role": "user", "parts": [{ "text": f"Translate this text to {target_lang}: {text}" }] }]
            payload = { "contents": chatHistory }
            apiKey = "AIzaSyAnX4k7FjX1AxNWShZa_LqosieO7KyD8mk"
            
            apiUrl = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={apiKey}"
            
            response = requests.post(apiUrl, json=payload)
            response.raise_for_status() 
            result = response.json()
            
            if 'candidates' in result and len(result['candidates']) > 0:
                translated_text = result['candidates'][0]['content']['parts'][0]['text']
                st.session_state.translated_text = translated_text
                st.success("Translation complete!")
            else:
                st.error("Could not translate the text. Please try again.")

    except requests.exceptions.RequestException as e:
        st.error(f"Translation failed due to a network error: {e}")
    except KeyError:
        st.error("Failed to parse the API response. The response format was unexpected.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

def create_tts_audio(text, lang='en'):
    """Create TTS audio using gTTS and return as base64 string."""
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            tts.save(tmp_file.name)
            
            with open(tmp_file.name, 'rb') as audio_file:
                audio_bytes = audio_file.read()
                audio_base64 = base64.b64encode(audio_bytes).decode()
            
            os.unlink(tmp_file.name)
            
            return audio_base64
    except Exception as e:
        st.error(f"Error creating audio: {e}")
        return None

def display_audio_player(text, lang='en'):
    """Create and display TTS audio player."""
    audio_base64 = create_tts_audio(text, lang)
    if audio_base64:
        audio_html = f"""
        <audio controls style="width: 100%;">
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            Your browser does not support the audio element.
        </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)
    else:
        st.error("Could not generate audio. Please try again.")

def generate_story(prompt):
    """Generates a story using the Gemini API."""
    try:
        if not prompt:
            st.warning("Please enter a prompt to generate a story.")
            return

        with st.spinner("Generating your story... this may take a moment."):
            chatHistory = [{
                "role": "user",
                "parts": [{
                    "text": f"Write a captivating and creative short story, approximately 300 words, based on the following prompt: {prompt}. The story should have a clear beginning, middle, and end, and a compelling narrative."
                }]
            }]

            payload = {
                "contents": chatHistory,
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95
                }
            }
            apiKey = "AIzaSyAnX4k7FjX1AxNWShZa_LqosieO7KyD8mk"
                
            apiUrl = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={apiKey}"
            
            response = requests.post(apiUrl, json=payload)
            response.raise_for_status() 
            result = response.json()
            
            if 'candidates' in result and len(result['candidates']) > 0:
                story = result['candidates'][0]['content']['parts'][0]['text']
                st.session_state.story_text = story
                st.success("Story generation complete!")
            else:
                st.error("Could not generate a story. Please try a different prompt.")
                st.session_state.story_text = "Failed to generate a story. Please try again."

    except requests.exceptions.RequestException as e:
        st.error(f"Story generation failed due to a network error: {e}")
    except KeyError:
        st.error("Failed to parse the API response. The response format was unexpected.")
        st.session_state.story_text = "Failed to generate a story. Please check the API response."
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        st.session_state.story_text = "An unexpected error occurred. Please try again."

# --- Settings Sidebar ---
st.sidebar.header("🎨 Settings")
st.session_state.custom_bg_color = st.sidebar.color_picker("Pick a background color", st.session_state.custom_bg_color)
st.session_state.score_text_color = st.sidebar.color_picker("Score text color", st.session_state.score_text_color)
st.session_state.button_bg_color = st.sidebar.color_picker("Button color", st.session_state.button_bg_color)

if st.sidebar.button("🎲 Randomize Design"):
    randomize_design()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("🎮 **Game Stats:**")
st.sidebar.markdown(f"• High Score: {st.session_state.score}")
st.sidebar.markdown(f"• Current Streak: {st.session_state.streak}")
st.sidebar.markdown(f"• Badges Earned: {len(st.session_state.badges)}")

# --- Main Header ---
st.title(f"{st.session_state.header_emoji} The Hub")
st.markdown("Welcome to your interactive learning playground!")

# --- Tabbed Layout ---
tab1, tab2, tab3 = st.tabs(["🎮 Math Games", "📚 Language", "🔬 Science"])

# --- Math Games Tab ---
with tab1:
    mode = st.radio("Choose a Math game:", ["Classic Checker", "Challenge Game"], key="math_game_radio")
    
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
            
            user_guess = st.text_input("Your guess:", key="word_guess")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Check Guess", key="check_guess_button"):
                    if user_guess.lower().strip() == st.session_state.word_to_scramble.lower():
                        st.success("✅ Correct! Great job! 🎉")
                        get_new_scrambled_word()
                        st.rerun()
                    else:
                        st.error("❌ Try again!")
            with col2:
                if st.button("Reveal Answer", key="reveal_button"):
                    st.session_state.revealed_answer = st.session_state.word_to_scramble
                    st.rerun()

            if st.session_state.revealed_answer:
                st.info(f"The answer is: **{st.session_state.revealed_answer.upper()}**")
                if st.button("🎲 New Word", key="new_word_after_reveal"):
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
    st.subheader("💡 Fun Projects & Facts")
    
    st.write("Explore these ideas for your next coding, art, or craft project!")
    
    col1, col2 = st.tabs(["Fun Facts", "Projects"])

    with col1:
        st.subheader("🔬 Science Facts")
        st.write("Click the button to learn a new and interesting science fact!")
        if st.button("Get a New Fact", key="new_fact_button"):
            get_new_science_fact_with_image()
            st.rerun()
        
        if st.session_state.science_fact_with_image:
            st.info(st.session_state.science_fact_with_image["fact"])
            st.image(st.session_state.science_fact_with_image["image"], 
                     caption="Science Fact Illustration", 
                     use_container_width=True)
    
    with col2:
        st.subheader("💻 Projects")
        st.write("Find your next creative challenge!")
        
        st.markdown("""
            <div class="project-card">
                <h4>Build a Simple Web App with Streamlit</h4>
                <p>Create your own interactive app like this one! Learn the basics of Streamlit, a powerful tool for building data apps in Python.</p>
                <a href="https://www.w3schools.com/python/python_functions.asp" target="_blank" rel="noopener noreferrer">Learn More &rarr;</a>
            </div>
            <div class="project-card">
                <h4>Pixel Art with Paper & Grids</h4>
                <p>Learn the basics of digital art by creating pixel art on paper. Use graph paper and colored pencils to design simple characters or objects, like a retro video game sprite.</p>
                <a href="https://artwithtrista.com/how-to-teach-grid-drawing/" target="_blank" rel="noopener noreferrer">Instructions &rarr;</a>
            </div>
            <div class="project-card">
                <h4>Code a Text-Based Adventure Game</h4>
                <p>Challenge yourself by creating a story with code. This project involves using basic variables and conditional statements (if/else) to build a game where choices change the outcome.</p>
                <a href="https://fpsvogel.com/posts/2023/why-make-a-text-based-game" target="_blank" rel="noopener noreferrer">Guide &rarr;</a>
            </div>
            <div class="project-card">
                <h4>Build a Paper Circuit with LEDs</h4>
                <p>Combine art and electronics by creating a circuit on paper. Use copper tape, coin cell batteries, and LEDs to make a light-up greeting card or a small illuminated artwork.</p>
                <a href="hhttps://www.exploratorium.edu/tinkering/projects/paper-circuits" target="_blank" rel="noopener noreferrer">Tutorial &rarr;</a>
            </div>
        """, unsafe_allow_html=True)
# ============================================================================
# SECTION 1: IMPORTS AND INITIAL SETUP
# ============================================================================
import streamlit as st
import json
from datetime import datetime
from openai import OpenAI
import os
import sqlite3
import re  # For word counting
import tempfile  # For handling audio files
# REMOVED: from spellchecker import SpellChecker  # No longer needed

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY")))

# ============================================================================
# SECTION 2: CSS STYLING AND VISUAL DESIGN
# ============================================================================
LOGO_URL = "https://menuhunterai.com/wp-content/uploads/2026/01/logo.png"

st.markdown(f"""
<style>
    /* Fix header spacing */
    .main-header {{
        text-align: center;
        padding-top: 0.5rem;
        margin-top: -1rem;
        margin-bottom: 0.5rem;
    }}
    
    .logo-img {{
        width: 100px;
        height: 100px;
        border-radius: 50%;
        object-fit: cover;
        margin: 0 auto 0.25rem auto;
        display: block;
    }}
    
    .chapter-guidance {{
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3498db;
        margin-bottom: 1rem;
        font-size: 0.95rem;
        line-height: 1.5;
    }}
    
    .question-box {{
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #4a5568;
        margin-bottom: 1.5rem;
        font-size: 1.2rem;
        font-weight: 500;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    
    .question-counter {{
        font-size: 1.1rem;
        font-weight: bold;
        color: #2c3e50;
    }}
    
    /* Chat styling */
    .stChatMessage {{
        margin-bottom: 0.5rem !important;
    }}
    
    .user-message-container {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        width: 100%;
    }}
    
    .message-text {{
        flex: 1;
        min-width: 0;
    }}
    
    /* Remove extra margins */
    [data-testid="stAppViewContainer"] {{
        padding-top: 0.5rem !important;
    }}
    
    .ghostwriter-tag {{
        font-size: 0.8rem;
        color: #666;
        font-style: italic;
        margin-top: 0.5rem;
    }}
    
    /* Word count styling */
    .word-count-box {{
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border: 2px solid #e0e0e0;
    }}
    
    .traffic-light {{
        display: inline-block;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        margin-right: 8px;
        vertical-align: middle;
    }}
    
    .traffic-green {{
        background-color: #2ecc71;
        box-shadow: 0 0 10px rgba(46, 204, 113, 0.5);
    }}
    
    .traffic-yellow {{
        background-color: #f39c12;
        box-shadow: 0 0 10px rgba(243, 156, 18, 0.5);
    }}
    
    .traffic-red {{
        background-color: #e74c3c;
        box-shadow: 0 0 10px rgba(231, 76, 60, 0.5);
    }}
    
    /* Audio input styling */
    .audio-recording {{
        background-color: #e8f5e9;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 2px solid #4caf50;
    }}
    
    .audio-preview {{
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 8px;
        margin-top: 1rem;
        border-left: 4px solid #2196f3;
    }}
    
    .transcription-box {{
        background-color: #e8f4fc;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #2196f3;
    }}
    
    .auto-submit-notice {{
        background-color: #e8f5e9;
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #4caf50;
        font-size: 0.9rem;
    }}
    
    .spelling-suggestion {{
        background-color: #fff3cd;
        padding: 0.5rem;
        border-radius: 5px;
        margin-top: 0.25rem;
        font-size: 0.85rem;
        border-left: 3px solid #ffc107;
    }}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SECTION 3: CHAPTER DEFINITIONS AND DATA STRUCTURE
# ============================================================================
CHAPTERS = [
    {
        "id": 1,
        "title": "Childhood",
        "guidance": "Welcome to the Childhood chapter—this is where we lay the foundation of your story. Professional biographies thrive on specific, sensory-rich memories. I'm looking for the kind of details that transport readers: not just what happened, but how it felt, smelled, sounded. The 'insignificant' moments often reveal the most. Take your time—we're mining for gold here.",
        "questions": [
            "What is your earliest memory?",
            "Can you describe your family home growing up?",
            "Who were the most influential people in your early years?",
            "What was school like for you?",
            "Were there any favourite games or hobbies?",
            "Is there a moment from childhood that shaped who you are?",
            "If you could give your younger self some advice, what would it be?"
        ],
        "completed": False,
        "word_target": 800
    },
    {
        "id": 2,
        "title": "Family & Relationships",
        "guidance": "Family stories are complex ecosystems. We're not seeking perfect narratives, but authentic ones. The richest material often lives in the tensions, the unsaid things, the small rituals. My job is to help you articulate what usually goes unspoken. Think in scenes rather than summaries.",
        "questions": [
            "How would you describe your relationship with your parents?",
            "Are there any family traditions you remember fondly?",
            "What was your relationship like with siblings or close relatives?",
            "Can you share a story about a family celebration or challenge?",
            "How did your family shape your values?"
        ],
        "completed": False,
        "word_target": 700
    },
    {
        "id": 3,
        "title": "Education & Growing Up",
        "guidance": "Education isn't just about schools—it's about how you learned to navigate the world. We're interested in the hidden curriculum: what you learned about yourself, about systems, about survival and growth. Think beyond grades to transformation.",
        "questions": [
            "What were your favourite subjects at school?",
            "Did you have any memorable teachers or mentors?",
            "How did you feel about exams and studying?",
            "Were there any big turning points in your education?",
            "Did you pursue further education or training?",
            "What advice would you give about learning?"
        ],
        "completed": False,
        "word_target": 600
    }
]

# ============================================================================
# SECTION 4: DATABASE FUNCTIONS
# ============================================================================
def init_db():
    conn = sqlite3.connect('life_story.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            user_id TEXT,
            chapter_id INTEGER,
            question TEXT,
            answer TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS word_targets (
            chapter_id INTEGER PRIMARY KEY,
            word_target INTEGER DEFAULT 500
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ============================================================================
# SECTION 5: SESSION STATE INITIALIZATION
# ============================================================================
if "responses" not in st.session_state:
    st.session_state.current_chapter = 0
    st.session_state.current_question = 0
    st.session_state.responses = {}
    st.session_state.user_id = "Guest"
    st.session_state.chapter_conversations = {}
    st.session_state.editing = None
    st.session_state.edit_text = ""
    st.session_state.ghostwriter_mode = True
    st.session_state.show_speech = True
    st.session_state.speech_text = ""
    st.session_state.speech_preview = ""
    st.session_state.pending_transcription = None
    st.session_state.audio_transcribed = False
    st.session_state.show_transcription = False
    st.session_state.auto_submit_text = None
    st.session_state.spellcheck_enabled = True  # Spelling correction toggle
    
    # Initialize for each chapter
    for chapter in CHAPTERS:
        chapter_id = chapter["id"]
        st.session_state.responses[chapter_id] = {
            "title": chapter["title"],
            "questions": {},
            "summary": "",
            "completed": False,
            "word_target": chapter.get("word_target", 500)
        }
        st.session_state.chapter_conversations[chapter_id] = {}
    
    # Load word targets from database
    try:
        conn = sqlite3.connect('life_story.db')
        cursor = conn.cursor()
        cursor.execute("SELECT chapter_id, word_target FROM word_targets")
        for chapter_id, word_target in cursor.fetchall():
            if chapter_id in st.session_state.responses:
                st.session_state.responses[chapter_id]["word_target"] = word_target
        conn.close()
    except:
        pass

# ============================================================================
# SECTION 6: CORE APPLICATION FUNCTIONS
# ============================================================================
def load_user_data():
    if st.session_state.user_id == "Guest":
        return
    
    try:
        conn = sqlite3.connect('life_story.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT chapter_id, question, answer 
            FROM responses 
            WHERE user_id = ?
        """, (st.session_state.user_id,))
        
        for chapter_id, question, answer in cursor.fetchall():
            if chapter_id not in st.session_state.responses:
                continue
            st.session_state.responses[chapter_id]["questions"][question] = {
                "answer": answer,
                "timestamp": datetime.now().isoformat()
            }
        
        conn.close()
    except:
        pass

def save_response(chapter_id, question, answer):
    user_id = st.session_state.user_id
    
    if chapter_id not in st.session_state.responses:
        st.session_state.responses[chapter_id] = {
            "title": CHAPTERS[chapter_id-1]["title"],
            "questions": {},
            "summary": "",
            "completed": False,
            "word_target": CHAPTERS[chapter_id-1].get("word_target", 500)
        }
    
    st.session_state.responses[chapter_id]["questions"][question] = {
        "answer": answer,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        conn = sqlite3.connect('life_story.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO responses 
            (user_id, chapter_id, question, answer) 
            VALUES (?, ?, ?, ?)
        """, (user_id, chapter_id, question, answer))
        conn.commit()
        conn.close()
    except:
        pass

def save_word_target(chapter_id, word_target):
    try:
        conn = sqlite3.connect('life_story.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO word_targets 
            (chapter_id, word_target) 
            VALUES (?, ?)
        """, (chapter_id, word_target))
        conn.commit()
        conn.close()
    except:
        pass

def calculate_chapter_word_count(chapter_id):
    total_words = 0
    chapter_data = st.session_state.responses.get(chapter_id, {})
    conversations = st.session_state.chapter_conversations.get(chapter_id, {})
    
    for question, answer_data in chapter_data.get("questions", {}).items():
        if answer_data.get("answer"):
            total_words += len(re.findall(r'\w+', answer_data["answer"]))
    
    for question_text, conv in conversations.items():
        for msg in conv:
            if msg["role"] == "user":
                total_words += len(re.findall(r'\w+', msg["content"]))
    
    return total_words

def get_traffic_light(chapter_id):
    current_count = calculate_chapter_word_count(chapter_id)
    target = st.session_state.responses[chapter_id].get("word_target", 500)
    
    if target == 0:
        return "#2ecc71", "🟢", 100
    
    progress = (current_count / target) * 100
    
    if progress >= 100:
        return "#2ecc71", "🟢", progress
    elif progress >= 70:
        return "#f39c12", "🟡", progress
    else:
        return "#e74c3c", "🔴", progress

def clean_speech_text(text):
    if not text:
        return text
    
    text = text.strip()
    
    replacements = {
        "uh": "", "um": "", "er": "", "ah": "",
        "like, ": "", "you know, ": "", "sort of ": "", "kind of ": "",
        "  ": " "
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    if text and len(text) > 0:
        text = text[0].upper() + text[1:] if text[0].isalpha() else text
    
    if text and text[-1] not in ['.', '!', '?', ',', ';', ':']:
        text += '.'
    
    return text

# ============================================================================
# SECTION 7: SPEECH-TO-TEXT AND SPELLING FUNCTIONS
# ============================================================================
def transcribe_audio(audio_file):
    """Transcribe audio using OpenAI Whisper API"""
    try:
        # Read the audio bytes from UploadedFile object
        audio_bytes = audio_file.read()
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        # Transcribe using Whisper
        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"
            )
        
        # Clean up
        os.unlink(tmp_path)
        
        return transcript.text
        
    except Exception as e:
        st.error(f"Error transcribing audio: {str(e)}")
        return None

def check_spelling_openai(text):
    """Use OpenAI to check and fix spelling mistakes"""
    if not text or not st.session_state.spellcheck_enabled:
        return text, []
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Fix spelling and grammar mistakes in the following text. Return only the corrected text."},
                {"role": "user", "content": text}
            ],
            max_tokens=len(text) + 100,
            temperature=0.1
        )
        corrected_text = response.choices[0].message.content
        
        # Simple comparison to find changes
        if corrected_text != text:
            return corrected_text, ["AI suggested corrections available"]
        else:
            return text, []
            
    except Exception as e:
        # If OpenAI fails, return original text
        st.warning(f"Spell check unavailable: {str(e)}")
        return text, []

def auto_correct_text(text):
    """Auto-correct text using OpenAI"""
    if not text or not st.session_state.spellcheck_enabled:
        return text
    
    corrected_text, _ = check_spelling_openai(text)
    return corrected_text
# ============================================================================
# SECTION 8: GHOSTWRITER PROMPT FUNCTION
# ============================================================================
def get_system_prompt():
    current_chapter = CHAPTERS[st.session_state.current_chapter]
    current_question = current_chapter["questions"][st.session_state.current_question]
    
    if st.session_state.ghostwriter_mode:
        return f"""ROLE: You are a professional biographer and ghostwriter helping someone document their life story for a UK English-speaking audience.

CURRENT CHAPTER: {current_chapter['title']}
CURRENT QUESTION: "{current_question}"

CORE PRINCIPLES:
1. You are warm but purposeful—not fawning, not overly casual
2. You think in narrative structure and concrete detail
3. Your questions are designed to extract rich, publishable material
4. You value specificity over generality, scenes over summaries
5. You are comfortable with thoughtful pauses and depth

TONE GUIDELINES:
- Warm but professional, like an experienced journalist or established biographer
- UK English: "worktop" not "countertop", "fortnight" not "two weeks", "quite" used judiciously
- Avoid Americanisms and overly sentimental language
- Not effusive, but genuinely engaged
- Respectful persistence when responses need deepening

CONVERSATION STRUCTURE:
For each response from the user:
1. ACKNOWLEDGE WITH PURPOSE (1 sentence): Not generic praise, but recognition of what's revealing
2. PLANT A FOLLOW-UP SEED (1 sentence): Suggest why this matters for the narrative
3. ASK ONE STRATEGIC QUESTION (1 question maximum): Choose based on what's needed

QUESTION STRATEGIES BASED ON RESPONSE TYPE:
- For surface-level responses: "Let's explore the texture of that. What sensory detail remains sharpest?"
- For past events: "What did that mean then versus what it means now?"
- For relationships: "What was understood but never said?"
- For general statements: "Give me one concrete Tuesday that captures this."

CHAPTER-SPECIFIC THINKING:
- CHILDHOOD: Mine for foundational moments, sensory memories, early patterns
- FAMILY: Explore dynamics, unspoken rules, rituals
- EDUCATION: Consider both formal learning and hidden curriculum

AVOID:
- Multiple follow-up questions in one response
- Overly emotional or therapeutic language
- American colloquialisms
- Empty praise ("Amazing!", "Fascinating!")
- Rushing past rich material

EXAMPLE RESPONSE TO "I remember my grandmother's kitchen":
"Kitchens often hold family history. Let's step into that space properly. What's the first smell that comes to mind? The feel of the worktop? And crucially—what version of yourself lived in that kitchen that doesn't exist elsewhere?"

Focus: Extract material for a compelling biography. Every question should serve that purpose."""
    else:
        return f"""You are a warm, professional biographer helping document a life story.

CURRENT CHAPTER: {current_chapter['title']}
CURRENT QUESTION: "{current_question}"

Please:
1. Listen actively to their response
2. Acknowledge it warmly (1-2 sentences)
3. Ask ONE natural follow-up question if appropriate
4. Keep the conversation flowing naturally

Tone: Kind, curious, professional
Goal: Draw out authentic, detailed memories

Focus ONLY on the current question. Don't reference previous chapters."""

# ============================================================================
# SECTION 9: MAIN APP HEADER
# ============================================================================
st.set_page_config(page_title="LifeStory AI", page_icon="📖", layout="wide")

st.markdown(f"""
<div class="main-header">
    <img src="{LOGO_URL}" class="logo-img" alt="LifeStory AI Logo">
    <h2 style="margin: 0; line-height: 1.2;">LifeStory AI</h2>
    <p style="font-size: 0.9rem; color: #666; margin: 0; line-height: 1.2;">Preserve Your Legacy • Share Your Story</p>
</div>
""", unsafe_allow_html=True)

st.caption("A professional guided journey through your life story")

if st.session_state.user_id != "Guest":
    load_user_data()

# ============================================================================
# SECTION 10: SIDEBAR - USER PROFILE AND SETTINGS
# ============================================================================
with st.sidebar:
    st.header("👤 Your Profile")
    
    new_user_id = st.text_input("Your Name:", value=st.session_state.user_id)
    
    if new_user_id != st.session_state.user_id:
        st.session_state.user_id = new_user_id
        st.session_state.responses = {}
        st.session_state.chapter_conversations = {}
        st.session_state.current_chapter = 0
        st.session_state.current_question = 0
        st.session_state.editing = None
        st.session_state.edit_text = ""
        st.session_state.speech_text = ""
        st.session_state.speech_preview = ""
        st.session_state.pending_transcription = None
        st.session_state.audio_transcribed = False
        st.session_state.show_transcription = False
        st.session_state.auto_submit_text = None
        
        for chapter in CHAPTERS:
            chapter_id = chapter["id"]
            st.session_state.responses[chapter_id] = {
                "title": chapter["title"],
                "questions": {},
                "summary": "",
                "completed": False,
                "word_target": chapter.get("word_target", 500)
            }
            st.session_state.chapter_conversations[chapter_id] = {}
        
        load_user_data()
        st.rerun()
    
    st.divider()
    st.header("✍️ Interview Style")
    
    ghostwriter_mode = st.toggle(
        "Professional Ghostwriter Mode", 
        value=st.session_state.ghostwriter_mode,
        help="When enabled, the AI acts as a professional biographer using advanced interviewing techniques."
    )
    
    if ghostwriter_mode != st.session_state.ghostwriter_mode:
        st.session_state.ghostwriter_mode = ghostwriter_mode
        st.rerun()
    
    show_speech = st.toggle(
        "Show Speech Input",
        value=st.session_state.show_speech,
        help="Show voice recording interface with automatic transcription"
    )
    
    if show_speech != st.session_state.show_speech:
        st.session_state.show_speech = show_speech
        st.rerun()
    
    spellcheck_enabled = st.toggle(
        "Auto Spelling Check",
        value=st.session_state.spellcheck_enabled,
        help="Check and suggest spelling corrections as you type"
    )
    
    if spellcheck_enabled != st.session_state.spellcheck_enabled:
        st.session_state.spellcheck_enabled = spellcheck_enabled
        st.rerun()
    
    if st.session_state.ghostwriter_mode:
        st.success("✓ Professional mode active")
    else:
        st.info("Standard mode active")
    
    st.divider()
    
       # ============================================================================
    # SECTION 10A: SIDEBAR - WORD COUNT SETTINGS (NEW CLEARLY MARKED SECTION)
    # ============================================================================
    st.header("📊 Word Count Settings")
    
    for i, chapter in enumerate(CHAPTERS):
        chapter_id = chapter["id"]
        
        # Get current values
        target_words = st.session_state.responses[chapter_id].get("word_target", 500)
        word_count = calculate_chapter_word_count(chapter_id)
        color, emoji, progress = get_traffic_light(chapter_id)
        
        # Determine chapter status
        chapter_data = st.session_state.responses.get(chapter_id, {})
        if chapter_data.get("completed", False):
            status = "✅"
        elif i == st.session_state.current_chapter:
            status = "▶️"
        else:
            status = "●"
        
        # Chapter button
        button_text = f"{emoji} {status} Chapter {chapter['id']}: {chapter['title']}"
        
        if st.button(button_text, 
                    key=f"select_{i}",
                    use_container_width=True,
                    help=f"{word_count}/{target_words} words ({progress:.0f}%)"):
            st.session_state.current_chapter = i
            st.session_state.current_question = 0
            st.session_state.editing = None
            st.rerun()
        
        # Progress bar and word count display
        if target_words > 0:
            progress_bar = min(word_count / target_words, 1.0)
            st.progress(progress_bar)
            
            # Display with traffic light emoji
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.caption(f"{emoji} {word_count}/{target_words} words")
            with col2:
                st.caption(f"{progress:.0f}%")
            with col3:
                if st.button("✏️", key=f"edit_target_{chapter_id}", help="Edit word target"):
                    st.session_state[f"editing_target_{chapter_id}"] = True
        
        # Edit target input section
        if st.session_state.get(f"editing_target_{chapter_id}"):
            new_target = st.number_input(
                f"Target words for Chapter {chapter_id}:",
                min_value=100,
                max_value=5000,
                value=target_words,
                key=f"target_input_{chapter_id}",
                label_visibility="collapsed"
            )
            
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("💾 Save", key=f"save_target_{chapter_id}", type="primary"):
                    # Update session state - THIS IS THE SOURCE OF TRUTH
                    st.session_state.responses[chapter_id]["word_target"] = new_target
                    # Also update database
                    save_word_target(chapter_id, new_target)
                    st.session_state[f"editing_target_{chapter_id}"] = False
                    st.rerun()
            with col_cancel:
                if st.button("❌ Cancel", key=f"cancel_target_{chapter_id}"):
                    st.session_state[f"editing_target_{chapter_id}"] = False
                    st.rerun()
    
    # ============================================================================
    # SECTION 10B: SIDEBAR - NAVIGATION CONTROLS
    # ============================================================================
    st.subheader("Question Navigation")
    
    current_chapter = CHAPTERS[st.session_state.current_chapter]
    st.markdown(f'<div class="question-counter">Question {st.session_state.current_question + 1} of {len(current_chapter["questions"])}</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Previous", disabled=st.session_state.current_question == 0, key="prev_q_sidebar"):
            st.session_state.current_question = max(0, st.session_state.current_question - 1)
            st.session_state.editing = None
            st.rerun()
    
    with col2:
        if st.button("Next →", disabled=st.session_state.current_question >= len(current_chapter["questions"]) - 1, key="next_q_sidebar"):
            st.session_state.current_question = min(len(current_chapter["questions"]) - 1, st.session_state.current_question + 1)
            st.session_state.editing = None
            st.rerun()
    
    st.divider()
    st.subheader("Chapter Navigation")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Prev Chapter", disabled=st.session_state.current_chapter == 0, key="prev_chap_sidebar"):
            st.session_state.current_chapter = max(0, st.session_state.current_chapter - 1)
            st.session_state.current_question = 0
            st.session_state.editing = None
            st.rerun()
    with col2:
        if st.button("Next Chapter →", disabled=st.session_state.current_chapter >= len(CHAPTERS)-1, key="next_chap_sidebar"):
            st.session_state.current_chapter = min(len(CHAPTERS)-1, st.session_state.current_chapter + 1)
            st.session_state.current_question = 0
            st.session_state.editing = None
            st.rerun()
    
    chapter_options = [f"Chapter {c['id']}: {c['title']}" for c in CHAPTERS]
    selected_chapter = st.selectbox("Jump to chapter:", chapter_options, index=st.session_state.current_chapter)
    if chapter_options.index(selected_chapter) != st.session_state.current_chapter:
        st.session_state.current_chapter = chapter_options.index(selected_chapter)
        st.session_state.current_question = 0
        st.session_state.editing = None
        st.rerun()
    
    st.divider()
    
    # ============================================================================
    # SECTION 10C: SIDEBAR - EXPORT OPTIONS
    # ============================================================================
    st.subheader("📤 Export Options")
    
    total_answers = sum(len(ch.get("questions", {})) for ch in st.session_state.responses.values())
    st.caption(f"Total answers to export: {total_answers}")
    
    if st.button("📥 Export Current Progress", type="primary"):
        if total_answers > 0:
            # Simple export implementation
            export_data = {"chapters": {}}
            for chapter in CHAPTERS:
                chapter_id = chapter["id"]
                chapter_data = st.session_state.responses.get(chapter_id, {})
                if chapter_data.get("questions"):
                    export_data["chapters"][chapter_id] = chapter_data
            
            st.download_button(
                label="Download as JSON",
                data=json.dumps(export_data, indent=2),
                file_name=f"LifeStory_{st.session_state.user_id}.json",
                mime="application/json"
            )
        else:
            st.warning("No responses to export yet!")
    
    st.divider()
    
    # ============================================================================
    # SECTION 10D: SIDEBAR - MANAGEMENT CONTROLS
    # ============================================================================
    st.subheader("⚙️ Management")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear Chapter", type="secondary"):
            current_chapter_id = CHAPTERS[st.session_state.current_chapter]["id"]
            try:
                conn = sqlite3.connect('life_story.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM responses WHERE user_id = ? AND chapter_id = ?", 
                              (st.session_state.user_id, current_chapter_id))
                conn.commit()
                conn.close()
                st.session_state.responses[current_chapter_id]["questions"] = {}
                st.rerun()
            except:
                pass
    
    with col2:
        if st.button("Clear All", type="secondary"):
            try:
                conn = sqlite3.connect('life_story.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM responses WHERE user_id = ?", 
                              (st.session_state.user_id,))
                conn.commit()
                conn.close()
                for chapter in CHAPTERS:
                    chapter_id = chapter["id"]
                    st.session_state.responses[chapter_id]["questions"] = {}
                st.rerun()
            except:
                pass

# ============================================================================
# SECTION 11: MAIN CONTENT - CHAPTER HEADER AND WORD COUNT
# ============================================================================
current_chapter = CHAPTERS[st.session_state.current_chapter]
current_chapter_id = current_chapter["id"]
current_question_text = current_chapter["questions"][st.session_state.current_question]

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.subheader(f"Chapter {current_chapter['id']}: {current_chapter['title']}")
    
    if st.session_state.ghostwriter_mode:
        st.markdown('<p class="ghostwriter-tag">Professional Ghostwriter Mode • Advanced Interviewing</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="ghostwriter-tag">Standard Interview Mode</p>', unsafe_allow_html=True)
        
with col2:
    st.markdown(f'<div class="question-counter" style="margin-top: 1rem;">Question {st.session_state.current_question + 1} of {len(current_chapter["questions"])}</div>', unsafe_allow_html=True)
with col3:
    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        if st.button("← Prev", disabled=st.session_state.current_question == 0, key="prev_q_quick"):
            st.session_state.current_question = max(0, st.session_state.current_question - 1)
            st.session_state.editing = None
            st.rerun()
    with nav_col2:
        if st.button("Next →", disabled=st.session_state.current_question >= len(current_chapter["questions"]) - 1, key="next_q_quick"):
            st.session_state.current_question = min(len(current_chapter["questions"]) - 1, st.session_state.current_question + 1)
            st.session_state.editing = None
            st.rerun()

# WORD COUNT DISPLAY - SYNCHRONIZED WITH SIDEBAR
current_word_count = calculate_chapter_word_count(current_chapter_id)
# FIXED: Use the session state target from sidebar edits
target_words = st.session_state.responses[current_chapter_id].get("word_target", 500)
color, emoji, progress_percent = get_traffic_light(current_chapter_id)

# Calculate remaining words
remaining_words = max(0, target_words - current_word_count)
status_text = f"{remaining_words} words remaining" if remaining_words > 0 else "Target achieved!"

st.markdown(f"""
<div class="word-count-box">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
        <div>
            <h4 style="margin: 0; display: flex; align-items: center;">
                <span class="traffic-light" style="background-color: {color};"></span>
                Word Progress: {current_word_count} / {target_words}
            </h4>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem; color: #666;">
                {emoji} {progress_percent:.0f}% complete • {status_text}
            </p>
        </div>
        <div style="text-align: center;">
            <div style="font-size: 1.5rem; font-weight: bold;">{emoji}</div>
            <div style="font-size: 0.8rem; color: #666;">Status</div>
        </div>
    </div>
    <div style="margin-top: 1rem;">
        <div style="height: 12px; background-color: #e0e0e0; border-radius: 6px; overflow: hidden;">
            <div style="height: 100%; width: {min(progress_percent, 100)}%; background-color: {color}; border-radius: 6px; transition: width 0.3s ease;"></div>
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 0.5rem; font-size: 0.8rem; color: #666;">
            <span>0</span>
            <span>Target: {target_words}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Questions progress
chapter_data = st.session_state.responses.get(current_chapter_id, {})
questions_answered = len(chapter_data.get("questions", {}))
total_questions = len(current_chapter["questions"])

if total_questions > 0:
    question_progress = questions_answered / total_questions
    st.progress(min(question_progress, 1.0))
    st.caption(f"📝 Questions answered: {questions_answered}/{total_questions} ({question_progress*100:.0f}%)")

# ============================================================================
# SECTION 12: AUTOMATIC SPEECH-TO-TEXT WITH WHISPER API
# ============================================================================
if st.session_state.show_speech:
    st.markdown("### 🎤 Speak Your Answer")
    st.markdown("""
    <div class="audio-recording">
        <strong>Automatic Speech-to-Text:</strong>
        <ul style="margin: 0.5rem 0 0 1rem; padding-left: 1rem;">
            <li>Record your answer - Whisper AI will transcribe it automatically</li>
            <li>Transcription appears below for review and editing</li>
            <li>Click "Use This Answer" to add it directly to the conversation</li>
            <li>Works with any microphone in your browser</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Streamlit's built-in audio input
    audio_bytes = st.audio_input(
        "Click to record your answer:",
        key=f"audio_input_{current_chapter_id}_{st.session_state.current_question}"
    )
    
    if audio_bytes:
        # Display the recorded audio
        st.audio(audio_bytes, format="audio/wav")
        
        # Auto-transcribe using Whisper API
        if not st.session_state.audio_transcribed:
            with st.spinner("Transcribing with Whisper AI..."):
                transcribed_text = transcribe_audio(audio_bytes)
                if transcribed_text:
                    st.session_state.pending_transcription = transcribed_text
                    st.session_state.audio_transcribed = True
                    st.rerun()
    
    # Show transcribed text for editing
    if st.session_state.pending_transcription:
        st.markdown("### 📝 Transcribed Text")
        st.markdown('<div class="transcription-box">', unsafe_allow_html=True)
        
        # Text area with spell checking
        transcribed_text = st.text_area(
            "Edit your transcribed answer:",
            value=st.session_state.pending_transcription,
            height=200,
            key="transcription_edit",
            help="Edit the transcription before adding it to your story"
        )
        
        # Spelling check for transcribed text
        if transcribed_text and st.session_state.spellcheck_enabled:
            _, suggestions = check_spelling(transcribed_text)
            if suggestions:
                st.markdown('<div class="spelling-suggestion">', unsafe_allow_html=True)
                st.write("**Spelling suggestions:**")
                for wrong, correct in suggestions[:3]:  # Show top 3 suggestions
                    st.write(f"• '{wrong}' → '{correct}'")
                st.markdown('</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            if st.button("✅ Use This Answer", type="primary", use_container_width=True):
                # Auto-correct spelling if enabled
                if st.session_state.spellcheck_enabled:
                    corrected_text = auto_correct_text(transcribed_text)
                    st.session_state.auto_submit_text = corrected_text
                else:
                    st.session_state.auto_submit_text = transcribed_text
                
                st.session_state.pending_transcription = None
                st.session_state.audio_transcribed = False
                st.rerun()
        
        with col2:
            if st.button("🔄 Re-transcribe", type="secondary", use_container_width=True):
                st.session_state.audio_transcribed = False
                st.session_state.pending_transcription = None
                st.rerun()
        
        with col3:
            if st.button("❌ Cancel", type="secondary", use_container_width=True):
                st.session_state.pending_transcription = None
                st.session_state.audio_transcribed = False
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")

# ============================================================================
# SECTION 13: CONVERSATION DISPLAY WITH SPELL CHECKING
# ============================================================================
current_chapter_id = current_chapter["id"]
current_question_text = current_chapter["questions"][st.session_state.current_question]

if current_chapter_id not in st.session_state.chapter_conversations:
    st.session_state.chapter_conversations[current_chapter_id] = {}

conversation = st.session_state.chapter_conversations[current_chapter_id].get(current_question_text, [])

if not conversation:
    with st.chat_message("assistant"):
        if st.session_state.ghostwriter_mode:
            welcome_msg = f"""Let's explore this question properly: **{current_question_text}**

Take your time with this—good biographies are built from thoughtful reflection rather than quick answers.

*Current chapter word count: {current_word_count}/{target_words} words*"""
        else:
            welcome_msg = f"I'd love to hear your thoughts about this question: **{current_question_text}**"
        
        st.markdown(welcome_msg)
        conversation.append({"role": "assistant", "content": welcome_msg})
        st.session_state.chapter_conversations[current_chapter_id][current_question_text] = conversation
else:
    for i, message in enumerate(conversation):
        if message["role"] == "assistant":
            with st.chat_message("assistant"):
                st.markdown(message["content"])
        
        elif message["role"] == "user":
            is_editing = (st.session_state.editing == (current_chapter_id, current_question_text, i))
            
            with st.chat_message("user"):
                if is_editing:
                    # Edit mode with spell checking
                    new_text = st.text_area(
                        "Edit your answer:",
                        value=st.session_state.edit_text,
                        key=f"edit_area_{current_chapter_id}_{hash(current_question_text)}_{i}",
                        height=150,
                        label_visibility="collapsed"
                    )
                    
                    # Real-time spell checking while editing
                    if new_text and st.session_state.spellcheck_enabled:
                        corrected_text, suggestions = check_spelling_openai(new_text)
                        if suggestions and corrected_text != new_text:
                            st.markdown('<div class="spelling-suggestion">', unsafe_allow_html=True)
                            st.write("**Spelling/grammar suggestions available**")
                            st.write(f"*Corrected version:* {corrected_text[:200]}...")
                            if st.button("Apply Correction", key=f"apply_correction_{i}"):
                                new_text = corrected_text
                                st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)
                    
                    if new_text:
                        edit_word_count = len(re.findall(r'\w+', new_text))
                        st.caption(f"📝 Editing: {edit_word_count} words")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✓ Save", key=f"save_{current_chapter_id}_{hash(current_question_text)}_{i}", type="primary"):
                            # Auto-correct before saving if enabled
                            if st.session_state.spellcheck_enabled:
                                new_text = auto_correct_text(new_text)
                            
                            conversation[i]["content"] = new_text
                            st.session_state.chapter_conversations[current_chapter_id][current_question_text] = conversation
                            save_response(current_chapter_id, current_question_text, new_text)
                            st.session_state.editing = None
                            st.rerun()
                    with col2:
                        if st.button("✕ Cancel", key=f"cancel_{current_chapter_id}_{hash(current_question_text)}_{i}"):
                            st.session_state.editing = None
                            st.rerun()
                else:
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.markdown(message["content"])
                        word_count = len(re.findall(r'\w+', message["content"]))
                        st.caption(f"📝 {word_count} words • Click ✏️ to edit")
                    with col2:
                        if st.button("✏️", key=f"edit_{current_chapter_id}_{hash(current_question_text)}_{i}"):
                            st.session_state.editing = (current_chapter_id, current_question_text, i)
                            st.session_state.edit_text = message["content"]
                            st.rerun()

# ============================================================================
# SECTION 14: CHAT INPUT WITH AUTO-SUBMIT AND SPELL CHECKING
# ============================================================================
if st.session_state.editing is None:
    user_input = None
    
    # Check for auto-submitted text from speech
    if st.session_state.auto_submit_text:
        user_input = st.session_state.auto_submit_text
        del st.session_state.auto_submit_text
    else:
        # Regular chat input with spell checking
        chat_input_container = st.container()
        with chat_input_container:
            user_input = st.chat_input("Type your answer here...")
            
            # Show spelling suggestions above input
            if user_input and st.session_state.spellcheck_enabled:
                corrected_text, suggestions = check_spelling_openai(user_input)
                if suggestions and corrected_text != user_input:
                    st.markdown('<div class="spelling-suggestion">', unsafe_allow_html=True)
                    st.write("**Suggested correction:**")
                    st.write(f"*{corrected_text}*")
                    if st.button("Use Corrected Version", key="use_corrected"):
                        user_input = corrected_text
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
    
    if user_input:
        current_chapter_id = current_chapter["id"]
        current_question_text = current_chapter["questions"][st.session_state.current_question]
        
        if current_chapter_id not in st.session_state.chapter_conversations:
            st.session_state.chapter_conversations[current_chapter_id] = {}
        
        if current_question_text not in st.session_state.chapter_conversations[current_chapter_id]:
            st.session_state.chapter_conversations[current_chapter_id][current_question_text] = []
        
        conversation = st.session_state.chapter_conversations[current_chapter_id][current_question_text]
        
        # Auto-correct before adding to conversation
        if st.session_state.spellcheck_enabled:
            user_input = auto_correct_text(user_input)
        
        # Add user message
        conversation.append({"role": "user", "content": user_input})
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    messages_for_api = [
                        {"role": "system", "content": get_system_prompt()},
                        *conversation[-5:]
                    ]
                    
                    if st.session_state.ghostwriter_mode:
                        temperature = 0.8
                        max_tokens = 400
                    else:
                        temperature = 0.7
                        max_tokens = 300
                    
                    response = client.chat.completions.create(
                        model="gpt-4-turbo-preview",
                        messages=messages_for_api,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    
                    ai_response = response.choices[0].message.content
                    
                    # Add word count encouragement
                    updated_word_count = calculate_chapter_word_count(current_chapter_id)
                    target_words = st.session_state.responses[current_chapter_id].get("word_target", 500)
                    progress = (updated_word_count / target_words * 100) if target_words > 0 else 100
                    
                    if progress < 50:
                        ai_response += f"\n\n*Note: You're building good material here. Current chapter: {updated_word_count}/{target_words} words.*"
                    elif progress < 80:
                        ai_response += f"\n\n*Good progress on this chapter: {updated_word_count}/{target_words} words.*"
                    elif progress < 100:
                        ai_response += f"\n\n*Excellent detail! Almost at your target: {updated_word_count}/{target_words} words.*"
                    else:
                        ai_response += f"\n\n*Fantastic! You've exceeded your word target: {updated_word_count}/{target_words} words.*"
                    
                    st.markdown(ai_response)
                    conversation.append({"role": "assistant", "content": ai_response})
                    
                except Exception as e:
                    error_msg = "Thank you for sharing that. Your response has been saved."
                    st.markdown(error_msg)
                    conversation.append({"role": "assistant", "content": error_msg})
        
        # Save to database
        save_response(current_chapter_id, current_question_text, user_input)
        
        # Update conversation
        st.session_state.chapter_conversations[current_chapter_id][current_question_text] = conversation
        
        st.rerun()
# ============================================================================
# SECTION 15: FOOTER WITH STATISTICS
# ============================================================================
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    total_words_all_chapters = sum(calculate_chapter_word_count(ch["id"]) for ch in CHAPTERS)
    st.metric("Total Words", f"{total_words_all_chapters}")
with col2:
    completed_chapters = sum(1 for ch in CHAPTERS if st.session_state.responses[ch["id"]].get("completed", False))
    st.metric("Completed Chapters", f"{completed_chapters}/{len(CHAPTERS)}")
with col3:
    total_questions_answered = sum(len(st.session_state.responses[ch["id"]].get("questions", {})) for ch in CHAPTERS)
    total_all_questions = sum(len(ch["questions"]) for ch in CHAPTERS)
    st.metric("Questions Answered", f"{total_questions_answered}/{total_all_questions}")



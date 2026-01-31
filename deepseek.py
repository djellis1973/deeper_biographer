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

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY")))

# ============================================================================
# SECTION 2: CSS STYLING AND VISUAL DESIGN
# ============================================================================
LOGO_URL = "https://menuhunterai.com/wp-content/uploads/2026/01/logo.png"

st.markdown(f"""
<style>
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
        margin-bottom: 0.5rem;
        font-size: 1.3rem;
        font-weight: 600;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        line-height: 1.4;
    }}
    
    .question-counter {{
        font-size: 1.1rem;
        font-weight: bold;
        color: #2c3e50;
    }}
    
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
    
    [data-testid="stAppViewContainer"] {{
        padding-top: 0.5rem !important;
    }}
    
    .ghostwriter-tag {{
        font-size: 0.8rem;
        color: #666;
        font-style: italic;
        margin-top: 0.5rem;
    }}
    
    .edit-target-box {{
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border: 1px solid #dee2e6;
    }}
    
    .warning-box {{
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 6px;
        padding: 1rem;
        margin: 0.5rem 0;
    }}
    
    .progress-container {{
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        margin: 1rem 0;
    }}
    
    .progress-header {{
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 1rem;
        color: #2c3e50;
    }}
    
    .progress-status {{
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }}
    
    .progress-bar-container {{
        height: 10px;
        background-color: #e0e0e0;
        border-radius: 5px;
        overflow: hidden;
        margin: 1rem 0;
    }}
    
    .progress-bar-fill {{
        height: 100%;
        border-radius: 5px;
        transition: width 0.3s ease;
    }}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SECTION 3: SESSION DEFINITIONS AND DATA STRUCTURE
# ============================================================================
SESSIONS = [
    {
        "id": 1,
        "title": "Childhood",
        "guidance": "Welcome to Session 1: Childhood—this is where we lay the foundation of your story. Professional biographies thrive on specific, sensory-rich memories. I'm looking for the kind of details that transport readers: not just what happened, but how it felt, smelled, sounded. The 'insignificant' moments often reveal the most. Take your time—we're mining for gold here.",
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
        "guidance": "Welcome to Session 2: Family & Relationships—this is where we explore the people who shaped you. Family stories are complex ecosystems. We're not seeking perfect narratives, but authentic ones. The richest material often lives in the tensions, the unsaid things, the small rituals. My job is to help you articulate what usually goes unspoken. Think in scenes rather than summaries.",
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
        "guidance": "Welcome to Session 3: Education & Growing Up—this is where we explore how you learned to navigate the world. Education isn't just about schools—it's about how you learned to navigate the world. We're interested in the hidden curriculum: what you learned about yourself, about systems, about survival and growth. Think beyond grades to transformation.",
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
# SECTION 4: DATABASE FUNCTIONS (FIXED)
# ============================================================================
def init_db():
    """Initialize database tables"""
    conn = sqlite3.connect('life_story.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            session_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, session_id, question)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS word_targets (
            session_id INTEGER PRIMARY KEY,
            word_target INTEGER DEFAULT 500
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            session_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            conversation TEXT NOT NULL,
            UNIQUE(user_id, session_id, question)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def load_user_data(user_id):
    """Load all data for a specific user"""
    if user_id == "Guest":
        return {}
    
    data = {"responses": {}, "conversations": {}}
    
    try:
        conn = sqlite3.connect('life_story.db')
        cursor = conn.cursor()
        
        # Load responses
        cursor.execute("""
            SELECT session_id, question, answer 
            FROM responses 
            WHERE user_id = ?
            ORDER BY session_id, timestamp
        """, (user_id,))
        
        for session_id, question, answer in cursor.fetchall():
            if session_id not in data["responses"]:
                data["responses"][session_id] = {}
            data["responses"][session_id][question] = {
                "answer": answer,
                "timestamp": datetime.now().isoformat()
            }
        
        # Load conversations
        cursor.execute("""
            SELECT session_id, question, conversation 
            FROM conversations 
            WHERE user_id = ?
        """, (user_id,))
        
        for session_id, question, conversation_json in cursor.fetchall():
            if session_id not in data["conversations"]:
                data["conversations"][session_id] = {}
            try:
                data["conversations"][session_id][question] = json.loads(conversation_json)
            except:
                data["conversations"][session_id][question] = []
        
        conn.close()
    except Exception as e:
        st.error(f"Error loading data: {e}")
    
    return data

def save_response(user_id, session_id, question, answer):
    """Save a response to database"""
    try:
        conn = sqlite3.connect('life_story.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO responses 
            (user_id, session_id, question, answer) 
            VALUES (?, ?, ?, ?)
        """, (user_id, session_id, question, answer))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error saving response: {e}")
        return False

def save_conversation(user_id, session_id, question, conversation):
    """Save a conversation to database"""
    try:
        conn = sqlite3.connect('life_story.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO conversations 
            (user_id, session_id, question, conversation) 
            VALUES (?, ?, ?, ?)
        """, (user_id, session_id, question, json.dumps(conversation)))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error saving conversation: {e}")
        return False

def save_word_target(session_id, word_target):
    """Save word target to database"""
    try:
        conn = sqlite3.connect('life_story.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO word_targets 
            (session_id, word_target) 
            VALUES (?, ?)
        """, (session_id, word_target))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error saving word target: {e}")
        return False

def load_word_targets():
    """Load all word targets from database"""
    targets = {}
    try:
        conn = sqlite3.connect('life_story.db')
        cursor = conn.cursor()
        cursor.execute("SELECT session_id, word_target FROM word_targets")
        for session_id, word_target in cursor.fetchall():
            targets[session_id] = word_target
        conn.close()
    except:
        pass
    return targets

# ============================================================================
# SECTION 5: SESSION STATE INITIALIZATION (FIXED)
# ============================================================================
if "initialized" not in st.session_state:
    # Initialize all session state variables
    st.session_state.initialized = True
    st.session_state.user_id = "Guest"
    st.session_state.current_session = 0
    st.session_state.current_question = 0
    st.session_state.responses = {}
    st.session_state.session_conversations = {}
    st.session_state.editing = None
    st.session_state.edit_text = ""
    st.session_state.ghostwriter_mode = True
    st.session_state.spellcheck_enabled = True
    st.session_state.editing_word_target = False
    st.session_state.confirming_clear = None
    
    # Initialize empty structures for each session
    for session in SESSIONS:
        session_id = session["id"]
        st.session_state.responses[session_id] = {
            "title": session["title"],
            "questions": {},
            "summary": "",
            "completed": False,
            "word_target": session.get("word_target", 500)
        }
        st.session_state.session_conversations[session_id] = {}

# ============================================================================
# SECTION 6: CORE APPLICATION FUNCTIONS
# ============================================================================
def calculate_author_word_count(session_id):
    """Calculate total words for a session"""
    total_words = 0
    session_data = st.session_state.responses.get(session_id, {})
    
    for question, answer_data in session_data.get("questions", {}).items():
        if answer_data.get("answer"):
            total_words += len(re.findall(r'\w+', answer_data["answer"]))
    
    return total_words

def get_progress_info(session_id):
    """Get progress information for a session"""
    current_count = calculate_author_word_count(session_id)
    target = st.session_state.responses[session_id].get("word_target", 500)
    
    if target == 0:
        progress_percent = 100
        emoji = "🟢"
        color = "#2ecc71"
    else:
        progress_percent = (current_count / target) * 100 if target > 0 else 100
        
        if progress_percent >= 100:
            emoji = "🟢"
            color = "#2ecc71"
        elif progress_percent >= 70:
            emoji = "🟡"
            color = "#f39c12"
        else:
            emoji = "🔴"
            color = "#e74c3c"
    
    remaining_words = max(0, target - current_count)
    status_text = f"{remaining_words} words remaining" if remaining_words > 0 else "Target achieved!"
    
    return {
        "current_count": current_count,
        "target": target,
        "progress_percent": progress_percent,
        "emoji": emoji,
        "color": color,
        "remaining_words": remaining_words,
        "status_text": status_text
    }

# ============================================================================
# SECTION 7: AUTO-CORRECT FUNCTION
# ============================================================================
def auto_correct_text(text):
    """Auto-correct text using OpenAI"""
    if not text or not st.session_state.spellcheck_enabled:
        return text
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Fix spelling and grammar mistakes in the following text. Return only the corrected text."},
                {"role": "user", "content": text}
            ],
            max_tokens=len(text) + 100,
            temperature=0.1
        )
        return response.choices[0].message.content
    except:
        return text

# ============================================================================
# SECTION 8: GHOSTWRITER PROMPT FUNCTION
# ============================================================================
def get_system_prompt():
    current_session = SESSIONS[st.session_state.current_session]
    current_question = current_session["questions"][st.session_state.current_question]
    
    if st.session_state.ghostwriter_mode:
        return f"""ROLE: You are a senior literary biographer with multiple award-winning books to your name.

CURRENT SESSION: Session {current_session['id']}: {current_session['title']}
CURRENT TOPIC: "{current_question}"

YOUR APPROACH:
1. Listen like an archivist
2. Think in scenes, sensory details, and emotional truth
3. Find the story that needs to be told
4. Respect silence and complexity

Tone: Literary but not pretentious. Serious but not solemn."""
    else:
        return f"""You are a warm, professional biographer helping document a life story.

CURRENT SESSION: Session {current_session['id']}: {current_session['title']}
CURRENT TOPIC: "{current_question}"

Please:
1. Listen actively
2. Acknowledge warmly
3. Ask ONE natural follow-up question
4. Keep conversation flowing

Tone: Kind, curious, professional"""

# ============================================================================
# SECTION 9: MAIN APP HEADER
# ============================================================================
st.set_page_config(page_title="DeeperVault UK Legacy Builder", page_icon="📖", layout="wide")

st.markdown(f"""
<div class="main-header">
    <img src="{LOGO_URL}" class="logo-img" alt="DeeperVault UK Logo">
    <h2 style="margin: 0; line-height: 1.2;">DeeperVault UK Legacy Builder</h2>
    <p style="font-size: 0.9rem; color: #666; margin: 0; line-height: 1.2;">Preserve Your Legacy • Share Your Story</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# SECTION 10: SIDEBAR - USER PROFILE AND SETTINGS (FIXED)
# ============================================================================
with st.sidebar:
    st.header("👤 Your Profile")
    
    # User ID input with proper loading
    new_user_id = st.text_input("Your Name:", value=st.session_state.user_id, key="user_id_input")
    
    if new_user_id != st.session_state.user_id:
        # Save current data first if switching from existing user
        if st.session_state.user_id != "Guest":
            # Data is already saved automatically when entered
            pass
        
        # Switch to new user
        st.session_state.user_id = new_user_id
        
        # Clear current session state
        for session in SESSIONS:
            session_id = session["id"]
            st.session_state.responses[session_id] = {
                "title": session["title"],
                "questions": {},
                "summary": "",
                "completed": False,
                "word_target": session.get("word_target", 500)
            }
            st.session_state.session_conversations[session_id] = {}
        
        # Load word targets
        word_targets = load_word_targets()
        for session_id, target in word_targets.items():
            if session_id in st.session_state.responses:
                st.session_state.responses[session_id]["word_target"] = target
        
        # Load user data if not Guest
        if new_user_id != "Guest":
            user_data = load_user_data(new_user_id)
            
            # Load responses
            for session_id, questions in user_data.get("responses", {}).items():
                if int(session_id) in st.session_state.responses:
                    st.session_state.responses[int(session_id)]["questions"] = questions
            
            # Load conversations
            for session_id, conversations in user_data.get("conversations", {}).items():
                if int(session_id) in st.session_state.session_conversations:
                    st.session_state.session_conversations[int(session_id)] = conversations
        
        st.rerun()
    
    # Show current user info
    if st.session_state.user_id != "Guest":
        st.success(f"✓ Signed in as: **{st.session_state.user_id}**")
        
        # Show stats
        total_responses = sum(len(session.get("questions", {})) for session in st.session_state.responses.values())
        total_words = sum(calculate_author_word_count(s["id"]) for s in SESSIONS)
        
        st.metric("Total Responses", total_responses)
        st.metric("Total Words", total_words)
    else:
        st.warning("Enter your name to save your progress")
    
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
    
    spellcheck_enabled = st.toggle(
        "Auto Spelling Correction",
        value=st.session_state.spellcheck_enabled,
        help="Automatically correct spelling and grammar as you type"
    )
    
    if spellcheck_enabled != st.session_state.spellcheck_enabled:
        st.session_state.spellcheck_enabled = spellcheck_enabled
        st.rerun()
    
    if st.session_state.ghostwriter_mode:
        st.success("✓ Professional mode active")
    else:
        st.info("Standard mode active")
    
    # ============================================================================
    # SECTION 10A: SIDEBAR - SESSION NAVIGATION
    # ============================================================================
    st.divider()
    st.header("📖 Sessions")
    
    for i, session in enumerate(SESSIONS):
        session_id = session["id"]
        session_data = st.session_state.responses.get(session_id, {})
        
        # Calculate responses in this session
        responses_count = len(session_data.get("questions", {}))
        total_questions = len(session["questions"])
        
        # Determine session status
        if i == st.session_state.current_session:
            status = "▶️"
        elif responses_count == total_questions:
            status = "✅"
        elif responses_count > 0:
            status = "🟡"
        else:
            status = "●"
        
        button_text = f"{status} Session {session_id}: {session['title']} ({responses_count}/{total_questions})"
        
        if st.button(button_text, 
                    key=f"select_{i}",
                    use_container_width=True):
            st.session_state.current_session = i
            st.session_state.current_question = 0
            st.session_state.editing = None
            st.rerun()
    
    # ============================================================================
    # SECTION 10B: SIDEBAR - NAVIGATION CONTROLS
    # ============================================================================
    st.divider()
    st.subheader("Topic Navigation")
    
    current_session = SESSIONS[st.session_state.current_session]
    st.markdown(f'<div class="question-counter">Topic {st.session_state.current_question + 1} of {len(current_session["questions"])}</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Previous Topic", disabled=st.session_state.current_question == 0, key="prev_q_sidebar"):
            st.session_state.current_question = max(0, st.session_state.current_question - 1)
            st.session_state.editing = None
            st.rerun()
    
    with col2:
        if st.button("Next Topic →", disabled=st.session_state.current_question >= len(current_session["questions"]) - 1, key="next_q_sidebar"):
            st.session_state.current_question = min(len(current_session["questions"]) - 1, st.session_state.current_question + 1)
            st.session_state.editing = None
            st.rerun()
    
    st.divider()
    st.subheader("Session Navigation")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Previous Session", disabled=st.session_state.current_session == 0, key="prev_session_sidebar"):
            st.session_state.current_session = max(0, st.session_state.current_session - 1)
            st.session_state.current_question = 0
            st.session_state.editing = None
            st.rerun()
    with col2:
        if st.button("Next Session →", disabled=st.session_state.current_session >= len(SESSIONS)-1, key="next_session_sidebar"):
            st.session_state.current_session = min(len(SESSIONS)-1, st.session_state.current_session + 1)
            st.session_state.current_question = 0
            st.session_state.editing = None
            st.rerun()
    
    session_options = [f"Session {s['id']}: {s['title']}" for s in SESSIONS]
    selected_session = st.selectbox("Jump to session:", session_options, index=st.session_state.current_session)
    if session_options.index(selected_session) != st.session_state.current_session:
        st.session_state.current_session = session_options.index(selected_session)
        st.session_state.current_question = 0
        st.session_state.editing = None
        st.rerun()
    
    st.divider()
    
    # ============================================================================
    # SECTION 10C: SIDEBAR - EXPORT OPTIONS
    # ============================================================================
    st.subheader("📤 Export Options")
    
    total_answers = sum(len(session.get("questions", {})) for session in st.session_state.responses.values())
    st.caption(f"Total answers: {total_answers}")
    
    if st.button("📥 Export Current Progress", type="primary"):
        if total_answers > 0:
            export_data = {"sessions": {}}
            for session in SESSIONS:
                session_id = session["id"]
                session_data = st.session_state.responses.get(session_id, {})
                if session_data.get("questions"):
                    export_data["sessions"][session_id] = session_data
            
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
    # SECTION 10D: SIDEBAR - DANGEROUS ACTIONS WITH CONFIRMATION
    # ============================================================================
    st.subheader("⚠️ Clear Data")
    
    if st.session_state.confirming_clear == "session":
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.warning("**WARNING: This will delete ALL answers in the current session!**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirm Delete Session", type="primary", use_container_width=True):
                current_session_id = SESSIONS[st.session_state.current_session]["id"]
                try:
                    # Delete from database
                    conn = sqlite3.connect('life_story.db')
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM responses WHERE user_id = ? AND session_id = ?", 
                                  (st.session_state.user_id, current_session_id))
                    cursor.execute("DELETE FROM conversations WHERE user_id = ? AND session_id = ?", 
                                  (st.session_state.user_id, current_session_id))
                    conn.commit()
                    conn.close()
                    
                    # Clear from session state
                    st.session_state.responses[current_session_id]["questions"] = {}
                    st.session_state.session_conversations[current_session_id] = {}
                    st.session_state.confirming_clear = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        with col2:
            if st.button("❌ Cancel", type="secondary", use_container_width=True):
                st.session_state.confirming_clear = None
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    elif st.session_state.confirming_clear == "all":
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.warning("**WARNING: This will delete ALL answers for ALL sessions!**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirm Delete All", type="primary", use_container_width=True):
                try:
                    # Delete from database
                    conn = sqlite3.connect('life_story.db')
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM responses WHERE user_id = ?", 
                                  (st.session_state.user_id,))
                    cursor.execute("DELETE FROM conversations WHERE user_id = ?", 
                                  (st.session_state.user_id,))
                    conn.commit()
                    conn.close()
                    
                    # Clear from session state
                    for session in SESSIONS:
                        session_id = session["id"]
                        st.session_state.responses[session_id]["questions"] = {}
                        st.session_state.session_conversations[session_id] = {}
                    st.session_state.confirming_clear = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        with col2:
            if st.button("❌ Cancel", type="secondary", use_container_width=True):
                st.session_state.confirming_clear = None
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Session", type="secondary", use_container_width=True):
                st.session_state.confirming_clear = "session"
                st.rerun()
        
        with col2:
            if st.button("🔥 Clear All", type="secondary", use_container_width=True):
                st.session_state.confirming_clear = "all"
                st.rerun()

# ============================================================================
# SECTION 11: MAIN CONTENT - SESSION HEADER
# ============================================================================
current_session = SESSIONS[st.session_state.current_session]
current_session_id = current_session["id"]
current_question_text = current_session["questions"][st.session_state.current_question]

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.subheader(f"Session {current_session_id}: {current_session['title']}")
    
    # Show response count for this session
    session_responses = len(st.session_state.responses[current_session_id].get("questions", {}))
    total_questions = len(current_session["questions"])
    st.caption(f"📝 {session_responses}/{total_questions} topics answered")
    
    if st.session_state.ghostwriter_mode:
        st.markdown('<p class="ghostwriter-tag">Professional Ghostwriter Mode</p>', unsafe_allow_html=True)
        
with col2:
    st.markdown(f'<div class="question-counter" style="margin-top: 1rem;">Topic {st.session_state.current_question + 1} of {len(current_session["questions"])}</div>', unsafe_allow_html=True)
with col3:
    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        if st.button("← Previous Topic", disabled=st.session_state.current_question == 0, key="prev_q_quick", use_container_width=True):
            st.session_state.current_question = max(0, st.session_state.current_question - 1)
            st.session_state.editing = None
            st.rerun()
    with nav_col2:
        if st.button("Next Topic →", disabled=st.session_state.current_question >= len(current_session["questions"]) - 1, key="next_q_quick", use_container_width=True):
            st.session_state.current_question = min(len(current_session["questions"]) - 1, st.session_state.current_question + 1)
            st.session_state.editing = None
            st.rerun()

# Show current topic
st.markdown(f"""
<div class="question-box">
    {current_question_text}
</div>
""", unsafe_allow_html=True)

# Show session guidance
st.markdown(f"""
<div class="chapter-guidance">
    {current_session.get('guidance', '')}
</div>
""", unsafe_allow_html=True)

# Topics progress
session_data = st.session_state.responses.get(current_session_id, {})
topics_answered = len(session_data.get("questions", {}))
total_topics = len(current_session["questions"])

if total_topics > 0:
    topic_progress = topics_answered / total_topics
    st.progress(min(topic_progress, 1.0))
    st.caption(f"📝 Topics explored: {topics_answered}/{total_topics} ({topic_progress*100:.0f}%)")

# ============================================================================
# SECTION 12: CONVERSATION DISPLAY AND CHAT INPUT (FIXED)
# ============================================================================
# Get or create conversation for this question
current_session_id = current_session["id"]

if current_session_id not in st.session_state.session_conversations:
    st.session_state.session_conversations[current_session_id] = {}

conversation = st.session_state.session_conversations[current_session_id].get(current_question_text, [])

if not conversation:
    # Check if we have a saved response for this question
    saved_response = st.session_state.responses[current_session_id]["questions"].get(current_question_text)
    
    if saved_response:
        # We have a saved response but no conversation - create one
        conversation = [
            {"role": "assistant", "content": f"Let's explore this topic in detail: {current_question_text}"},
            {"role": "user", "content": saved_response["answer"]}
        ]
        st.session_state.session_conversations[current_session_id][current_question_text] = conversation
    else:
        # Start new conversation
        with st.chat_message("assistant", avatar="👔"):
            welcome_msg = f"""<div style='font-size: 1.4rem; margin-bottom: 1rem;'>
Let's explore this topic in detail:
</div>
<div style='font-size: 1.8rem; font-weight: bold; color: #2c3e50; line-height: 1.3;'>
{current_question_text}
</div>
<div style='font-size: 1.1rem; margin-top: 1.5rem; color: #555;'>
Take your time with this—good biographies are built from thoughtful reflection.
</div>"""
            
            st.markdown(welcome_msg, unsafe_allow_html=True)
            conversation.append({"role": "assistant", "content": f"Let's explore this topic in detail: {current_question_text}\n\nTake your time with this—good biographies are built from thoughtful reflection."})
            st.session_state.session_conversations[current_session_id][current_question_text] = conversation

# Display existing conversation
for i, message in enumerate(conversation):
    if message["role"] == "assistant":
        with st.chat_message("assistant", avatar="👔"):
            st.markdown(message["content"])
    
    elif message["role"] == "user":
        is_editing = (st.session_state.editing == (current_session_id, current_question_text, i))
        
        with st.chat_message("user", avatar="👤"):
            if is_editing:
                # Edit mode
                new_text = st.text_area(
                    "Edit your answer:",
                    value=st.session_state.edit_text,
                    key=f"edit_area_{current_session_id}_{hash(current_question_text)}_{i}",
                    height=150,
                    label_visibility="collapsed"
                )
                
                if new_text:
                    edit_word_count = len(re.findall(r'\w+', new_text))
                    st.caption(f"📝 Editing: {edit_word_count} words")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✓ Save", key=f"save_{current_session_id}_{hash(current_question_text)}_{i}", type="primary"):
                        # Auto-correct before saving
                        if st.session_state.spellcheck_enabled:
                            new_text = auto_correct_text(new_text)
                        
                        # Update conversation
                        conversation[i]["content"] = new_text
                        st.session_state.session_conversations[current_session_id][current_question_text] = conversation
                        
                        # Save to database
                        save_response(st.session_state.user_id, current_session_id, current_question_text, new_text)
                        save_conversation(st.session_state.user_id, current_session_id, current_question_text, conversation)
                        
                        # Update session state
                        st.session_state.responses[current_session_id]["questions"][current_question_text] = {
                            "answer": new_text,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        st.session_state.editing = None
                        st.rerun()
                with col2:
                    if st.button("✕ Cancel", key=f"cancel_{current_session_id}_{hash(current_question_text)}_{i}"):
                        st.session_state.editing = None
                        st.rerun()
            else:
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(message["content"])
                    word_count = len(re.findall(r'\w+', message["content"]))
                    st.caption(f"📝 {word_count} words • Click ✏️ to edit")
                with col2:
                    if st.button("✏️", key=f"edit_{current_session_id}_{hash(current_question_text)}_{i}"):
                        st.session_state.editing = (current_session_id, current_question_text, i)
                        st.session_state.edit_text = message["content"]
                        st.rerun()

# ============================================================================
# CHAT INPUT BOX
# ============================================================================
input_container = st.container()

with input_container:
    st.write("")
    st.write("")
    
    user_input = st.chat_input("Type your answer here...")
    
    if user_input:
        # Auto-correct if enabled
        if st.session_state.spellcheck_enabled:
            user_input = auto_correct_text(user_input)
        
        # Add user message to conversation
        conversation.append({"role": "user", "content": user_input})
        
        # Generate AI response
        with st.chat_message("assistant", avatar="👔"):
            with st.spinner("Reflecting on your story..."):
                try:
                    # Generate thoughtful response
                    conversation_history = conversation[:-1]
                    
                    messages_for_api = [
                        {"role": "system", "content": get_system_prompt()},
                        *conversation_history,
                        {"role": "user", "content": user_input}
                    ]
                    
                    if st.session_state.ghostwriter_mode:
                        temperature = 0.8
                        max_tokens = 400
                    else:
                        temperature = 0.7
                        max_tokens = 300
                    
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages_for_api,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    
                    ai_response = response.choices[0].message.content
                    
                    # Add professional note
                    word_count = len(re.findall(r'\w+', user_input))
                    if word_count < 50:
                        ai_response += f"\n\n**Note:** You've touched on something important. Consider expanding on the sensory details—what did you see, hear, feel?"
                    elif word_count < 150:
                        ai_response += f"\n\n**Note:** Good detail. Where does the emotional weight live in this memory?"
                    
                    st.markdown(ai_response)
                    conversation.append({"role": "assistant", "content": ai_response})
                    
                except Exception as e:
                    error_msg = "Thank you for sharing that. Your response has been saved."
                    st.markdown(error_msg)
                    conversation.append({"role": "assistant", "content": error_msg})
        
        # Save everything
        st.session_state.session_conversations[current_session_id][current_question_text] = conversation
        
        # Save to database
        save_response(st.session_state.user_id, current_session_id, current_question_text, user_input)
        save_conversation(st.session_state.user_id, current_session_id, current_question_text, conversation)
        
        # Update session state
        st.session_state.responses[current_session_id]["questions"][current_question_text] = {
            "answer": user_input,
            "timestamp": datetime.now().isoformat()
        }
        
        st.rerun()

# ============================================================================
# SECTION 13: WORD PROGRESS INDICATOR
# ============================================================================
st.divider()

# Get progress info
progress_info = get_progress_info(current_session_id)

# Display progress container
st.markdown(f"""
<div class="progress-container">
    <div class="progress-header">📊 Session Progress</div>
    <div class="progress-status">{progress_info['emoji']} {progress_info['progress_percent']:.0f}% complete • {progress_info['status_text']}</div>
    <div class="progress-bar-container">
        <div class="progress-bar-fill" style="width: {min(progress_info['progress_percent'], 100)}%; background-color: {progress_info['color']};"></div>
    </div>
    <div style="text-align: center; font-size: 0.9rem; color: #666; margin-top: 0.5rem;">
        {progress_info['current_count']} / {progress_info['target']} words
    </div>
</div>
""", unsafe_allow_html=True)

# Edit target button
if st.button("✏️ Change Word Target", key="edit_word_target_bottom", use_container_width=True):
    st.session_state.editing_word_target = not st.session_state.editing_word_target
    st.rerun()

# Show edit interface when triggered
if st.session_state.editing_word_target:
    st.markdown('<div class="edit-target-box">', unsafe_allow_html=True)
    st.write("**Change Word Target**")
    
    new_target = st.number_input(
        "Target words for this session:",
        min_value=100,
        max_value=5000,
        value=progress_info['target'],
        key="target_edit_input_bottom",
        label_visibility="collapsed"
    )
    
    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button("💾 Save", key="save_word_target_bottom", type="primary", use_container_width=True):
            # Update session state
            st.session_state.responses[current_session_id]["word_target"] = new_target
            # Update database
            save_word_target(current_session_id, new_target)
            st.session_state.editing_word_target = False
            st.rerun()
    with col_cancel:
        if st.button("❌ Cancel", key="cancel_word_target_bottom", use_container_width=True):
            st.session_state.editing_word_target = False
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# SECTION 14: FOOTER WITH STATISTICS
# ============================================================================
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    total_words_all_sessions = sum(calculate_author_word_count(s["id"]) for s in SESSIONS)
    st.metric("Total Words", f"{total_words_all_sessions}")
with col2:
    completed_sessions = sum(1 for s in SESSIONS if len(st.session_state.responses[s["id"]].get("questions", {})) == len(s["questions"]))
    st.metric("Completed Sessions", f"{completed_sessions}/{len(SESSIONS)}")
with col3:
    total_topics_answered = sum(len(st.session_state.responses[s["id"]].get("questions", {})) for s in SESSIONS)
    total_all_topics = sum(len(s["questions"]) for s in SESSIONS)
    st.metric("Topics Explored", f"{total_topics_answered}/{total_all_topics}")

# ============================================================================
# SECTION 15: SIMPLE PUBLISH & VAULT SECTION
# ============================================================================
st.divider()
st.subheader("📘 Publish Your Biography")

# Get the current user's data
current_user = st.session_state.get('user_id', '')
export_data = {}

# Prepare data for export
for session in SESSIONS:
    session_id = session["id"]
    session_data = st.session_state.responses.get(session_id, {})
    if session_data.get("questions"):
        export_data[str(session_id)] = {
            "title": session["title"],
            "questions": session_data["questions"]
        }

if current_user and current_user != "Guest" and export_data:
    # Count total stories
    total_stories = sum(len(session['questions']) for session in export_data.values())
    
    # Create JSON data for the publisher
    json_data = json.dumps({
        "user": current_user,
        "stories": export_data,
        "export_date": datetime.now().isoformat()
    }, indent=2)
    
    # Encode the data for URL
    import base64
    encoded_data = base64.b64encode(json_data.encode()).decode()
    
    # Create URL for the publisher
    publisher_base_url = "https://deeperbiographer-dny9n2j6sflcsppshrtrmu.streamlit.app/"
    publisher_url = f"{publisher_base_url}?data={encoded_data}"
    
    st.success(f"✅ **{total_stories} stories ready to publish!**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🖨️ Create Your Book")
        st.markdown(f"""
        Generate a beautiful, formatted biography from your stories.
        
        **[📘 Click to Create Biography]({publisher_url})**
        
        Your book will include:
        • Professional formatting
        • Table of contents
        • All your stories organized
        • Ready to print or share
        """)
    
    with col2:
        st.markdown("#### 🔐 Save to Your Vault")
        st.markdown("""
        **After creating your book:**
        
        1. Generate your biography (link on left)
        2. Download the formatted PDF
        3. Save it to your secure vault
        
        **[💾 Go to Secure Vault](https://digital-legacy-vault.streamlit.app)**
        
        Your vault preserves important documents forever.
        """)
    
    # Backup download
    with st.expander("📥 Download Raw Data (Backup)"):
        st.download_button(
            label="Download Stories as JSON",
            data=json_data,
            file_name=f"{current_user}_stories.json",
            mime="application/json",
            use_container_width=True
        )
        st.caption("Use this if the publisher link doesn't work")
        
elif current_user and current_user != "Guest":
    st.info("📝 **Answer some questions first!** Come back here after saving some stories.")
else:
    st.info("👤 **Enter your name in the sidebar to begin**")

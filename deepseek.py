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
    
    /* Chat styling */
    .stChatMessage {{
        margin-bottom: 0.5rem !important;
    }}
    
    /* Custom avatar styling */
    .ghostwriter-avatar {{
        background-color: #4a5568 !important;
        color: white !important;
    }}
    
    .storyteller-avatar {{
        background-color: #2c5282 !important;
        color: white !important;
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
    
    .edit-target-box {{
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border: 1px solid #dee2e6;
    }}
    
    .danger-button {{
        background-color: #e74c3c !important;
        color: white !important;
        border-color: #c0392b !important;
    }}
    
    .danger-button:hover {{
        background-color: #c0392b !important;
    }}
    
    .warning-box {{
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 6px;
        padding: 1rem;
        margin: 0.5rem 0;
    }}
    
    /* Word count progress box styling */
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
    
    /* Navigation button styling */
    .nav-button {{
        font-size: 0.9rem;
        padding: 0.5rem 1rem;
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
# SECTION 4: DATABASE FUNCTIONS
# ============================================================================
def init_db():
    conn = sqlite3.connect('life_story.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            user_id TEXT,
            session_id INTEGER,
            question TEXT,
            answer TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS word_targets (
            session_id INTEGER PRIMARY KEY,
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
    st.session_state.current_session = 0
    st.session_state.current_question = 0
    st.session_state.responses = {}
    st.session_state.user_id = "Guest"
    st.session_state.session_conversations = {}
    st.session_state.editing = None
    st.session_state.edit_text = ""
    st.session_state.ghostwriter_mode = True
    st.session_state.spellcheck_enabled = True
    st.session_state.editing_word_target = False
    st.session_state.confirming_clear = None  # 'session' or 'all' or None
    
    # Initialize for each session
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
    
    # Load word targets from database
    try:
        conn = sqlite3.connect('life_story.db')
        cursor = conn.cursor()
        cursor.execute("SELECT session_id, word_target FROM word_targets")
        for session_id, word_target in cursor.fetchall():
            if session_id in st.session_state.responses:
                st.session_state.responses[session_id]["word_target"] = word_target
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
            SELECT session_id, question, answer 
            FROM responses 
            WHERE user_id = ?
        """, (st.session_state.user_id,))
        
        for session_id, question, answer in cursor.fetchall():
            if session_id not in st.session_state.responses:
                continue
            st.session_state.responses[session_id]["questions"][question] = {
                "answer": answer,
                "timestamp": datetime.now().isoformat()
            }
        
        conn.close()
    except:
        pass

def save_response(session_id, question, answer):
    user_id = st.session_state.user_id
    
    if session_id not in st.session_state.responses:
        st.session_state.responses[session_id] = {
            "title": SESSIONS[session_id-1]["title"],
            "questions": {},
            "summary": "",
            "completed": False,
            "word_target": SESSIONS[session_id-1].get("word_target", 500)
        }
    
    st.session_state.responses[session_id]["questions"][question] = {
        "answer": answer,
        "timestamp": datetime.now().isoformat()
    }
    
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
    except:
        pass

def save_word_target(session_id, word_target):
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
    except:
        pass

def calculate_author_word_count(session_id):
    total_words = 0
    session_data = st.session_state.responses.get(session_id, {})
    
    for question, answer_data in session_data.get("questions", {}).items():
        if answer_data.get("answer"):
            total_words += len(re.findall(r'\w+', answer_data["answer"]))
    
    return total_words

def get_progress_info(session_id):
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
        return text  # Return original if OpenAI fails

# ============================================================================
# SECTION 8: GHOSTWRITER PROMPT FUNCTION
# ============================================================================
def get_system_prompt():
    current_session = SESSIONS[st.session_state.current_session]
    current_question = current_session["questions"][st.session_state.current_question]
    
    if st.session_state.ghostwriter_mode:
        return f"""ROLE: You are a senior literary biographer with multiple award-winning books to your name. You're working with someone on their life story, and you treat this with the seriousness of archival research combined with literary craft.

CURRENT SESSION: Session {current_session['id']}: {current_session['title']}
CURRENT TOPIC: "{current_question}"

YOUR APPROACH:
1. You listen like an archivist—hearing not just what's said, but what's implied
2. You think in scenes, sensory details, and emotional truth
3. You're not here to flatter; you're here to find the story that needs to be told
4. You respect silence and complexity—you don't rush toward resolution
5. You understand that memory is reconstruction, and you help reconstruct with integrity

TECHNIQUE:
- After they share, you often pause before responding (reflected in thoughtful language)
- You reference specific details they've mentioned, showing you're truly listening
- You ask questions that open space rather than close it
- You sometimes gently challenge assumptions or explore contradictions
- You're comfortable with ambiguity and unresolved moments

EXAMPLE RESPONSES:
To "I remember my grandmother's kitchen always smelled of cinnamon":
"That's telling—cinnamon as character. Not just a smell, but a presence. Was it the cinnamon of baking or of potpourri? And did that scent mean comfort, or duty, or something more complicated?"

To "School was mostly boring until Mr. Jenkins' class":
"Let's sit with 'mostly boring' for a moment. What did that boredom feel like in your body? And what specifically shifted in Mr. Jenkins' room—was it the material, his presence, or something in you that changed?"

Tone: Literary but not pretentious. Serious but not solemn. You're doing important work, and it shows in your attention to detail."""
    else:
        return f"""You are a warm, professional biographer helping document a life story.

CURRENT SESSION: Session {current_session['id']}: {current_session['title']}
CURRENT TOPIC: "{current_question}"

Please:
1. Listen actively to their response
2. Acknowledge it warmly (1-2 sentences)
3. Ask ONE natural follow-up question if appropriate
4. Keep the conversation flowing naturally

Tone: Kind, curious, professional
Goal: Draw out authentic, detailed memories

Focus ONLY on the current topic. Don't reference previous sessions."""

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
        st.session_state.session_conversations = {}
        st.session_state.current_session = 0
        st.session_state.current_question = 0
        st.session_state.editing = None
        st.session_state.edit_text = ""
        st.session_state.editing_word_target = False
        st.session_state.confirming_clear = None
        
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
        
        # Determine session status
        if session_data.get("completed", False):
            status = "✅"
        elif i == st.session_state.current_session:
            status = "▶️"
        else:
            status = "●"
        
        # Session button (just title)
        button_text = f"{status} Session {session_id}: {session['title']}"
        
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
    st.caption(f"Total answers to export: {total_answers}")
    
    if st.button("📥 Export Current Progress", type="primary"):
        if total_answers > 0:
            # Simple export implementation
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
    st.subheader("⚠️ Dangerous Actions")
    
    if st.session_state.confirming_clear == "session":
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.warning("**WARNING: This will permanently delete ALL answers in the current session!**")
        st.write("Type 'DELETE SESSION' to confirm:")
        
        confirm_text = st.text_input("Confirmation:", key="confirm_session_delete", label_visibility="collapsed")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirm Delete", type="primary", use_container_width=True, disabled=confirm_text != "DELETE SESSION"):
                if confirm_text == "DELETE SESSION":
                    current_session_id = SESSIONS[st.session_state.current_session]["id"]
                    try:
                        conn = sqlite3.connect('life_story.db')
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM responses WHERE user_id = ? AND session_id = ?", 
                                      (st.session_state.user_id, current_session_id))
                        conn.commit()
                        conn.close()
                        st.session_state.responses[current_session_id]["questions"] = {}
                        st.session_state.confirming_clear = None
                        st.success("Session cleared!")
                        st.rerun()
                    except:
                        pass
        with col2:
            if st.button("❌ Cancel", type="secondary", use_container_width=True):
                st.session_state.confirming_clear = None
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    elif st.session_state.confirming_clear == "all":
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.warning("**WARNING: This will permanently delete ALL answers in ALL sessions!**")
        st.write("Type 'DELETE ALL' to confirm:")
        
        confirm_text = st.text_input("Confirmation:", key="confirm_all_delete", label_visibility="collapsed")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirm Delete All", type="primary", use_container_width=True, disabled=confirm_text != "DELETE ALL"):
                if confirm_text == "DELETE ALL":
                    try:
                        conn = sqlite3.connect('life_story.db')
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM responses WHERE user_id = ?", 
                                      (st.session_state.user_id,))
                        conn.commit()
                        conn.close()
                        for session in SESSIONS:
                            session_id = session["id"]
                            st.session_state.responses[session_id]["questions"] = {}
                        st.session_state.confirming_clear = None
                        st.success("All data cleared!")
                        st.rerun()
                    except:
                        pass
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
    
    if st.session_state.ghostwriter_mode:
        st.markdown('<p class="ghostwriter-tag">Professional Ghostwriter Mode • Advanced Interviewing</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="ghostwriter-tag">Standard Interview Mode</p>', unsafe_allow_html=True)
        
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
# SECTION 12: CONVERSATION DISPLAY AND CHAT INPUT
# ============================================================================
current_session_id = current_session["id"]
current_question_text = current_session["questions"][st.session_state.current_question]

if current_session_id not in st.session_state.session_conversations:
    st.session_state.session_conversations[current_session_id] = {}

conversation = st.session_state.session_conversations[current_session_id].get(current_question_text, [])

if not conversation:
    # Custom avatar for ghostwriter
    with st.chat_message("assistant", avatar="👔"):
        if st.session_state.ghostwriter_mode:
            welcome_msg = f"""<div style='font-size: 1.4rem; margin-bottom: 1rem;'>
Let's explore this topic in detail:
</div>
<div style='font-size: 1.8rem; font-weight: bold; color: #2c3e50; line-height: 1.3;'>
{current_question_text}
</div>
<div style='font-size: 1.1rem; margin-top: 1.5rem; color: #555;'>
Take your time with this—good biographies are built from thoughtful reflection rather than quick answers.
</div>"""
        else:
            welcome_msg = f"""<div style='font-size: 1.4rem; margin-bottom: 1rem;'>
I'd love to hear your thoughts about this topic:
</div>
<div style='font-size: 1.8rem; font-weight: bold; color: #2c3e50; line-height: 1.3;'>
{current_question_text}
</div>"""
        
        st.markdown(welcome_msg, unsafe_allow_html=True)
        conversation.append({"role": "assistant", "content": f"Let's explore this topic in detail: {current_question_text}\n\nTake your time with this—good biographies are built from thoughtful reflection rather than quick answers."})
        st.session_state.session_conversations[current_session_id][current_question_text] = conversation
else:
    for i, message in enumerate(conversation):
        if message["role"] == "assistant":
            # Custom avatar for ghostwriter
            with st.chat_message("assistant", avatar="👔"):
                st.markdown(message["content"])
        
        elif message["role"] == "user":
            is_editing = (st.session_state.editing == (current_session_id, current_question_text, i))
            
            # Custom avatar for storyteller
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
                            
                            conversation[i]["content"] = new_text
                            st.session_state.session_conversations[current_session_id][current_question_text] = conversation
                            save_response(current_session_id, current_question_text, new_text)
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
# CHAT INPUT BOX - MUST BE DIRECTLY HERE
# ============================================================================

# Create a container for the chat input
input_container = st.container()

with input_container:
    # Add some spacing
    st.write("")
    st.write("")
    
    # Create the chat input
    user_input = st.chat_input("Type your answer here...")
    
    if user_input:
        # Auto-correct as they type
        if st.session_state.spellcheck_enabled:
            user_input = auto_correct_text(user_input)
        
        # Add user message to conversation
        conversation.append({"role": "user", "content": user_input})
        
        # Generate AI response with expert critique
        # Custom avatar for ghostwriter
        with st.chat_message("assistant", avatar="👔"):
            with st.spinner("Reflecting on your story..."):
                try:
                    # First, analyze the person's response for critique
                    critique_prompt = f"""As a professional ghostwriter, analyze this response to the topic: "{current_question_text}"

PERSON'S STORY:
{user_input}

Provide a brief professional assessment (3-4 sentences max) focusing on:
1. What's working well narratively
2. What could be deepened or expanded
3. One specific suggestion for richer detail

Keep it concise, constructive, and professional. Focus on storytelling craft, not praise. Refer to the person as "the storyteller", "they", or "their story" - never use clinical terms like "user"."""

                    critique_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You're a seasoned biographer with 30 years experience. You provide sharp, constructive feedback that helps writers find their most compelling stories. Always refer to people as 'the storyteller', 'they', or use their name if provided - never use clinical terms like 'user' or 'the user'."},
                            {"role": "user", "content": critique_prompt}
                        ],
                        temperature=0.7,
                        max_tokens=200
                    )
                    
                    critique = critique_response.choices[0].message.content
                    
                    # Now generate the conversational follow-up
                    conversation_history = conversation[:-1]  # Get everything except the just-added user message
                    
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
                    
                    # Add the expert critique at the end
                    ai_response += f"\n\n---\n\n**Professional note:** {critique}"
                    
                    st.markdown(ai_response)
                    conversation.append({"role": "assistant", "content": ai_response})
                    
                except Exception as e:
                    # Fallback if critique fails
                    try:
                        conversation_history = conversation[:-1]
                        
                        messages_for_api = [
                            {"role": "system", "content": get_system_prompt()},
                            *conversation_history,
                            {"role": "user", "content": user_input}
                        ]
                        
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=messages_for_api,
                            temperature=0.8,
                            max_tokens=400
                        )
                        
                        ai_response = response.choices[0].message.content
                        
                        # Add a thoughtful observation instead
                        word_count = len(re.findall(r'\w+', user_input))
                        if word_count < 50:
                            ai_response += f"\n\n**Observation:** You've touched on something important here. What would happen if you slowed down this moment? What details are just outside the frame of this memory?"
                        elif word_count < 150:
                            ai_response += f"\n\n**Observation:** There's good texture in this recollection. I'm noticing where the emotion lives in this story—let's explore that space more deliberately."
                        else:
                            ai_response += f"\n\n**Observation:** This has real narrative weight. The challenge now is curation—what's the through-line that makes this memory essential to your story?"
                        
                        st.markdown(ai_response)
                        conversation.append({"role": "assistant", "content": ai_response})
                        
                    except Exception as e2:
                        error_msg = "Thank you for sharing that. Your response has been saved."
                        st.markdown(error_msg)
                        conversation.append({"role": "assistant", "content": error_msg})
        
        # Save to database
        save_response(current_session_id, current_question_text, user_input)
        
        # Update conversation
        st.session_state.session_conversations[current_session_id][current_question_text] = conversation
        
        st.rerun()
# ============================================================================
# SECTION 13: WORD PROGRESS INDICATOR (BELOW CHAT INPUT)
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
    completed_sessions = sum(1 for s in SESSIONS if st.session_state.responses[s["id"]].get("completed", False))
    st.metric("Completed Sessions", f"{completed_sessions}/{len(SESSIONS)}")
with col3:
    total_topics_answered = sum(len(st.session_state.responses[s["id"]].get("questions", {})) for s in SESSIONS)
    total_all_topics = sum(len(s["questions"]) for s in SESSIONS)
    st.metric("Topics Explored", f"{total_topics_answered}/{total_all_topics}")

# ============================================================================
# SECTION: PUBLISH YOUR BIOGRAPHY (WITH EXPORT DATA IN URL)
# ============================================================================
st.divider()
st.subheader("📖 Ready to Publish Your Biography?")

# Get the current user's data
current_user = st.session_state.get('user_id', '')
export_data = {}

# Prepare data for export - using your existing session state structure
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
    
    # Create JSON data
    json_data = json.dumps({
        "user": current_user,
        "stories": export_data,
        "export_date": datetime.now().isoformat()
    }, indent=2)
    
    # Encode the data for URL
    import base64
    encoded_data = base64.b64encode(json_data.encode()).decode()
    
    # Create URL with the data
    publisher_base_url = "https://deeperbiographer-dny9n2j6sflcsppshrtrmu.streamlit.app/"
    publisher_url = f"{publisher_base_url}?data={encoded_data}"
    
    st.markdown(f"""
    Your **{total_stories} stories** are ready to publish.
    
    **[🖨️ Click here to generate your biography]({publisher_url})**
    
    *All your data comes automatically - no typing needed!*
    """)
    
    # Also provide manual download as backup
    with st.expander("📥 Backup: Download Data File"):
        st.download_button(
            label="Download Stories as JSON",
            data=json_data,
            file_name=f"{current_user}_stories.json",
            mime="application/json"
        )
        st.caption("If the link doesn't work, download this file and upload it in the publisher app.")
        
elif current_user and current_user != "Guest":
    st.info("💡 **Answer some questions first!** Your stories will appear here once you save them.")
else:
    st.info("👤 **Please enter your name in the sidebar to begin.**")

st.caption("Your data stays private - it's encoded in the URL and never stored on our servers.")

# ============================================================================
# SECTION: CONNECT TO YOUR SECURE LEGACY VAULT
# ============================================================================
st.divider()
st.subheader("🔐 Store Your Biography Securely")

# Replace this with your actual vault app URL
VAULT_APP_URL = "https://digital-legacy-vault-vwvd4eclaeq4hxtcbbshr2.streamlit.app/"

st.markdown(f"""
**Your biography is complete!**

Preserve it alongside your legal documents, photos, and important files in your personal, encrypted vault.

**[➡️ Go to Secure Legacy Vault]({VAULT_APP_URL})**

*Features of your vault:*
*   **Zero-Knowledge Encryption:** Your password never leaves your device.
*   **Organized Storage:** Categorize documents (Legal, Medical, Personal, Biography).
*   **Future-Proof:** Designed to preserve your legacy for generations.
""")

# ============================================================================
# SECTION: DIRECT VAULT UPLOAD (One-Click Method)
# ============================================================================
st.divider()
st.subheader("🚀 Save to Your Secure Vault")

# Your actual vault URL - CHANGE THIS TO YOUR REAL VAULT URL!
VAULT_APP_URL = "https://digital-legacy-vault-vwvd4eclaeq4hxtcbbshr2.streamlit.app"  # ⬅️ YOUR REAL URL

# Get user name for filename
user_name = st.session_state.get('user_id', 'User').replace(' ', '_')
filename = f"{user_name}_Life_Story.txt"

# Create the pre-filled vault link
import urllib.parse
encoded_filename = urllib.parse.quote(filename)
prefilled_vault_link = f"{VAULT_APP_URL}?prefill_name={encoded_filename}&category=Biography&source=biography_app"

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 📦 Prepare Your Biography")
    
    # Check if we have stories to export
    if export_data and total_stories > 0:
        # Create a simple text version of the biography
        biography_text = f"Life Story of {user_name}\n"
        biography_text += "=" * 50 + "\n\n"
        
        for session_id, session_data in export_data.items():
            biography_text += f"## {session_data.get('title', f'Session {session_id}')}\n\n"
            for question, answer_data in session_data.get('questions', {}).items():
                biography_text += f"### {question}\n"
                biography_text += f"{answer_data.get('answer', '')}\n\n"
        
        # Download button
        st.download_button(
            label="📥 Download Biography (.txt)",
            data=biography_text,
            file_name=filename,
            mime="text/plain",
            type="primary",
            use_container_width=True,
            help="Download your complete biography as a text file"
        )
        
        st.caption(f"Contains {total_stories} stories, ready for your vault.")
        
        # Show what's included
        with st.expander("📋 Preview Biography Contents", expanded=False):
            st.write(f"**Filename:** `{filename}`")
            st.write(f"**Total Stories:** {total_stories}")
            st.write(f"**User:** {user_name}")
            st.write("**Contains sessions:**")
            for session_id in export_data.keys():
                st.write(f"- {export_data[session_id].get('title', f'Session {session_id}')}")
    else:
        st.warning("No stories to save yet.")
        st.info("Complete some interview questions first!")
        biography_text = ""

with col2:
    st.markdown("#### 🔒 Secure Storage Instructions")
    
    if export_data and total_stories > 0:
        st.success(f"✅ **{total_stories} stories ready to save!**")
        
        st.markdown(f"""
        **How to save your biography:**
        
        1. **Click the download button** (← left) to save your file
        2. **[Open your secure vault]({prefilled_vault_link})**
        3. **Upload** the downloaded file when prompted
        
        **The vault will automatically:**
        • Suggest filename: `{filename}`
        • Select "Biography" category
        • Add helpful notes
        
        ⚠️ **Important:** Keep your vault password safe! Without it, your encrypted files cannot be recovered.
        """)
        
        # Direct link to vault
        st.link_button(
            "🔗 Open My Secure Vault",
            prefilled_vault_link,
            use_container_width=True,
            help="Opens your vault app in a new tab"
        )
        
        # Show the link for debugging
        with st.expander("🔍 View vault link details", expanded=False):
            st.code(prefilled_vault_link)
            st.caption("This link opens your vault with pre-filled information. Save it as a bookmark!")
    else:
        st.info("📝 **Complete your biography first!**")
        st.markdown("""
        Once you've answered some questions, you'll see:
        1. A download button for your biography
        2. Instructions for saving to your vault
        3. A direct link to your secure vault
        """)

# Optional: Show security info
st.markdown("---")
st.markdown("""
### 🛡️ About Your Secure Vault

Your **Digital Legacy Vault** is a zero-knowledge encrypted storage system:

- **Military-Grade Encryption:** Your files are encrypted before they leave your device
- **Biography Category:** Special section designed for life stories
- **Future Access:** Share access instructions with loved ones
- **No Data Mining:** We never read or analyze your personal stories

*Your biography deserves the highest level of protection.*
""")

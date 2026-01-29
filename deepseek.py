import streamlit as st
import json
from datetime import datetime
from openai import OpenAI
import os
import sqlite3
import base64
from fpdf import FPDF
import tempfile
from PIL import Image, ImageDraw
import io

# ────────────────────────────────────────────────
# BRANDING CONFIGURATION
# ────────────────────────────────────────────────
# Your exact colors
BRAND_COLORS = {
    "beige": "#b5aa96ff",
    "background_grey": "#c7c7c4ff",
    "dark_grey": "#3e403fff",
    "accent": "#4a5568",  # Added for contrast
    "light": "#f8f9fa"
}

# Custom CSS with your exact colors
CUSTOM_CSS = f"""
<style>
    /* Main container styling */
    .main {{
        background-color: {BRAND_COLORS['background_grey']};
    }}
    
    /* Header with gradient */
    .main-header {{
        background: linear-gradient(135deg, {BRAND_COLORS['dark_grey']} 0%, #2d2f2e 100%);
        padding: 2.5rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }}
    
    /* Sidebar styling */
    .css-1d391kg, .css-12oz5g7 {{
        background-color: {BRAND_COLORS['background_grey']} !important;
    }}
    
    /* Buttons */
    .stButton > button {{
        background-color: {BRAND_COLORS['dark_grey']};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s;
    }}
    .stButton > button:hover {{
        background-color: {BRAND_COLORS['beige']};
        color: {BRAND_COLORS['dark_grey']};
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }}
    
    /* Primary button */
    div[data-testid="stButton"]:has(button[kind="primary"]) button {{
        background: linear-gradient(135deg, {BRAND_COLORS['dark_grey']} 0%, #2d2f2e 100%);
        color: white;
    }}
    
    /* Cards */
    .chapter-card {{
        background-color: {BRAND_COLORS['beige']}20; /* 20% opacity */
        padding: 1rem;
        border-left: 4px solid {BRAND_COLORS['dark_grey']};
        border-radius: 8px;
        margin-bottom: 0.75rem;
        transition: all 0.3s;
    }}
    .chapter-card:hover {{
        background-color: {BRAND_COLORS['beige']}40;
        transform: translateX(5px);
    }}
    
    /* Chat messages */
    .stChatMessage {{
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
    }}
    div[data-testid="stChatMessage"]:has(svg[aria-label="user"]) {{
        background-color: {BRAND_COLORS['beige']}30;
    }}
    div[data-testid="stChatMessage"]:has(svg[aria-label="assistant"]) {{
        background-color: {BRAND_COLORS['background_grey']};
    }}
    
    /* Progress bars */
    .stProgress > div > div > div > div {{
        background-color: {BRAND_COLORS['dark_grey']};
    }}
    
    /* Input boxes */
    .stTextInput > div > div > input {{
        border: 2px solid {BRAND_COLORS['beige']};
        border-radius: 8px;
        background-color: white;
    }}
    
    /* Divider */
    hr {{
        border-color: {BRAND_COLORS['beige']}50;
    }}
    
    /* Brand footer */
    .brand-footer {{
        background-color: {BRAND_COLORS['dark_grey']};
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin-top: 3rem;
        text-align: center;
    }}
    
    /* Logo container */
    .logo-container {{
        display: flex;
        justify-content: center;
        margin-bottom: 1rem;
    }}
    .logo-img {{
        width: 120px;
        height: 120px;
        border-radius: 50%;
        object-fit: cover;
        border: 4px solid {BRAND_COLORS['beige']};
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }}
</style>
"""

# Create a round logo if not exists
def create_round_logo():
    """Create a round logo with LSAI initials"""
    img = Image.new('RGB', (400, 400), BRAND_COLORS['dark_grey'])
    draw = ImageDraw.Draw(img)
    
    # Draw a circle
    draw.ellipse([50, 50, 350, 350], fill=BRAND_COLORS['beige'])
    
    # Draw initials
    # For simplicity, we'll create a text-based logo
    # In production, you'd use a proper font
    draw.ellipse([100, 100, 300, 300], fill=BRAND_COLORS['dark_grey'])
    
    # Convert to base64
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"

# Get logo (use base64 encoded placeholder or load from file)
def get_logo():
    """Get logo - tries local file first, then creates one"""
    # Try to load from file
    try:
        with open("logo.png", "rb") as f:
            logo_bytes = f.read()
            logo_b64 = base64.b64encode(logo_bytes).decode()
            return f"data:image/png;base64,{logo_b64}"
    except:
        # Create a logo if file doesn't exist
        return create_round_logo()

LOGO_URL = get_logo()

# ────────────────────────────────────────────────
# APP CONFIGURATION
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="LifeStory AI",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Initialize OpenAI client - USING GPT-4O-MINI for cost efficiency
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY")))
MODEL = "gpt-4o-mini"

# ────────────────────────────────────────────────
# DATABASE SETUP (PERSISTENCE)
# ────────────────────────────────────────────────
@st.cache_resource
def init_database():
    """Initialize SQLite database with proper schema"""
    conn = sqlite3.connect('life_story.db')
    cursor = conn.cursor()
    
    # Messages table (chat history)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        user_id TEXT,
        role TEXT,
        content TEXT,
        chapter_id INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_user_session (user_id, session_id)
    )
    ''')
    
    # Structured responses table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        chapter_id INTEGER,
        question TEXT,
        answer TEXT,
        privacy_level TEXT DEFAULT 'Family',
        media_attached INTEGER DEFAULT 0,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, chapter_id, question)
    )
    ''')
    
    # User progress table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_progress (
        user_id TEXT PRIMARY KEY,
        current_chapter INTEGER DEFAULT 0,
        current_question INTEGER DEFAULT 0,
        total_answers INTEGER DEFAULT 0,
        last_active DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Chapter summaries table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chapter_summaries (
        user_id TEXT,
        chapter_id INTEGER,
        summary TEXT,
        generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, chapter_id)
    )
    ''')
    
    conn.commit()
    return conn

conn = init_database()
cursor = conn.cursor()

# ────────────────────────────────────────────────
# CHAPTER STRUCTURE (First 3 chapters)
# ────────────────────────────────────────────────
CHAPTERS = [
    {
        "id": 1,
        "title": "Childhood Beginnings",
        "icon": "👶",
        "description": "Early memories, home, and formative experiences",
        "questions": [
            "What is your earliest memory?",
            "Can you describe your family home growing up?",
            "Who were the most influential people in your early years?",
            "What was school like for you?",
            "Were there any favourite games or hobbies?",
            "Is there a moment from childhood that shaped who you are?",
            "If you could give your younger self some advice, what would it be?"
        ],
        "color": BRAND_COLORS['beige']
    },
    {
        "id": 2,
        "title": "Family & Relationships",
        "icon": "👨‍👩‍👧‍👦",
        "description": "Family bonds, traditions, and personal connections",
        "questions": [
            "How would you describe your relationship with your parents?",
            "Are there any family traditions you remember fondly?",
            "What was your relationship like with siblings or close relatives?",
            "Can you share a story about a family celebration or challenge?",
            "How did your family shape your values?"
        ],
        "color": BRAND_COLORS['beige'] + "80"  # 50% opacity
    },
    {
        "id": 3,
        "title": "Education & Growth",
        "icon": "🎓",
        "description": "Learning journey, mentors, and personal development",
        "questions": [
            "What were your favourite subjects at school?",
            "Did you have any memorable teachers or mentors?",
            "How did you feel about exams and studying?",
            "Were there any big turning points in your education?",
            "Did you pursue further education or training?",
            "What advice would you give about learning?"
        ],
        "color": BRAND_COLORS['beige'] + "40"  # 25% opacity
    }
]

# ────────────────────────────────────────────────
# SESSION STATE MANAGEMENT
# ────────────────────────────────────────────────
def init_session_state():
    """Initialize or load session state"""
    defaults = {
        "messages": [],
        "current_chapter": 0,
        "current_question": 0,
        "responses": {},
        "interview_started": False,
        "user_id": "Guest",
        "session_id": f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "privacy_level": "Family"
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Initialize response structure
    for chapter in CHAPTERS:
        if chapter["id"] not in st.session_state.responses:
            st.session_state.responses[chapter["id"]] = {
                "title": chapter["title"],
                "questions": {},
                "summary": "",
                "completed": False,
                "answered_count": 0
            }
    
    # Load user data if exists
    load_user_data()

def load_user_data():
    """Load user data from database"""
    if st.session_state.user_id == "Guest":
        return
    
    # Load structured responses
    cursor.execute("""
        SELECT chapter_id, question, answer, privacy_level 
        FROM responses 
        WHERE user_id = ? 
        ORDER BY timestamp
    """, (st.session_state.user_id,))
    
    for chapter_id, question, answer, privacy_level in cursor.fetchall():
        if chapter_id not in st.session_state.responses:
            continue
        st.session_state.responses[chapter_id]["questions"][question] = {
            "answer": answer,
            "privacy_level": privacy_level,
            "timestamp": datetime.now().isoformat()
        }
        st.session_state.responses[chapter_id]["answered_count"] += 1
    
    # Load progress
    cursor.execute("""
        SELECT current_chapter, current_question, total_answers 
        FROM user_progress 
        WHERE user_id = ?
    """, (st.session_state.user_id,))
    
    row = cursor.fetchone()
    if row:
        st.session_state.current_chapter = row[0]
        st.session_state.current_question = row[1]
        # total_answers not currently used but stored for stats

def save_response(chapter_id, question, answer):
    """Save response to database"""
    user_id = st.session_state.user_id
    
    # Save to session state
    if chapter_id not in st.session_state.responses:
        st.session_state.responses[chapter_id] = {
            "title": CHAPTERS[chapter_id-1]["title"],
            "questions": {},
            "summary": "",
            "completed": False,
            "answered_count": 0
        }
    
    is_new = question not in st.session_state.responses[chapter_id]["questions"]
    st.session_state.responses[chapter_id]["questions"][question] = {
        "answer": answer,
        "timestamp": datetime.now().isoformat(),
        "privacy_level": st.session_state.privacy_level
    }
    
    if is_new:
        st.session_state.responses[chapter_id]["answered_count"] += 1
    
    # Save to database
    cursor.execute("""
        INSERT OR REPLACE INTO responses 
        (user_id, chapter_id, question, answer, privacy_level) 
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, chapter_id, question, answer, st.session_state.privacy_level))
    
    # Update user progress
    cursor.execute("""
        INSERT OR REPLACE INTO user_progress 
        (user_id, current_chapter, current_question, total_answers, last_active) 
        VALUES (?, ?, ?, COALESCE((SELECT total_answers + 1 FROM user_progress WHERE user_id = ?), 1), CURRENT_TIMESTAMP)
    """, (user_id, st.session_state.current_chapter, st.session_state.current_question, user_id))
    
    conn.commit()

def save_message(role, content):
    """Save message to database"""
    cursor.execute("""
        INSERT INTO messages 
        (session_id, user_id, role, content, chapter_id) 
        VALUES (?, ?, ?, ?, ?)
    """, (
        st.session_state.session_id,
        st.session_state.user_id,
        role,
        content,
        CHAPTERS[st.session_state.current_chapter]["id"]
    ))
    conn.commit()

# ────────────────────────────────────────────────
# AI FUNCTIONS
# ────────────────────────────────────────────────
def get_system_prompt():
    """Generate dynamic system prompt for current chapter/question"""
    current_chapter = CHAPTERS[st.session_state.current_chapter]
    current_question = current_chapter["questions"][st.session_state.current_question]
    
    return f"""You are a warm, empathetic biographer helping someone document their life story.

CURRENT CHAPTER: {current_chapter['title']}
CURRENT QUESTION: "{current_question}"

ROLE & TONE:
- Be warm, curious, and professional
- Use natural, conversational language
- Show genuine interest in their stories
- Be sensitive to emotional content
- Encourage vivid, detailed memories

CONVERSATION FLOW:
1. Acknowledge their answer warmly (1-2 sentences)
2. Ask ONE natural follow-up question if appropriate
3. Then transition to next question naturally

OCCASIONAL REMINDERS (use sparingly):
- "You can mark this as Private/Family/Public if you wish"
- "Would you like to add a photo to this memory?"
- "We can revisit this later if you prefer"

Keep responses concise (2-3 sentences max after acknowledgment).
Focus on drawing out authentic, meaningful stories."""

def generate_chapter_summary(chapter_id):
    """Generate AI summary of a completed chapter"""
    chapter = st.session_state.responses.get(chapter_id, {})
    if not chapter.get("questions"):
        return "This chapter hasn't been started yet."
    
    # Prepare conversation context
    qa_pairs = []
    for question, data in chapter["questions"].items():
        qa_pairs.append(f"Question: {question}\nAnswer: {data['answer'][:300]}...")
    
    prompt = f"""Please create a warm, narrative summary of this life story chapter titled "{chapter.get('title', 'Untitled')}".

Based on these responses:
{chr(10).join(qa_pairs)}

Write a 3-paragraph summary that:
1. Captures the key themes and emotions
2. Highlights important memories mentioned
3. Reads like a beautiful story excerpt
4. Maintains the person's authentic voice

Summary:"""
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a professional biographer summarizing life story chapters with warmth and authenticity."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        summary = response.choices[0].message.content
        
        # Save to database
        cursor.execute("""
            INSERT OR REPLACE INTO chapter_summaries 
            (user_id, chapter_id, summary) 
            VALUES (?, ?, ?)
        """, (st.session_state.user_id, chapter_id, summary))
        conn.commit()
        
        return summary
    except Exception as e:
        return f"Unable to generate summary: {str(e)}"

# ────────────────────────────────────────────────
# EXPORT FUNCTIONS
# ────────────────────────────────────────────────
class AutobiographyPDF(FPDF):
    """Custom PDF class for autobiography"""
    def __init__(self):
        super().__init__()
        self.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
        self.add_font('DejaVu', 'B', 'DejaVuSans-Bold.ttf', uni=True)
        self.set_auto_page_break(auto=True, margin=15)
        self.set_margins(20, 20, 20)
    
    def header(self):
        if self.page_no() == 1:
            # Title page
            self.set_font('DejaVu', 'B', 24)
            self.set_text_color(*hex_to_rgb(BRAND_COLORS['dark_grey']))
            self.cell(0, 40, "My Life Story", ln=True, align='C')
            self.ln(20)
            
            # User and date
            self.set_font('DejaVu', '', 14)
            self.cell(0, 10, f"By: {st.session_state.user_id}", ln=True, align='C')
            self.cell(0, 10, f"Generated: {datetime.now().strftime('%B %d, %Y')}", ln=True, align='C')
            self.ln(30)
        else:
            # Chapter headers
            self.set_font('DejaVu', 'B', 16)
            self.set_text_color(*hex_to_rgb(BRAND_COLORS['dark_grey']))
            self.cell(0, 10, f"Chapter {self.current_chapter}", ln=True)
            self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('DejaVu', '', 10)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')
    
    def add_chapter(self, chapter_id, chapter_data):
        self.current_chapter = chapter_id
        self.add_page()
        
        # Chapter title
        self.set_font('DejaVu', 'B', 18)
        self.set_text_color(*hex_to_rgb(BRAND_COLORS['dark_grey']))
        self.cell(0, 15, f"Chapter {chapter_id}: {chapter_data['title']}", ln=True)
        self.ln(10)
        
        # Questions and answers
        self.set_font('DejaVu', '', 12)
        self.set_text_color(0)
        
        for question, data in chapter_data["questions"].items():
            # Question
            self.set_font('DejaVu', 'B', 12)
            self.multi_cell(0, 8, f"Q: {question}")
            self.ln(2)
            
            # Answer
            self.set_font('DejaVu', '', 12)
            self.multi_cell(0, 8, f"A: {data['answer']}")
            self.ln(8)
        
        # Summary if exists
        if chapter_data.get("summary"):
            self.ln(5)
            self.set_font('DejaVu', 'I', 11)
            self.set_text_color(*hex_to_rgb(BRAND_COLORS['beige']))
            self.multi_cell(0, 8, f"Summary: {chapter_data['summary']}")
            self.ln(10)

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 8:  # With alpha
        hex_color = hex_color[:6]
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_pdf():
    """Create professional PDF document"""
    pdf = AutobiographyPDF()
    
    # Add cover page
    pdf.add_page()
    
    # Add chapters
    for chapter_id in sorted(st.session_state.responses.keys()):
        chapter_data = st.session_state.responses[chapter_id]
        if chapter_data.get("questions"):
            pdf.add_chapter(chapter_id, chapter_data)
    
    return pdf.output(dest='S').encode('latin-1')

def export_json():
    """Export as structured JSON"""
    export_data = {
        "metadata": {
            "project": "LifeStory AI Autobiography",
            "version": "1.0",
            "user_id": st.session_state.user_id,
            "export_date": datetime.now().isoformat(),
            "total_chapters": len(CHAPTERS),
            "chapters_completed": sum(1 for cid in st.session_state.responses 
                                    if st.session_state.responses[cid].get("completed", False)),
            "total_answers": sum(st.session_state.responses[cid].get("answered_count", 0) 
                               for cid in st.session_state.responses)
        },
        "chapters": st.session_state.responses
    }
    return json.dumps(export_data, indent=2)

def export_text():
    """Export as formatted text manuscript"""
    text = "=" * 70 + "\n"
    text += " " * 20 + "MY LIFE STORY\n"
    text += "=" * 70 + "\n\n"
    text += f"Author: {st.session_state.user_id}\n"
    text += f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n"
    
    for chapter_id in sorted(st.session_state.responses.keys()):
        chapter = st.session_state.responses[chapter_id]
        if not chapter.get("questions"):
            continue
        
        text += "\n" + "=" * 70 + "\n"
        text += f"CHAPTER {chapter_id}: {chapter['title'].upper()}\n"
        text += "=" * 70 + "\n\n"
        
        for question, data in chapter["questions"].items():
            text += f"Q: {question}\n"
            text += f"A: {data['answer']}\n\n"
        
        if chapter.get("summary"):
            text += "―" * 50 + "\n"
            text += "SUMMARY:\n"
            text += chapter['summary'] + "\n"
            text += "―" * 50 + "\n"
    
    text += "\n" + "=" * 70 + "\n"
    text += "END OF AUTOBIOGRAPHY\n"
    text += "=" * 70 + "\n"
    
    return text

# ────────────────────────────────────────────────
# VOICE INPUT SIMULATION (Placeholder for future)
# ────────────────────────────────────────────────
def voice_input_demo():
    """Show voice input demo (real implementation requires Whisper)"""
    st.info("🎤 **Voice Input**")
    st.write("Coming soon: Dictate your answers using speech-to-text.")
    st.write("Future integration will use OpenAI's Whisper API for accurate transcription.")
    
    # Simulated recording button
    if st.button("🎤 Try Voice Demo", use_container_width=True):
        st.session_state.demo_voice = True
        st.rerun()
    
    if st.session_state.get("demo_voice"):
        st.success("Voice recording simulated! In production, this would transcribe your speech to text.")

# ────────────────────────────────────────────────
# MAIN APPLICATION UI
# ────────────────────────────────────────────────
init_session_state()

# Header Section
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.markdown(f"""
    <div class="main-header">
        <div class="logo-container">
            <img src="{LOGO_URL}" class="logo-img" alt="LifeStory AI Logo">
        </div>
        <h1 style="text-align: center; margin: 0; font-size: 2.8rem;">LifeStory AI</h1>
        <p style="text-align: center; margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">
            Preserve Your Legacy • Share Your Story
        </p>
    </div>
    """, unsafe_allow_html=True)

# Main layout
main_col, side_col = st.columns([3, 1])

with side_col:
    # User Profile Section
    st.markdown("### 👤 Your Profile")
    
    new_user_id = st.text_input(
        "Your Name:",
        value=st.session_state.user_id,
        key="user_id_input",
        help="Enter your name to save progress"
    )
    
    if new_user_id != st.session_state.user_id:
        st.session_state.user_id = new_user_id
        load_user_data()
        st.rerun()
    
    st.selectbox(
        "Default Privacy:",
        ["Private", "Family", "Public"],
        index=1,
        key="privacy_level",
        help="Who can see your stories?"
    )
    
    st.divider()
    
    # Chapter Navigation
    st.markdown("### 📖 Chapters")
    
    for i, chapter in enumerate(CHAPTERS):
        chapter_responses = st.session_state.responses.get(chapter["id"], {})
        progress = chapter_responses.get("answered_count", 0) / len(chapter["questions"])
        
        col_a, col_b = st.columns([3, 1])
        with col_a:
            is_current = i == st.session_state.current_chapter
            btn_type = "primary" if is_current else "secondary"
            
            if st.button(
                f"{chapter['icon']} {chapter['title']}",
                key=f"nav_{i}",
                use_container_width=True,
                type=btn_type
            ):
                st.session_state.current_chapter = i
                st.session_state.current_question = 0
                st.rerun()
        
        with col_b:
            st.caption(f"{chapter_responses.get('answered_count', 0)}/{len(chapter['questions'])}")
        
        st.progress(min(progress, 1.0))
    
    st.divider()
    
    # Quick Actions
    st.markdown("### ⚡ Quick Actions")
    
    if st.button("🔍 Generate Chapter Summary", use_container_width=True):
        current_id = CHAPTERS[st.session_state.current_chapter]["id"]
        summary = generate_chapter_summary(current_id)
        st.session_state.responses[current_id]["summary"] = summary
        st.session_state.responses[current_id]["completed"] = True
        st.success(f"Summary generated for Chapter {current_id}!")
    
    if st.button("📊 View Statistics", use_container_width=True):
        total_answers = sum(r.get("answered_count", 0) for r in st.session_state.responses.values())
        completed_chapters = sum(1 for r in st.session_state.responses.values() if r.get("completed", False))
        st.info(f"**Progress:** {total_answers} answers across {completed_chapters}/{len(CHAPTERS)} chapters")
    
    st.divider()
    
    # Export Section
    st.markdown("### 📤 Export Options")
    export_format = st.radio("Format:", ["PDF", "Text", "JSON"], horizontal=True)
    
    if st.button(f"📥 Download {export_format}", use_container_width=True, type="primary"):
        with st.spinner(f"Creating {export_format} document..."):
            if export_format == "PDF":
                pdf_bytes = create_pdf()
                st.download_button(
                    label="⬇️ Download PDF",
                    data=pdf_bytes,
                    file_name=f"LifeStory_{st.session_state.user_id}_{datetime.now().date()}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            elif export_format == "Text":
                st.download_button(
                    label="⬇️ Download Text",
                    data=export_text(),
                    file_name=f"LifeStory_{st.session_state.user_id}_{datetime.now().date()}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            else:
                st.download_button(
                    label="⬇️ Download JSON",
                    data=export_json(),
                    file_name=f"LifeStory_{st.session_state.user_id}_{datetime.now().date()}.json",
                    mime="application/json",
                    use_container_width=True
                )
    
    st.divider()
    
    # Voice Input Demo
    voice_input_demo()

with main_col:
    # Current Chapter Display
    current_chapter = CHAPTERS[st.session_state.current_chapter]
    chapter_responses = st.session_state.responses.get(current_chapter["id"], {})
    
    # Progress header
    col_a, col_b, col_c = st.columns([2, 1, 1])
    with col_a:
        st.markdown(f"### {current_chapter['icon']} {current_chapter['title']}")
        st.caption(current_chapter['description'])
    with col_b:
        progress = chapter_responses.get("answered_count", 0) / len(current_chapter["questions"])
        st.metric("Progress", f"{int(progress * 100)}%")
    with col_c:
        if chapter_responses.get("completed", False):
            st.success("✓ Completed")
        else:
            st.info("In Progress")
    
    # Current question
    current_question = current_chapter["questions"][st.session_state.current_question]
    st.markdown(f"""
    <div style="background-color: {BRAND_COLORS['beige']}30; padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
        <h4 style="margin: 0; color: {BRAND_COLORS['dark_grey']};">Question {st.session_state.current_question + 1}/{len(current_chapter['questions'])}</h4>
        <p style="font-size: 1.1rem; margin: 0.5rem 0 0 0;">{current_question}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Question navigation
    q_col1, q_col2, q_col3 = st.columns([1, 2, 1])
    with q_col1:
        if st.button("← Previous", disabled=st.session_state.current_question == 0):
            st.session_state.current_question = max(0, st.session_state.current_question - 1)
            st.rerun()
    with q_col3:
        if st.button("Next →", disabled=st.session_state.current_question >= len(current_chapter["questions"]) - 1):
            st.session_state.current_question = min(len(current_chapter["questions"]) - 1, 
                                                   st.session_state.current_question + 1)
            st.rerun()
    
    # Chat Display
    st.markdown("---")
    st.markdown("### 💬 Conversation")
    
    # Display last 6 messages
    for message in st.session_state.messages[-6:]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Auto-start if new session
    if not st.session_state.interview_started and len(st.session_state.messages) == 0:
        welcome_message = f"""Hello **{st.session_state.user_id}**! I'm your personal biographer.

I'll guide you through {len(CHAPTERS)} chapters of your life story, starting with **{current_chapter['title']}**.

Let's begin with your first memory:

**{current_question}**"""
        
        st.session_state.messages.append({"role": "assistant", "content": welcome_message})
        save_message("assistant", welcome_message)
        st.session_state.interview_started = True
        st.rerun()
    
    # User Input
    st.markdown("---")
    st.markdown("### ✍️ Your Answer")
    
    # Text area for response
    user_answer = st.text_area(
        "Type your response here:",
        height=150,
        key="user_input",
        label_visibility="collapsed",
        placeholder="Take your time to share your story..."
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Submit Answer", type="primary", use_container_width=True):
            if user_answer.strip():
                # Save and process response
                st.session_state.messages.append({"role": "user", "content": user_answer})
                save_message("user", user_answer)
                save_response(current_chapter["id"], current_question, user_answer)
                
                # Generate AI response
                with st.spinner("Thinking..."):
                    try:
                        response = client.chat.completions.create(
                            model=MODEL,
                            messages=[
                                {"role": "system", "content": get_system_prompt()},
                                *st.session_state.messages[-3:]  # Last few messages for context
                            ],
                            temperature=0.7,
                            max_tokens=250
                        )
                        
                        ai_response = response.choices[0].message.content
                        st.session_state.messages.append({"role": "assistant", "content": ai_response})
                        save_message("assistant", ai_response)
                        
                        # Move to next question if not the last
                        if st.session_state.current_question < len(current_chapter["questions"]) - 1:
                            st.session_state.current_question += 1
                        else:
                            st.session_state.responses[current_chapter["id"]]["completed"] = True
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Sorry, I encountered an error: {str(e)}")
            else:
                st.warning("Please write something before submitting.")

# Footer
st.markdown("""
<div class="brand-footer">
    <div style="display: flex; justify-content: center; align-items: center; gap: 1rem; margin-bottom: 1rem;">
        <div style="width: 40px; height: 40px; border-radius: 50%; background-color: white; display: flex; align-items: center; justify-content: center;">
            <span style="color: #3e403f; font-weight: bold;">LS</span>
        </div>
        <div>
            <h3 style="margin: 0; color: white;">LifeStory AI</h3>
            <p style="margin: 0; opacity: 0.8; font-size: 0.9rem;">Preserving personal histories for future generations</p>
        </div>
    </div>
    <p style="margin: 0; font-size: 0.9rem; opacity: 0.7;">
        Built with ❤️ using GPT-4o-mini • All data stored locally on your device • © 2024 LifeStory AI
    </p>
</div>
""", unsafe_allow_html=True)

# Close database connection on app end
conn.close()

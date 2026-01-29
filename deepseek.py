import streamlit as st
import json
from datetime import datetime
from openai import OpenAI
import os
import sqlite3
import base64
import io
from PIL import Image, ImageDraw

# Try to import PDF module with fallback
try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

# ────────────────────────────────────────────────
# APP CONFIGURATION
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="LifeStory AI",
    page_icon="📖",
    layout="wide"
)

# ────────────────────────────────────────────────
# BRANDING CONFIGURATION
# ────────────────────────────────────────────────
BRAND_COLORS = {
    "beige": "#b5aa96",
    "background_grey": "#c7c7c4", 
    "dark_grey": "#3e403f",
    "light": "#f8f9fa"
}

# Your logo URL
LOGO_URL = "https://menuhunterai.com/wp-content/uploads/2026/01/logo.png"

# Custom CSS
CUSTOM_CSS = f"""
<style>
    .main {{
        background-color: {BRAND_COLORS['background_grey']};
    }}
    
    .main-header {{
        background: linear-gradient(135deg, {BRAND_COLORS['dark_grey']} 0%, #2d2f2e 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }}
    
    .stButton > button {{
        background-color: {BRAND_COLORS['dark_grey']};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
    }}
    
    .chapter-card {{
        background-color: {BRAND_COLORS['beige']}20;
        padding: 1rem;
        border-left: 4px solid {BRAND_COLORS['dark_grey']};
        border-radius: 8px;
        margin-bottom: 0.75rem;
    }}
    
    .brand-footer {{
        background-color: {BRAND_COLORS['dark_grey']};
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin-top: 3rem;
        text-align: center;
    }}
    
    .logo-img {{
        width: 120px;
        height: 120px;
        border-radius: 50%;
        object-fit: cover;
        border: 4px solid {BRAND_COLORS['beige']};
    }}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ────────────────────────────────────────────────
# INITIALIZE OPENAI
# ────────────────────────────────────────────────
api_key = st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY"))
if not api_key:
    st.error("OpenAI API key not found. Please set it in Streamlit secrets or environment variables.")
    st.stop()

client = OpenAI(api_key=api_key)
MODEL = "gpt-4o-mini"

# ────────────────────────────────────────────────
# DATABASE SETUP
# ────────────────────────────────────────────────
@st.cache_resource
def init_database():
    conn = sqlite3.connect('life_story.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS responses (
        user_id TEXT,
        chapter_id INTEGER,
        question TEXT,
        answer TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, chapter_id, question)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        user_id TEXT,
        role TEXT,
        content TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    return conn

conn = init_database()
cursor = conn.cursor()

# ────────────────────────────────────────────────
# CHAPTER STRUCTURE
# ────────────────────────────────────────────────
CHAPTERS = [
    {
        "id": 1,
        "title": "Childhood Beginnings",
        "icon": "👶",
        "questions": [
            "What is your earliest memory?",
            "Can you describe your family home growing up?",
            "Who were the most influential people in your early years?",
            "What was school like for you?",
            "Were there any favourite games or hobbies?",
            "Is there a moment from childhood that shaped who you are?",
            "If you could give your younger self some advice, what would it be?"
        ]
    },
    {
        "id": 2,
        "title": "Family & Relationships",
        "icon": "👨‍👩‍👧‍👦", 
        "questions": [
            "How would you describe your relationship with your parents?",
            "Are there any family traditions you remember fondly?",
            "What was your relationship like with siblings or close relatives?",
            "Can you share a story about a family celebration or challenge?",
            "How did your family shape your values?"
        ]
    },
    {
        "id": 3,
        "title": "Education & Growth",
        "icon": "🎓",
        "questions": [
            "What were your favourite subjects at school?",
            "Did you have any memorable teachers or mentors?",
            "How did you feel about exams and studying?",
            "Were there any big turning points in your education?",
            "Did you pursue further education or training?",
            "What advice would you give about learning?"
        ]
    }
]

# ────────────────────────────────────────────────
# SESSION STATE MANAGEMENT
# ────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.current_chapter = 0
    st.session_state.current_question = 0
    st.session_state.responses = {}
    st.session_state.interview_started = False
    st.session_state.user_id = "Guest"
    
    # Initialize response structure
    for chapter in CHAPTERS:
        st.session_state.responses[chapter["id"]] = {
            "title": chapter["title"],
            "questions": {},
            "answered_count": 0
        }

def load_user_data():
    """Load user data from database"""
    if st.session_state.user_id == "Guest":
        return
    
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
        st.session_state.responses[chapter_id]["answered_count"] += 1

def save_response(chapter_id, question, answer):
    """Save response to database"""
    user_id = st.session_state.user_id
    
    # Save to session state
    if chapter_id not in st.session_state.responses:
        st.session_state.responses[chapter_id] = {
            "title": CHAPTERS[chapter_id-1]["title"],
            "questions": {},
            "answered_count": 0
        }
    
    is_new = question not in st.session_state.responses[chapter_id]["questions"]
    st.session_state.responses[chapter_id]["questions"][question] = {
        "answer": answer,
        "timestamp": datetime.now().isoformat()
    }
    
    if is_new:
        st.session_state.responses[chapter_id]["answered_count"] += 1
    
    # Save to database
    cursor.execute("""
        INSERT OR REPLACE INTO responses 
        (user_id, chapter_id, question, answer) 
        VALUES (?, ?, ?, ?)
    """, (user_id, chapter_id, question, answer))
    
    # Save message
    cursor.execute("""
        INSERT INTO messages 
        (user_id, role, content) 
        VALUES (?, ?, ?)
    """, (user_id, "user", answer))
    
    conn.commit()

# ────────────────────────────────────────────────
# AI FUNCTIONS
# ────────────────────────────────────────────────
def get_system_prompt():
    """Generate system prompt"""
    current_chapter = CHAPTERS[st.session_state.current_chapter]
    current_question = current_chapter["questions"][st.session_state.current_question]
    
    return f"""You are a warm, empathetic biographer helping someone document their life story.

We're discussing: {current_question}

Please:
1. Listen actively to their response
2. Acknowledge it warmly (1-2 sentences)
3. Ask ONE natural follow-up question if appropriate
4. Keep the conversation flowing naturally

Tone: Kind, curious, professional
Goal: Draw out authentic, detailed memories"""

def generate_ai_response(user_input):
    """Generate AI response"""
    try:
        # Get conversation context
        context_messages = [
            {"role": "system", "content": get_system_prompt()}
        ]
        
        # Add recent messages
        for msg in st.session_state.messages[-4:]:
            context_messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add current input
        context_messages.append({"role": "user", "content": user_input})
        
        # Generate response
        response = client.chat.completions.create(
            model=MODEL,
            messages=context_messages,
            temperature=0.7,
            max_tokens=250
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return "Thank you for sharing that. Tell me more..."

# ────────────────────────────────────────────────
# EXPORT FUNCTIONS
# ────────────────────────────────────────────────
def export_json():
    """Export as JSON"""
    export_data = {
        "user_id": st.session_state.user_id,
        "export_date": datetime.now().isoformat(),
        "chapters": st.session_state.responses
    }
    return json.dumps(export_data, indent=2)

def export_text():
    """Export as text"""
    text = f"My Life Story\n{'='*60}\n\n"
    text += f"Author: {st.session_state.user_id}\n"
    text += f"Date: {datetime.now().strftime('%B %d, %Y')}\n\n"
    
    for chapter_id in sorted(st.session_state.responses.keys()):
        chapter = st.session_state.responses[chapter_id]
        if not chapter.get("questions"):
            continue
        
        text += f"\nCHAPTER {chapter_id}: {chapter['title']}\n"
        text += "-" * 40 + "\n\n"
        
        for question, data in chapter["questions"].items():
            text += f"Q: {question}\n"
            text += f"A: {data['answer']}\n\n"
    
    return text

def export_html():
    """Export as HTML"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>My Life Story - {st.session_state.user_id}</title>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                line-height: 1.6; 
                max-width: 800px; 
                margin: 0 auto; 
                padding: 40px;
                background-color: {BRAND_COLORS['background_grey']};
            }}
            .header {{ 
                text-align: center; 
                margin-bottom: 40px;
                padding-bottom: 20px;
                border-bottom: 3px solid {BRAND_COLORS['beige']};
            }}
            h1 {{ color: {BRAND_COLORS['dark_grey']}; }}
            .chapter {{ 
                margin: 40px 0;
                padding: 20px;
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>My Life Story</h1>
            <p>Author: {st.session_state.user_id}</p>
            <p>Generated: {datetime.now().strftime('%B %d, %Y')}</p>
        </div>
    """
    
    for chapter_id in sorted(st.session_state.responses.keys()):
        chapter = st.session_state.responses[chapter_id]
        if not chapter.get("questions"):
            continue
        
        html += f"""
        <div class="chapter">
            <h2>Chapter {chapter_id}: {chapter['title']}</h2>
        """
        
        for question, data in chapter["questions"].items():
            html += f"""
            <p><strong>Q: {question}</strong></p>
            <p>A: {data['answer']}</p>
            <hr>
            """
        
        html += "</div>"
    
    html += """
    </body>
    </html>
    """
    
    return html

# PDF Export (if available)
if FPDF_AVAILABLE:
    def create_pdf():
        """Create PDF"""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="My Life Story", ln=1, align='C')
        pdf.ln(10)
        
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 10, txt=f"By: {st.session_state.user_id}", ln=1, align='C')
        pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%B %d, %Y')}", ln=1, align='C')
        pdf.ln(15)
        
        # Chapters
        for chapter_id in sorted(st.session_state.responses.keys()):
            chapter = st.session_state.responses[chapter_id]
            if not chapter.get("questions"):
                continue
            
            # Chapter header
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt=f"Chapter {chapter_id}: {chapter['title']}", ln=1)
            pdf.ln(5)
            
            # Questions and answers
            pdf.set_font("Arial", size=11)
            for question, data in chapter["questions"].items():
                pdf.set_font("Arial", 'B', 11)
                pdf.multi_cell(0, 8, txt=f"Q: {question}")
                pdf.set_font("Arial", size=11)
                pdf.multi_cell(0, 8, txt=f"A: {data['answer']}")
                pdf.ln(3)
            
            pdf.ln(10)
        
        return pdf.output(dest='S').encode('latin-1')

# ────────────────────────────────────────────────
# HEADER SECTION
# ────────────────────────────────────────────────
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.markdown(f"""
    <div class="main-header">
        <div style="text-align: center;">
            <img src="{LOGO_URL}" class="logo-img" alt="LifeStory AI Logo">
        </div>
        <h1 style="text-align: center; margin: 0;">LifeStory AI</h1>
        <p style="text-align: center; margin: 0.5rem 0 0 0; opacity: 0.9;">
            Preserve Your Legacy • Share Your Story
        </p>
    </div>
    """, unsafe_allow_html=True)

# ────────────────────────────────────────────────
# MAIN LAYOUT
# ────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])

with col2:  # Sidebar
    # User Profile
    st.markdown("### 👤 Your Profile")
    
    new_user_id = st.text_input(
        "Your Name:",
        value=st.session_state.user_id,
        key="user_id_input"
    )
    
    if new_user_id != st.session_state.user_id:
        st.session_state.user_id = new_user_id
        load_user_data()
        st.rerun()
    
    st.divider()
    
    # Chapter Navigation
    st.markdown("### 📖 Chapters")
    
    for i, chapter in enumerate(CHAPTERS):
        chapter_data = st.session_state.responses.get(chapter["id"], {})
        answered = chapter_data.get("answered_count", 0)
        total = len(chapter["questions"])
        
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
        
        st.progress(min(answered / total, 1.0) if total > 0 else 0)
        st.caption(f"{answered}/{total} answered")
    
    st.divider()
    
    # Export Section
    st.markdown("### 📤 Export Options")
    
    if not FPDF_AVAILABLE:
        export_formats = ["HTML", "Text", "JSON"]
    else:
        export_formats = ["PDF", "HTML", "Text", "JSON"]
    
    export_format = st.radio("Format:", export_formats)
    
    if st.button("📥 Export Now", use_container_width=True, type="primary"):
        with st.spinner(f"Creating {export_format} document..."):
            if export_format == "PDF" and FPDF_AVAILABLE:
                pdf_bytes = create_pdf()
                st.download_button(
                    label="Download PDF",
                    data=pdf_bytes,
                    file_name=f"LifeStory_{st.session_state.user_id}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            elif export_format == "HTML":
                st.download_button(
                    label="Download HTML",
                    data=export_html(),
                    file_name=f"LifeStory_{st.session_state.user_id}.html",
                    mime="text/html",
                    use_container_width=True
                )
            elif export_format == "Text":
                st.download_button(
                    label="Download Text",
                    data=export_text(),
                    file_name=f"LifeStory_{st.session_state.user_id}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            else:  # JSON
                st.download_button(
                    label="Download JSON",
                    data=export_json(),
                    file_name=f"LifeStory_{st.session_state.user_id}.json",
                    mime="application/json",
                    use_container_width=True
                )

with col1:  # Main content
    # Current Chapter
    current_chapter = CHAPTERS[st.session_state.current_chapter]
    chapter_data = st.session_state.responses.get(current_chapter["id"], {})
    
    # Progress header
    st.markdown(f"### {current_chapter['icon']} {current_chapter['title']}")
    
    # Progress bar
    answered = chapter_data.get("answered_count", 0)
    total = len(current_chapter["questions"])
    st.progress(min(answered / total, 1.0) if total > 0 else 0)
    st.caption(f"Question {answered + 1} of {total}")
    
    # Current question
    current_question = current_chapter["questions"][st.session_state.current_question]
    st.markdown(f"""
    <div style="background-color: {BRAND_COLORS['beige']}30; padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
        <h4 style="margin: 0; color: {BRAND_COLORS['dark_grey']};">Question {st.session_state.current_question + 1}</h4>
        <p style="font-size: 1.1rem; margin: 0.5rem 0 0 0;">{current_question}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Question navigation
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_a:
        if st.button("← Previous", disabled=st.session_state.current_question == 0):
            st.session_state.current_question = max(0, st.session_state.current_question - 1)
            st.rerun()
    with col_c:
        if st.button("Next →", disabled=st.session_state.current_question >= total - 1):
            st.session_state.current_question = min(total - 1, st.session_state.current_question + 1)
            st.rerun()
    
    # Chat Display
    st.markdown("---")
    st.markdown("### 💬 Conversation")
    
    # Display messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Auto-start if new session
    if not st.session_state.interview_started and len(st.session_state.messages) == 0:
        welcome_message = f"""Hello **{st.session_state.user_id}**! I'm your personal biographer.

I'll guide you through {len(CHAPTERS)} chapters of your life story, starting with **{current_chapter['title']}**.

**{current_question}**"""
        
        st.session_state.messages.append({"role": "assistant", "content": welcome_message})
        st.session_state.interview_started = True
        st.rerun()
    
    # User Input
    st.markdown("---")
    user_input = st.chat_input("Type your answer here...")
    
    if user_input:
        # Save user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Save response
        save_response(current_chapter["id"], current_question, user_input)
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                ai_response = generate_ai_response(user_input)
                st.markdown(ai_response)
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
        
        # Move to next question if not the last
        if st.session_state.current_question < total - 1:
            st.session_state.current_question += 1
            st.rerun()

# ────────────────────────────────────────────────
# FOOTER
# ────────────────────────────────────────────────
st.markdown("""
<div class="brand-footer">
    <h3 style="margin: 0; color: white;">LifeStory AI</h3>
    <p style="margin: 0; opacity: 0.8;">Preserving personal histories for future generations</p>
    <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem; opacity: 0.7;">
        Built with ❤️ • All data stored locally • © 2024
    </p>
</div>
""", unsafe_allow_html=True)

# Close database connection
conn.close()

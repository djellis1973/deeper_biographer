import streamlit as st
import json
from datetime import datetime
from openai import OpenAI
import os
import sqlite3
import re  # For word counting

# ────────────────────────────────────────────────
# CLEAN BRANDING WITH LOGO - FIXED SPACING
# ────────────────────────────────────────────────
LOGO_URL = "https://menuhunterai.com/wp-content/uploads/2026/01/logo.png"

# Enhanced CSS with traffic light system
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
</style>
""", unsafe_allow_html=True)

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY")))

# Define the chapter structure with professional guidance text
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
        "word_target": 800  # New: word count target per chapter
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
        "word_target": 700  # New: word count target per chapter
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
        "word_target": 600  # New: word count target per chapter
    }
]

# Initialize database
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

# Initialize session state
if "responses" not in st.session_state:
    st.session_state.current_chapter = 0
    st.session_state.current_question = 0
    st.session_state.responses = {}
    st.session_state.user_id = "Guest"
    st.session_state.chapter_conversations = {}  # {chapter_id: {question_text: conversation}}
    st.session_state.editing = None  # (chapter_id, question_text, message_index)
    st.session_state.edit_text = ""
    st.session_state.ghostwriter_mode = True
    st.session_state.show_speech = True
    st.session_state.speech_text = ""
    st.session_state.speech_preview = ""
    
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
        st.session_state.chapter_conversations[chapter_id] = {}  # Empty dict for questions
    
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

# Load user data from database
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

# Save response to database
def save_response(chapter_id, question, answer):
    user_id = st.session_state.user_id
    
    # Save to session state
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
    
    # Save to database
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

# Save word target to database
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

# Calculate word count for a chapter
def calculate_chapter_word_count(chapter_id):
    """Calculate total words for a chapter"""
    total_words = 0
    chapter_data = st.session_state.responses.get(chapter_id, {})
    conversations = st.session_state.chapter_conversations.get(chapter_id, {})
    
    # Count words from saved responses
    for question, answer_data in chapter_data.get("questions", {}).items():
        if answer_data.get("answer"):
            total_words += len(re.findall(r'\w+', answer_data["answer"]))
    
    # Count words from conversations
    for question_text, conv in conversations.items():
        for msg in conv:
            if msg["role"] == "user":
                total_words += len(re.findall(r'\w+', msg["content"]))
    
    return total_words

# Get traffic light color and emoji
def get_traffic_light(chapter_id):
    """Return traffic light color and emoji based on word count progress"""
    current_count = calculate_chapter_word_count(chapter_id)
    target = st.session_state.responses[chapter_id].get("word_target", 500)
    
    if target == 0:
        return "#2ecc71", "🟢", 100  # Green if no target
    
    progress = (current_count / target) * 100
    
    if progress >= 100:
        return "#2ecc71", "🟢", progress  # Green
    elif progress >= 70:
        return "#f39c12", "🟡", progress  # Yellow
    else:
        return "#e74c3c", "🔴", progress  # Red

# Clear entire chapter
def clear_chapter(chapter_id):
    user_id = st.session_state.user_id
    
    # Clear from session state
    if chapter_id in st.session_state.responses:
        st.session_state.responses[chapter_id]["questions"] = {}
        st.session_state.responses[chapter_id]["completed"] = False
        st.session_state.responses[chapter_id]["summary"] = ""
    
    # Clear conversation for this chapter
    if chapter_id in st.session_state.chapter_conversations:
        st.session_state.chapter_conversations[chapter_id] = {}
    
    # Clear from database
    try:
        conn = sqlite3.connect('life_story.db')
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM responses 
            WHERE user_id = ? AND chapter_id = ?
        """, (user_id, chapter_id))
        conn.commit()
        conn.close()
    except:
        pass

# Clear everything (reset)
def clear_all():
    user_id = st.session_state.user_id
    
    # Clear session state
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
    
    st.session_state.current_chapter = 0
    st.session_state.current_question = 0
    st.session_state.editing = None
    st.session_state.edit_text = ""
    st.session_state.speech_text = ""
    st.session_state.speech_preview = ""
    
    # Clear database
    try:
        conn = sqlite3.connect('life_story.db')
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM responses 
            WHERE user_id = ?
        """, (user_id,))
        conn.commit()
        conn.close()
    except:
        pass

# PROFESSIONAL GHOSTWRITER SYSTEM PROMPT
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
        # Legacy mode (original behavior)
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

# Generate chapter summary
def generate_chapter_summary(chapter_id):
    chapter = st.session_state.responses.get(chapter_id, {})
    if not chapter.get("questions"):
        return "No responses yet for this chapter."
    
    questions_answers = []
    for q, data in chapter["questions"].items():
        questions_answers.append(f"Q: {q}\nA: {data.get('answer', 'No answer')}")
    
    if not questions_answers:
        return "No responses yet for this chapter."
    
    prompt = f"""Based on these interview responses for Chapter {chapter_id}: {chapter.get('title', 'Untitled')}, create a concise 3-4 paragraph summary capturing the key themes and stories.

Responses:
{"\n".join(questions_answers)}

Summary:"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a professional biographer summarizing life story chapters."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Could not generate summary: {str(e)}"

# Clean speech text
def clean_speech_text(text):
    """Clean up speech recognition output"""
    if not text:
        return text
    
    # Remove common speech artifacts
    text = text.strip()
    
    # Fix common speech recognition errors
    replacements = {
        "uh": "",
        "um": "",
        "er": "",
        "ah": "",
        "like, ": "",
        "you know, ": "",
        "sort of ": "",
        "kind of ": "",
        "  ": " "  # Double spaces
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Capitalize first letter
    if text and len(text) > 0:
        text = text[0].upper() + text[1:] if text[0].isalpha() else text
    
    # Ensure ends with punctuation if it doesn't
    if text and text[-1] not in ['.', '!', '?', ',', ';', ':']:
        text += '.'
    
    return text

# Export functions
def export_json():
    """Export all responses as JSON - includes ALL chapters and ALL conversation answers"""
    export_data = {
        "metadata": {
            "project": "LifeStory AI",
            "user_id": st.session_state.user_id,
            "export_date": datetime.now().isoformat(),
            "export_format": "JSON",
            "interview_style": "Professional Ghostwriter" if st.session_state.ghostwriter_mode else "Standard"
        },
        "chapters": {}
    }
    
    for chapter in CHAPTERS:
        chapter_id = chapter["id"]
        chapter_data = st.session_state.responses.get(chapter_id, {})
        conversations = st.session_state.chapter_conversations.get(chapter_id, {})
        
        # Get ALL Q&A for this chapter
        chapter_qa = {}
        chapter_full_conversations = {}
        
        # Process each question in the chapter
        for question_text in chapter["questions"]:
            # Get main answer from saved responses
            main_answer = ""
            if question_text in chapter_data.get("questions", {}):
                main_answer = chapter_data["questions"][question_text].get("answer", "")
            
            # Get full conversation for this question
            full_conversation = []
            if question_text in conversations:
                # Extract all user answers from conversation
                user_answers = []
                conversation_history = []
                for msg in conversations[question_text]:
                    conversation_history.append({
                        "role": msg["role"],
                        "content": msg["content"],
                        "timestamp": datetime.now().isoformat() if msg["role"] == "user" else ""
                    })
                    if msg["role"] == "user":
                        user_answers.append(msg["content"])
                
                # Store full conversation
                if conversation_history:
                    chapter_full_conversations[question_text] = conversation_history
                
                # If we have user answers, use them
                if user_answers:
                    chapter_qa[question_text] = "\n".join(user_answers)
                elif main_answer:
                    chapter_qa[question_text] = main_answer
            elif main_answer:
                chapter_qa[question_text] = main_answer
        
        # Include chapters with content
        export_data["chapters"][str(chapter_id)] = {
            "title": chapter["title"],
            "guidance": chapter.get("guidance", ""),
            "questions": chapter_qa,
            "full_conversations": chapter_full_conversations,
            "summary": chapter_data.get("summary", ""),
            "completed": chapter_data.get("completed", False),
            "word_count": calculate_chapter_word_count(chapter_id),
            "word_target": chapter_data.get("word_target", 500),
            "total_questions": len(chapter["questions"]),
            "answered_questions": len(chapter_qa)
        }
    
    return json.dumps(export_data, indent=2)

def export_text():
    """Export all responses as formatted text - includes ALL chapters and conversations"""
    interview_style = "Professional Ghostwriter Interview" if st.session_state.ghostwriter_mode else "Standard Interview"
    
    text = "=" * 60 + "\n"
    text += "MY LIFE STORY\n"
    text += "=" * 60 + "\n\n"
    text += f"Author: {st.session_state.user_id}\n"
    text += f"Interview Style: {interview_style}\n"
    text += f"Generated: {datetime.now().strftime('%d %B %Y at %H:%M')}\n\n"
    
    has_content = False
    
    for chapter in CHAPTERS:
        chapter_id = chapter["id"]
        chapter_data = st.session_state.responses.get(chapter_id, {})
        conversations = st.session_state.chapter_conversations.get(chapter_id, {})
        
        # Check if this chapter has any content
        chapter_has_content = False
        chapter_content = []
        
        for question_text in chapter["questions"]:
            has_saved_answer = question_text in chapter_data.get("questions", {})
            has_conversation = question_text in conversations and conversations[question_text]
            
            if has_saved_answer or has_conversation:
                chapter_has_content = True
                q_block = f"Q: {question_text}\n"
                
                if has_conversation:
                    user_answers = []
                    ai_messages = []
                    
                    for msg in conversations[question_text]:
                        if msg["role"] == "user":
                            user_answers.append(f"A: {msg['content']}")
                        elif msg["role"] == "assistant":
                            if not ("I'd love to hear your thoughts about this question:" in msg['content'] and len(conversations[question_text]) == 1):
                                ai_messages.append(f"Interviewer: {msg['content']}")
                    
                    if user_answers:
                        q_block += "\n".join(user_answers) + "\n"
                    if ai_messages:
                        q_block += "\n".join(ai_messages) + "\n"
                
                elif has_saved_answer:
                    q_block += f"A: {chapter_data['questions'][question_text].get('answer', '')}\n"
                
                chapter_content.append(q_block)
        
        # Always include the chapter
        text += f"\n{'=' * 60}\n"
        text += f"CHAPTER {chapter_id}: {chapter['title']}\n"
        text += f"{'=' * 60}\n\n"
        
        # Add word count info
        word_count = calculate_chapter_word_count(chapter_id)
        word_target = chapter_data.get("word_target", 500)
        progress = (word_count / word_target * 100) if word_target > 0 else 100
        
        text += f"Word Count: {word_count} / {word_target} ({progress:.1f}%)\n"
        if progress >= 100:
            text += "Status: 🟢 Target Achieved\n\n"
        elif progress >= 70:
            text += "Status: 🟡 Close to Target\n\n"
        else:
            text += "Status: 🔴 Needs More Content\n\n"
        
        # Add chapter guidance
        text += f"Chapter Introduction:\n{chapter.get('guidance', '')}\n\n"
        
        if chapter_has_content:
            has_content = True
            text += f"{'-' * 50}\n\n"
            
            for i, q_block in enumerate(chapter_content):
                text += q_block
                if i < len(chapter_content) - 1:
                    text += "\n" + "-" * 40 + "\n\n"
            
            # Add summary if available
            summary = chapter_data.get("summary")
            if summary and summary != "No responses yet for this chapter.":
                text += "\n" + "=" * 50 + "\n"
                text += "CHAPTER SUMMARY:\n"
                text += "=" * 50 + "\n\n"
                text += f"{summary}\n\n"
        else:
            text += "\n[No responses recorded for this chapter yet]\n\n"
        
        text += f"Chapter Status: {'COMPLETED' if chapter_data.get('completed', False) else 'IN PROGRESS'}\n"
        answered_count = len([q for q in chapter['questions'] if q in chapter_data.get('questions', {}) or (q in conversations and any(msg['role'] == 'user' for msg in conversations[q]))])
        text += f"Questions answered: {answered_count}/{len(chapter['questions'])}\n"
        text += "\n" + "=" * 60 + "\n"
    
    if not has_content:
        text += "\nNo responses have been recorded yet in any chapter.\n"
        text += "=" * 60 + "\n"
    
    return text

# ────────────────────────────────────────────────
# STREAMLIT UI - UPDATED WITH NEW FEATURES
# ────────────────────────────────────────────────
st.set_page_config(page_title="LifeStory AI", page_icon="📖", layout="wide")

# Clean header with logo
st.markdown(f"""
<div class="main-header">
    <img src="{LOGO_URL}" class="logo-img" alt="LifeStory AI Logo">
    <h2 style="margin: 0; line-height: 1.2;">LifeStory AI</h2>
    <p style="font-size: 0.9rem; color: #666; margin: 0; line-height: 1.2;">Preserve Your Legacy • Share Your Story</p>
</div>
""", unsafe_allow_html=True)

st.caption("A professional guided journey through your life story")

# Load user data on startup
if st.session_state.user_id != "Guest":
    load_user_data()

# Sidebar for navigation and controls
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
        
        # Reinitialize for new user
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
    
    # Professional Ghostwriter Mode Toggle
    st.divider()
    st.header("✍️ Interview Style")
    
    ghostwriter_mode = st.toggle(
        "Professional Ghostwriter Mode", 
        value=st.session_state.ghostwriter_mode,
        help="When enabled, the AI acts as a professional biographer using advanced interviewing techniques to draw out richer, more detailed responses."
    )
    
    if ghostwriter_mode != st.session_state.ghostwriter_mode:
        st.session_state.ghostwriter_mode = ghostwriter_mode
        st.rerun()
    
    # Speech Input Toggle
    show_speech = st.toggle(
        "Show Speech Input",
        value=st.session_state.show_speech,
        help="Show voice recording interface"
    )
    
    if show_speech != st.session_state.show_speech:
        st.session_state.show_speech = show_speech
        st.rerun()
    
    if st.session_state.ghostwriter_mode:
        st.success("✓ Professional mode active")
        st.caption("AI will use advanced interviewing techniques")
    else:
        st.info("Standard mode active")
        st.caption("AI will use simpler conversation style")
    
    st.divider()
    
    st.header("📖 Chapter Progress")
    
    # Chapter progress tracker with word counts
    for i, chapter in enumerate(CHAPTERS):
        chapter_id = chapter["id"]
        chapter_data = st.session_state.responses.get(chapter_id, {})
        
        # Calculate word count and traffic light
        word_count = calculate_chapter_word_count(chapter_id)
        target_words = chapter_data.get("word_target", 500)
        color, emoji, progress = get_traffic_light(chapter_id)
        
        # Determine status
        if chapter_data.get("completed", False):
            status = "✅"
        elif i == st.session_state.current_chapter:
            status = "▶️"
        else:
            status = "●"
        
        # Chapter button with traffic light
        button_text = f"{emoji} {status} Chapter {chapter['id']}: {chapter['title']}"
        
        if st.button(button_text, 
                    key=f"select_{i}",
                    use_container_width=True,
                    help=f"{word_count}/{target_words} words ({progress:.0f}%)"):
            st.session_state.current_chapter = i
            st.session_state.current_question = 0
            st.session_state.editing = None
            st.rerun()
        
        # Progress bar with word count
        if target_words > 0:
            progress_bar = min(word_count / target_words, 1.0)
            st.progress(progress_bar)
            
            # Word count display
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption(f"📝 {word_count}/{target_words} words")
            with col2:
                if st.button("✏️", key=f"edit_target_{chapter_id}", help="Edit word target"):
                    st.session_state[f"editing_target_{chapter_id}"] = True
        
        # Edit target input
        if st.session_state.get(f"editing_target_{chapter_id}"):
            new_target = st.number_input(
                f"Target for Chapter {chapter_id}:",
                min_value=100,
                max_value=5000,
                value=target_words,
                key=f"target_input_{chapter_id}",
                label_visibility="collapsed"
            )
            
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("💾 Save", key=f"save_target_{chapter_id}"):
                    st.session_state.responses[chapter_id]["word_target"] = new_target
                    save_word_target(chapter_id, new_target)
                    st.session_state[f"editing_target_{chapter_id}"] = False
                    st.rerun()
            with col_cancel:
                if st.button("❌ Cancel", key=f"cancel_target_{chapter_id}"):
                    st.session_state[f"editing_target_{chapter_id}"] = False
                    st.rerun()
    
    st.divider()
    
    # Navigation controls for moving between questions
    st.subheader("Question Navigation")
    
    # Show current question number
    current_chapter = CHAPTERS[st.session_state.current_chapter]
    st.markdown(f'<div class="question-counter">Question {st.session_state.current_question + 1} of {len(current_chapter["questions"])}</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        # Previous question button
        if st.button("← Previous", disabled=st.session_state.current_question == 0, key="prev_q_sidebar"):
            st.session_state.current_question = max(0, st.session_state.current_question - 1)
            st.session_state.editing = None
            st.rerun()
    
    with col2:
        # Next question button
        if st.button("Next →", disabled=st.session_state.current_question >= len(current_chapter["questions"]) - 1, key="next_q_sidebar"):
            st.session_state.current_question = min(len(current_chapter["questions"]) - 1, st.session_state.current_question + 1)
            st.session_state.editing = None
            st.rerun()
    
    # Chapter navigation
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
    
    # Jump to specific chapter
    chapter_options = [f"Chapter {c['id']}: {c['title']}" for c in CHAPTERS]
    selected_chapter = st.selectbox("Jump to chapter:", chapter_options, index=st.session_state.current_chapter)
    if chapter_options.index(selected_chapter) != st.session_state.current_chapter:
        st.session_state.current_chapter = chapter_options.index(selected_chapter)
        st.session_state.current_question = 0
        st.session_state.editing = None
        st.rerun()
    
    st.divider()
    
    # Export section
    st.subheader("📤 Export Options")
    
    # Show what will be exported
    total_answers = sum(len(ch.get("questions", {})) for ch in st.session_state.responses.values())
    total_conversations = sum(len([q for q, conv in convs.items() if any(msg['role'] == 'user' for msg in conv)]) for convs in st.session_state.chapter_conversations.values())
    total_to_export = max(total_answers, total_conversations)
    st.caption(f"Total answers to export: {total_to_export}")
    
    if st.button("📥 Export Current Progress", type="primary"):
        if total_to_export > 0:
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="Download as JSON",
                    data=export_json(),
                    file_name=f"LifeStory_{st.session_state.user_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json"
                )
            with col2:
                st.download_button(
                    label="Download as Text",
                    data=export_text(),
                    file_name=f"LifeStory_{st.session_state.user_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain"
                )
        else:
            st.warning("No responses to export yet. Start answering questions first!")
    
    st.divider()
    
    # Management Section
    st.subheader("⚙️ Management")
    
    # Clear buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear Current Chapter", type="secondary", key="clear_chap_bottom"):
            current_chapter_id = CHAPTERS[st.session_state.current_chapter]["id"]
            clear_chapter(current_chapter_id)
            st.session_state.current_question = 0
            st.session_state.editing = None
            st.rerun()
    
    with col2:
        if st.button("Clear All", type="secondary", key="clear_all_bottom"):
            clear_all()
            st.rerun()
    
    # Complete chapter button in sidebar
    if st.button("✅ Complete Chapter", type="primary", use_container_width=True, key="complete_chap_bottom"):
        current_chapter_id = CHAPTERS[st.session_state.current_chapter]["id"]
        chapter_data = st.session_state.responses.get(current_chapter_id, {})
        questions_answered = len(chapter_data.get("questions", {}))
        
        if questions_answered > 0:
            summary = generate_chapter_summary(current_chapter_id)
            st.session_state.responses[current_chapter_id]["summary"] = summary
            st.session_state.responses[current_chapter_id]["completed"] = True
            st.success(f"Chapter {current_chapter_id} completed!")
            st.rerun()
        else:
            st.warning("Answer at least one question before completing the chapter.")
    
    st.divider()
    st.caption("Built with DeepSeek AI • Your data is saved locally")
    st.caption(f"Audio recording uses Streamlit {st.__version__}")

# Main content area - FULL WIDTH
# Get current chapter
current_chapter = CHAPTERS[st.session_state.current_chapter]
current_chapter_id = current_chapter["id"]
current_question_text = current_chapter["questions"][st.session_state.current_question]

# Show chapter header with word count
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.subheader(f"Chapter {current_chapter['id']}: {current_chapter['title']}")
    
    # Show interview style indicator
    if st.session_state.ghostwriter_mode:
        st.markdown('<p class="ghostwriter-tag">Professional Ghostwriter Mode • Advanced Interviewing</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="ghostwriter-tag">Standard Interview Mode</p>', unsafe_allow_html=True)
        
with col2:
    # Larger question counter
    st.markdown(f'<div class="question-counter" style="margin-top: 1rem;">Question {st.session_state.current_question + 1} of {len(current_chapter["questions"])}</div>', unsafe_allow_html=True)
with col3:
    # Quick navigation buttons
    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        if st.button("← Prev", disabled=st.session_state.current_question == 0, key="prev_q_quick", use_container_width=True):
            st.session_state.current_question = max(0, st.session_state.current_question - 1)
            st.session_state.editing = None
            st.rerun()
    with nav_col2:
        if st.button("Next →", disabled=st.session_state.current_question >= len(current_chapter["questions"]) - 1, key="next_q_quick", use_container_width=True):
            st.session_state.current_question = min(len(current_chapter["questions"]) - 1, st.session_state.current_question + 1)
            st.session_state.editing = None
            st.rerun()

# WORD COUNT DISPLAY WITH TRAFFIC LIGHT SYSTEM
current_word_count = calculate_chapter_word_count(current_chapter_id)
target_words = st.session_state.responses[current_chapter_id].get("word_target", 500)
color, emoji, progress_percent = get_traffic_light(current_chapter_id)

# Display word count box
st.markdown(f"""
<div class="word-count-box">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h4 style="margin: 0; display: flex; align-items: center;">
                <span class="traffic-light" style="background-color: {color};"></span>
                Word Count: {current_word_count} / {target_words}
            </h4>
            <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem; color: #666;">
                {emoji} {progress_percent:.0f}% of target • {target_words - current_word_count} words remaining
            </p>
        </div>
        <div>
            <span style="font-size: 1.2rem; font-weight: bold;">{emoji}</span>
        </div>
    </div>
    <div style="margin-top: 1rem;">
        <div style="height: 10px; background-color: #e0e0e0; border-radius: 5px; overflow: hidden;">
            <div style="height: 100%; width: {min(progress_percent, 100)}%; background-color: {color}; border-radius: 5px;"></div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Show progress bar for questions
chapter_data = st.session_state.responses.get(current_chapter_id, {})
questions_answered = len(chapter_data.get("questions", {}))
total_questions = len(current_chapter["questions"])

if total_questions > 0:
    question_progress = questions_answered / total_questions
    st.progress(min(question_progress, 1.0))
    st.caption(f"Questions answered: {questions_answered}/{total_questions}")

# Show chapter guidance
st.markdown(f"""
<div class="chapter-guidance">
    {current_chapter.get('guidance', '')}
</div>
""", unsafe_allow_html=True)

# Show current question
st.markdown(f"""
<div class="question-box">
    {current_question_text}
</div>
""", unsafe_allow_html=True)

# UPDATED SPEECH INTERFACE USING STREAMLIT'S BUILT-IN AUDIO INPUT
if st.session_state.show_speech:
    st.markdown("### 🎤 Speak Your Answer")
    st.markdown("""
    <div class="audio-recording">
        <strong>Voice Recording Instructions:</strong>
        <ul style="margin: 0.5rem 0 0 1rem; padding-left: 1rem;">
            <li>Click the microphone icon below to start recording</li>
            <li>Speak clearly - your browser will record the audio</li>
            <li>When finished, click the microphone again to stop</li>
            <li>Your audio will be saved for transcription</li>
            <li>Works in all modern browsers that support microphone access</li>
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
        
        # Store audio bytes in session state for later use
        st.session_state.audio_bytes = audio_bytes
        
        # Note about transcription
        st.info("""
        **Note:** You've recorded audio successfully! 
        
        To transcribe this audio to text, you would use OpenAI's Whisper API:
        
        ```python
        # Example for transcribing the audio
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            with open(tmp.name, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
        ```
        
        For now, please type or paste your answer in the text area below.
        """)
    
    # Manual text input for speech
    speech_text = st.text_area(
        "Type or paste your spoken answer here:",
        value=st.session_state.speech_text,
        height=150,
        key="speech_text_area",
        placeholder="Type your answer here, or paste transcribed text..."
    )
    
    if speech_text != st.session_state.speech_text:
        st.session_state.speech_text = speech_text
    
    if st.session_state.speech_text:
        # Show word count for the speech text
        speech_word_count = len(re.findall(r'\w+', st.session_state.speech_text))
        st.caption(f"📝 Speech text word count: {speech_word_count} words")
        
        # Use speech text button
        if st.button("✅ Use This Text for Answer", type="primary", use_container_width=True):
            # Clean and use the speech text
            cleaned_text = clean_speech_text(st.session_state.speech_text)
            st.session_state.speech_preview = f"Ready to use: {cleaned_text[:100]}..."
            st.session_state.speech_text = cleaned_text
            # This will be picked up by the chat input below
    
    st.markdown("---")
    st.markdown("### ✏️ Or Continue with Chat Below")

# Get conversation for current question
current_chapter_id = current_chapter["id"]
current_question_text = current_chapter["questions"][st.session_state.current_question]

# Handle backward compatibility
if current_chapter_id in st.session_state.chapter_conversations:
    if isinstance(st.session_state.chapter_conversations[current_chapter_id], list):
        old_conversation = st.session_state.chapter_conversations[current_chapter_id]
        st.session_state.chapter_conversations[current_chapter_id] = {}
        for msg in old_conversation:
            if "Let's start with:" in msg.get("content", ""):
                question_match = msg["content"].split("Let's start with:")[-1].strip().strip('**')
                if question_match:
                    st.session_state.chapter_conversations[current_chapter_id][question_match] = old_conversation
                    break
        if not st.session_state.chapter_conversations[current_chapter_id]:
            st.session_state.chapter_conversations[current_chapter_id][current_question_text] = old_conversation

# Ensure chapter_conversations[chapter_id] exists and is a dict
if current_chapter_id not in st.session_state.chapter_conversations:
    st.session_state.chapter_conversations[current_chapter_id] = {}

# Get conversation for this specific question
conversation = st.session_state.chapter_conversations[current_chapter_id].get(current_question_text, [])

# Display conversation - ALWAYS show at least an AI welcome message if empty
if not conversation:
    # Show appropriate welcome message based on mode
    with st.chat_message("assistant"):
        if st.session_state.ghostwriter_mode:
            # Professional ghostwriter welcome
            welcome_msg = f"""Let's explore this question properly: **{current_question_text}**

Take your time with this—good biographies are built from thoughtful reflection rather than quick answers.

*Current chapter word count: {current_word_count}/{target_words} words*"""
        else:
            # Standard welcome
            welcome_msg = f"I'd love to hear your thoughts about this question: **{current_question_text}**"
        
        st.markdown(welcome_msg)
        # Add to conversation so it shows in history
        conversation.append({"role": "assistant", "content": welcome_msg})
        st.session_state.chapter_conversations[current_chapter_id][current_question_text] = conversation
else:
    # Display existing conversation
    for i, message in enumerate(conversation):
        if message["role"] == "assistant":
            with st.chat_message("assistant"):
                st.markdown(message["content"])
        
        elif message["role"] == "user":
            # Check if this message is being edited
            is_editing = (st.session_state.editing == (current_chapter_id, current_question_text, i))
            
            with st.chat_message("user"):
                if is_editing:
                    # Edit mode: show text input and buttons
                    new_text = st.text_area(
                        "Edit your answer:",
                        value=st.session_state.edit_text,
                        key=f"edit_area_{current_chapter_id}_{hash(current_question_text)}_{i}",
                        label_visibility="collapsed"
                    )
                    
                    # Show word count while editing
                    if new_text:
                        edit_word_count = len(re.findall(r'\w+', new_text))
                        st.caption(f"📝 Editing: {edit_word_count} words")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✓ Save", key=f"save_{current_chapter_id}_{hash(current_question_text)}_{i}", type="primary"):
                            # Save the edited answer
                            conversation[i]["content"] = new_text
                            st.session_state.chapter_conversations[current_chapter_id][current_question_text] = conversation
                            
                            # Save to database
                            save_response(current_chapter_id, current_question_text, new_text)
                            
                            st.session_state.editing = None
                            st.rerun()
                    with col2:
                        if st.button("✕ Cancel", key=f"cancel_{current_chapter_id}_{hash(current_question_text)}_{i}"):
                            st.session_state.editing = None
                            st.rerun()
                else:
                    # Normal mode: show answer with edit button
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.markdown(message["content"])
                        # Show word count for this answer
                        word_count = len(re.findall(r'\w+', message["content"]))
                        st.caption(f"📝 {word_count} words")
                    with col2:
                        if st.button("✏️", key=f"edit_{current_chapter_id}_{hash(current_question_text)}_{i}"):
                            st.session_state.editing = (current_chapter_id, current_question_text, i)
                            st.session_state.edit_text = message["content"]
                            st.rerun()

# Chat input - ALWAYS SHOW when not editing
if st.session_state.editing is None:
    # Check if we have speech text to use
    if st.session_state.speech_text:
        # Show the speech text with option to use it
        speech_word_count = len(re.findall(r'\w+', st.session_state.speech_text))
        st.info(f"**Speech text ready ({speech_word_count} words):** {st.session_state.speech_text[:200]}...")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Use Speech Text", type="primary", key="use_speech_text"):
                user_input = clean_speech_text(st.session_state.speech_text)
                # Store for chat input
                st.session_state.pending_input = user_input
                # Clear speech text after use
                st.session_state.speech_text = ""
                st.session_state.speech_preview = ""
                st.rerun()
        with col2:
            if st.button("❌ Clear Speech Text", key="clear_speech_text"):
                st.session_state.speech_text = ""
                st.session_state.speech_preview = ""
                st.rerun()
    
    # Regular chat input - check for pending input from speech
    user_input = None
    if "pending_input" in st.session_state and st.session_state.pending_input:
        user_input = st.session_state.pending_input
        del st.session_state.pending_input
    else:
        user_input = st.chat_input("Type your answer here...")
    
    if user_input:
        current_chapter_id = current_chapter["id"]
        current_question_text = current_chapter["questions"][st.session_state.current_question]
        
        # Get conversation for this question
        if current_chapter_id not in st.session_state.chapter_conversations:
            st.session_state.chapter_conversations[current_chapter_id] = {}
        
        if current_question_text not in st.session_state.chapter_conversations[current_chapter_id]:
            st.session_state.chapter_conversations[current_chapter_id][current_question_text] = []
        
        conversation = st.session_state.chapter_conversations[current_chapter_id][current_question_text]
        
        # Add user message
        conversation.append({"role": "user", "content": user_input})
        
        # Show updated word count after adding response
        updated_word_count = calculate_chapter_word_count(current_chapter_id)
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    messages_for_api = [
                        {"role": "system", "content": get_system_prompt()},
                        *conversation[-5:]  # Last 5 messages for context
                    ]
                    
                    # Adjust parameters based on mode
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
                    
                    # Add word count info to response in professional mode
                    if st.session_state.ghostwriter_mode and updated_word_count > 0:
                        target_words = st.session_state.responses[current_chapter_id].get("word_target", 500)
                        progress = (updated_word_count / target_words * 100) if target_words > 0 else 100
                        
                        # Add subtle word count encouragement
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
                    if st.session_state.ghostwriter_mode:
                        error_msg = "Thank you for that. Your response gives us good material to work with."
                    else:
                        error_msg = "Thank you for sharing that. Your response has been saved."
                    
                    st.markdown(error_msg)
                    conversation.append({"role": "assistant", "content": error_msg})
        
        # Save to database
        save_response(current_chapter_id, current_question_text, user_input)
        
        # Update conversation
        st.session_state.chapter_conversations[current_chapter_id][current_question_text] = conversation
        
        # Clear speech text if it was used
        if user_input == st.session_state.get("speech_text", ""):
            st.session_state.speech_text = ""
            st.session_state.speech_preview = ""
        
        st.rerun()

# Footer with current stats
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

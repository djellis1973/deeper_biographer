import streamlit as st
import json
from datetime import datetime
from openai import OpenAI
import os
import sqlite3

# ────────────────────────────────────────────────
# CLEAN BRANDING WITH LOGO
# ────────────────────────────────────────────────
LOGO_URL = "https://menuhunterai.com/wp-content/uploads/2026/01/logo.png"

# Clean CSS
st.markdown(f"""
<style>
    .main-header {{
        text-align: center;
        padding: 2rem 0;
        margin-bottom: 2rem;
    }}
    
    .logo-img {{
        width: 100px;
        height: 100px;
        border-radius: 50%;
        object-fit: cover;
        margin-bottom: 1rem;
    }}
    
    .question-box {{
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #4a5568;
        margin-bottom: 1rem;
    }}
</style>
""", unsafe_allow_html=True)

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY")))

# Define the chapter structure from your PDF (first 3 chapters)
CHAPTERS = [
    {
        "id": 1,
        "title": "Childhood",
        "questions": [
            "What is your earliest memory?",
            "Can you describe your family home growing up?",
            "Who were the most influential people in your early years?",
            "What was school like for you?",
            "Were there any favourite games or hobbies?",
            "Is there a moment from childhood that shaped who you are?",
            "If you could give your younger self some advice, what would it be?"
        ],
        "completed": False
    },
    {
        "id": 2,
        "title": "Family & Relationships",
        "questions": [
            "How would you describe your relationship with your parents?",
            "Are there any family traditions you remember fondly?",
            "What was your relationship like with siblings or close relatives?",
            "Can you share a story about a family celebration or challenge?",
            "How did your family shape your values?"
        ],
        "completed": False
    },
    {
        "id": 3,
        "title": "Education & Growing Up",
        "questions": [
            "What were your favourite subjects at school?",
            "Did you have any memorable teachers or mentors?",
            "How did you feel about exams and studying?",
            "Were there any big turning points in your education?",
            "Did you pursue further education or training?",
            "What advice would you give about learning?"
        ],
        "completed": False
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
    conn.commit()
    conn.close()

init_db()

# Initialize session state - WITH SEPARATE CONVERSATIONS
if "responses" not in st.session_state:
    st.session_state.current_chapter = 0
    st.session_state.current_question = 0
    st.session_state.responses = {}
    st.session_state.user_id = "Guest"
    st.session_state.chapter_conversations = {}  # Separate conversations per chapter
    
    # Initialize for each chapter
    for chapter in CHAPTERS:
        chapter_id = chapter["id"]
        st.session_state.responses[chapter_id] = {
            "title": chapter["title"],
            "questions": {},
            "summary": "",
            "completed": False
        }
        st.session_state.chapter_conversations[chapter_id] = []  # Empty conversation for each chapter

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
            "completed": False
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

# Delete a specific response
def delete_response(chapter_id, question):
    user_id = st.session_state.user_id
    
    # Delete from session state
    if chapter_id in st.session_state.responses:
        if question in st.session_state.responses[chapter_id]["questions"]:
            del st.session_state.responses[chapter_id]["questions"][question]
    
    # Delete from database
    try:
        conn = sqlite3.connect('life_story.db')
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM responses 
            WHERE user_id = ? AND chapter_id = ? AND question = ?
        """, (user_id, chapter_id, question))
        conn.commit()
        conn.close()
    except:
        pass

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
        st.session_state.chapter_conversations[chapter_id] = []
    
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
            "completed": False
        }
        st.session_state.chapter_conversations[chapter_id] = []
    
    st.session_state.current_chapter = 0
    st.session_state.current_question = 0
    
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

# Dynamic system prompt based on current chapter
def get_system_prompt():
    current_chapter = CHAPTERS[st.session_state.current_chapter]
    current_question = current_chapter["questions"][st.session_state.current_question]
    
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
        questions_answers.append(f"Q: {q}\nA: {data.get('answer', 'No answer')[:200]}")
    
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

# Export functions
def export_json():
    """Export all responses as JSON"""
    export_data = {
        "metadata": {
            "project": "LifeStory AI",
            "user_id": st.session_state.user_id,
            "export_date": datetime.now().isoformat(),
            "export_format": "JSON"
        },
        "chapters": {}
    }
    
    # Only include chapters that have responses
    for chapter_id, chapter_data in st.session_state.responses.items():
        if chapter_data.get("questions"):
            export_data["chapters"][str(chapter_id)] = {
                "title": chapter_data.get("title", f"Chapter {chapter_id}"),
                "questions": chapter_data.get("questions", {}),
                "summary": chapter_data.get("summary", ""),
                "completed": chapter_data.get("completed", False)
            }
    
    return json.dumps(export_data, indent=2)

def export_text():
    """Export all responses as formatted text"""
    text = "=" * 60 + "\n"
    text += "MY LIFE STORY\n"
    text += "=" * 60 + "\n\n"
    text += f"Author: {st.session_state.user_id}\n"
    text += f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n"
    
    # Track if we have any content
    has_content = False
    
    for chapter_id in sorted(st.session_state.responses.keys()):
        chapter = st.session_state.responses[chapter_id]
        
        # Only include chapters with questions
        if chapter.get("questions"):
            has_content = True
            text += f"\nCHAPTER {chapter_id}: {chapter.get('title', 'Untitled')}\n"
            text += "-" * 50 + "\n\n"
            
            for question, data in chapter.get("questions", {}).items():
                text += f"Q: {question}\n"
                text += f"A: {data.get('answer', '')}\n\n"
            
            summary = chapter.get("summary")
            if summary and summary != "No responses yet for this chapter.":
                text += "Summary:\n"
                text += f"{summary}\n\n"
            
            text += "=" * 60 + "\n"
    
    if not has_content:
        text += "\nNo responses have been recorded yet.\n"
        text += "=" * 60 + "\n"
    
    return text

# ────────────────────────────────────────────────
# STREAMLIT UI
# ────────────────────────────────────────────────
st.set_page_config(page_title="LifeStory AI", page_icon="📖", layout="wide")

# Clean header with logo
st.markdown(f"""
<div class="main-header">
    <img src="{LOGO_URL}" class="logo-img" alt="LifeStory AI Logo">
    <h1>LifeStory AI</h1>
    <p>Preserve Your Legacy • Share Your Story</p>
</div>
""", unsafe_allow_html=True)

st.caption("A guided journey through your life story")

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
        
        # Reinitialize for new user
        for chapter in CHAPTERS:
            chapter_id = chapter["id"]
            st.session_state.responses[chapter_id] = {
                "title": chapter["title"],
                "questions": {},
                "summary": "",
                "completed": False
            }
            st.session_state.chapter_conversations[chapter_id] = []
        
        load_user_data()
        st.rerun()
    
    st.divider()
    
    # Management Section
    st.header("⚙️ Management")
    
    # Clear buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear Current Chapter", type="secondary"):
            current_chapter_id = CHAPTERS[st.session_state.current_chapter]["id"]
            clear_chapter(current_chapter_id)
            st.session_state.current_question = 0
            st.rerun()
    
    with col2:
        if st.button("Clear All", type="secondary"):
            clear_all()
            st.rerun()
    
    st.divider()
    
    st.header("📖 Chapter Progress")
    
    # Chapter progress tracker
    for i, chapter in enumerate(CHAPTERS):
        chapter_id = chapter["id"]
        chapter_data = st.session_state.responses.get(chapter_id, {})
        
        # Determine status
        if chapter_data.get("completed", False):
            status = "✅"
        elif i == st.session_state.current_chapter:
            status = "▶️"
        else:
            status = "●"
        
        # Chapter button
        if st.button(f"{status} Chapter {chapter['id']}: {chapter['title']}", 
                    key=f"select_{i}",
                    use_container_width=True):
            st.session_state.current_chapter = i
            st.session_state.current_question = 0
            st.rerun()
        
        # Show progress within chapter
        questions_answered = len(chapter_data.get("questions", {}))
        total_questions = len(chapter["questions"])
        
        if total_questions > 0:
            progress = questions_answered / total_questions
            st.progress(min(progress, 1.0))
            st.caption(f"{questions_answered}/{total_questions} questions answered")
    
    st.divider()
    
    # Navigation controls
    st.subheader("Navigation")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Previous", disabled=st.session_state.current_chapter == 0):
            st.session_state.current_chapter = max(0, st.session_state.current_chapter - 1)
            st.session_state.current_question = 0
            st.rerun()
    with col2:
        if st.button("Next →", disabled=st.session_state.current_chapter >= len(CHAPTERS)-1):
            st.session_state.current_chapter = min(len(CHAPTERS)-1, st.session_state.current_chapter + 1)
            st.session_state.current_question = 0
            st.rerun()
    
    # Jump to specific chapter
    chapter_options = [f"Chapter {c['id']}: {c['title']}" for c in CHAPTERS]
    selected_chapter = st.selectbox("Jump to chapter:", chapter_options, index=st.session_state.current_chapter)
    if chapter_options.index(selected_chapter) != st.session_state.current_chapter:
        st.session_state.current_chapter = chapter_options.index(selected_chapter)
        st.session_state.current_question = 0
        st.rerun()
    
    st.divider()
    
    # Export section
    st.subheader("📤 Export Options")
    
    # Show what will be exported
    total_answers = sum(len(ch.get("questions", {})) for ch in st.session_state.responses.values())
    st.caption(f"Total answers to export: {total_answers}")
    
    if st.button("📥 Export Current Progress", type="primary"):
        if total_answers > 0:
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
    st.caption("Built with DeepSeek AI • Your data is saved locally")

# Main chat interface
col1, col2 = st.columns([3, 1])

with col1:
    # Get current chapter
    current_chapter = CHAPTERS[st.session_state.current_chapter]
    current_chapter_id = current_chapter["id"]
    current_question_text = current_chapter["questions"][st.session_state.current_question]
    
    # Show chapter header
    st.subheader(f"Chapter {current_chapter['id']}: {current_chapter['title']}")
    
    # Show progress
    chapter_data = st.session_state.responses.get(current_chapter_id, {})
    questions_answered = len(chapter_data.get("questions", {}))
    total_questions = len(current_chapter["questions"])
    
    if total_questions > 0:
        progress = questions_answered / total_questions
        st.progress(min(progress, 1.0))
        st.caption(f"Question {st.session_state.current_question + 1} of {total_questions}")
    
    # Show current question
    st.markdown(f"""
    <div class="question-box">
        <h4 style="margin: 0;">{current_question_text}</h4>
    </div>
    """, unsafe_allow_html=True)
    
    # Show existing answer if already answered
    existing_answer = chapter_data.get("questions", {}).get(current_question_text, {}).get("answer", "")
    if existing_answer:
        with st.expander("📝 Your previous answer:", expanded=False):
            st.markdown(existing_answer)
            
            if st.button("🗑️ Delete this answer", key=f"delete_current"):
                delete_response(current_chapter_id, current_question_text)
                st.rerun()
    
    # Show conversation for current chapter ONLY - THE WORKING FEATURE
    conversation = st.session_state.chapter_conversations.get(current_chapter_id, [])
    
    # Auto-start conversation if empty AND no existing answer
    if not conversation and not existing_answer:
        welcome_message = f"Hello **{st.session_state.user_id}**! I'm here to help you with your life story. Let's start with: **{current_question_text}**"
        st.session_state.chapter_conversations[current_chapter_id] = [{"role": "assistant", "content": welcome_message}]
        conversation = st.session_state.chapter_conversations[current_chapter_id]
        st.rerun()
    
    # Display conversation
    for message in conversation:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

with col2:
    # Current chapter overview
    st.subheader("Current Questions")
    for i, question in enumerate(current_chapter["questions"]):
        is_current = i == st.session_state.current_question
        is_answered = question in chapter_data.get("questions", {})
        
        if is_current:
            st.markdown(f"<span style='color:blue; font-weight:bold;'>▶️ {question[:50]}...</span>", unsafe_allow_html=True)
        elif is_answered:
            st.markdown(f"<span style='color:green;'>✅ {question[:50]}...</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color:gray;'>○ {question[:50]}...</span>", unsafe_allow_html=True)
    
    st.divider()
    
    # Review and manage
    with st.expander("📋 Review Answers"):
        if chapter_data.get("questions"):
            for question, data in chapter_data.get("questions", {}).items():
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.caption(f"Q: {question[:40]}...")
                with col_b:
                    if st.button("🗑️", key=f"delete_{hash(question)}"):
                        delete_response(current_chapter_id, question)
                        st.rerun()
        else:
            st.caption("No answers yet in this chapter")
    
    st.divider()
    
    # Complete chapter
    if st.button("✅ Complete Chapter", type="primary"):
        if questions_answered > 0:
            summary = generate_chapter_summary(current_chapter_id)
            st.session_state.responses[current_chapter_id]["summary"] = summary
            st.session_state.responses[current_chapter_id]["completed"] = True
            st.success(f"Chapter {current_chapter_id} completed!")
            st.rerun()
        else:
            st.warning("Answer at least one question before completing the chapter.")

# Chat input
user_input = st.chat_input("Type your answer here...")

if user_input:
    current_chapter_id = current_chapter["id"]
    
    # Save response
    save_response(current_chapter_id, current_question_text, user_input)
    
    # Add to conversation
    conversation = st.session_state.chapter_conversations.get(current_chapter_id, [])
    conversation.append({"role": "user", "content": user_input})
    
    # Generate AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                messages_for_api = [
                    {"role": "system", "content": get_system_prompt()},
                    *conversation[-3:]  # Last few messages for context
                ]
                
                response = client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=messages_for_api,
                    temperature=0.7,
                    max_tokens=300
                )
                
                ai_response = response.choices[0].message.content
                st.markdown(ai_response)
                conversation.append({"role": "assistant", "content": ai_response})
                
            except Exception as e:
                error_msg = "Thank you for sharing that. Your response has been saved."
                st.markdown(error_msg)
                conversation.append({"role": "assistant", "content": error_msg})
    
    # Update conversation in session state
    st.session_state.chapter_conversations[current_chapter_id] = conversation
    
    # DON'T auto-move to next question - let the user continue the conversation
    # The AI can ask follow-up questions and the conversation can continue
    
    # Only move to next question when user clicks a navigation button
    st.rerun()

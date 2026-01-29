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

# Clean CSS - just adds logo and subtle styling
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
    
    .delete-btn {{
        background-color: #ff4444 !important;
        color: white !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 0.25rem 0.5rem !important;
        font-size: 0.8rem !important;
        margin-left: 10px !important;
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

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.current_chapter = 0  # Index in CHAPTERS list
    st.session_state.current_question = 0  # Index in current chapter's questions
    st.session_state.responses = {}
    st.session_state.interview_started = False
    st.session_state.user_id = "Guest"  # Default user
    st.session_state.chapter_messages = {}  # Store messages per chapter
    st.session_state.showing_welcome = False  # Track if welcome is shown
    
    # Initialize response structure
    for chapter in CHAPTERS:
        st.session_state.responses[chapter["id"]] = {
            "title": chapter["title"],
            "questions": {},
            "summary": "",
            "completed": False
        }
        st.session_state.chapter_messages[chapter["id"]] = []

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
                "timestamp": datetime.now().isoformat(),
                "privacy_level": "Not set"
            }
        
        conn.close()
    except:
        pass

# Save response to database
def save_response(chapter_id, question, answer):
    user_id = st.session_state.user_id
    
    # Save to session state
    chapter_key = chapter_id
    if chapter_key not in st.session_state.responses:
        st.session_state.responses[chapter_key] = {
            "title": CHAPTERS[chapter_id-1]["title"],
            "questions": {},
            "summary": "",
            "completed": False
        }
    
    st.session_state.responses[chapter_key]["questions"][question] = {
        "answer": answer,
        "timestamp": datetime.now().isoformat(),
        "privacy_level": "Not set"
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
        st.session_state.responses[chapter["id"]] = {
            "title": chapter["title"],
            "questions": {},
            "summary": "",
            "completed": False
        }
        st.session_state.chapter_messages[chapter["id"]] = []
    
    st.session_state.messages = []
    st.session_state.current_chapter = 0
    st.session_state.current_question = 0
    st.session_state.interview_started = False
    st.session_state.showing_welcome = False
    
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
    
    return f"""You are a warm, professional biographer helping the user craft a compelling, honest autobiography. 

CURRENT CHAPTER: Chapter {current_chapter['id']}: {current_chapter['title']}

We are currently exploring: "{current_question}"

CONVERSATION RULES:
1. Ask this ONE main question at a time
2. After the user answers, provide a warm, empathetic reflection (1-2 sentences)
3. Optionally ask ONE natural follow-up question to draw out more detail
4. When the topic feels explored, gently transition to the next question
5. At the end of each chapter, provide a brief summary

CHAPTER PROGRESS (for your reference only):
- Chapter 1: Childhood (7 questions)
- Chapter 2: Family & Relationships (5 questions)
- Chapter 3: Education & Growing Up (6 questions)

SPECIAL FEATURES (mention occasionally):
- "You can mark any answer with a privacy level if you wish: Private, Family, or Public"
- "Feel free to add photos or voice notes to enrich this memory"
- "We can revisit or skip any question anytime"

Tone: Warm, empathetic, curious, slightly literary. Focus on drawing out vivid details and authentic emotions.
Always keep the user in control of the pace and direction."""

# Generate chapter summary
def generate_chapter_summary(chapter_id):
    chapter = st.session_state.responses[chapter_id]
    questions_answers = "\n".join([f"Q: {q}\nA: {chapter['questions'][q]['answer'][:100]}..." for q in chapter['questions']])
    
    prompt = f"""Based on these interview responses for Chapter {chapter_id}: {chapter['title']}, create a concise 3-4 paragraph summary capturing the key themes and stories.

Responses:
{questions_answers}

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
    except:
        return "Summary pending completion of chapter."

# Export functions
def export_json():
    export_data = {
        "metadata": {
            "project": "DeeperVault Legacy Interview",
            "export_date": datetime.now().isoformat(),
            "chapters_completed": [c["id"] for c in CHAPTERS if st.session_state.responses[c["id"]]["completed"]],
            "total_questions_answered": sum(len(st.session_state.responses[c["id"]]["questions"]) for c in CHAPTERS)
        },
        "chapters": st.session_state.responses
    }
    return json.dumps(export_data, indent=2)

def export_text():
    text = "MY LIFE STORY\n"
    text += "=" * 50 + "\n\n"
    
    for chapter_id in sorted(st.session_state.responses.keys()):
        chapter = st.session_state.responses[chapter_id]
        if not chapter["questions"]:
            continue
            
        text += f"CHAPTER {chapter_id}: {chapter['title']}\n"
        text += "-" * 40 + "\n\n"
        
        for question, data in chapter["questions"].items():
            text += f"Q: {question}\n"
            text += f"A: {data['answer']}\n\n"
        
        if chapter.get("summary"):
            text += f"SUMMARY:\n{chapter['summary']}\n\n"
        
        text += "\n" + "=" * 50 + "\n\n"
    
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

# Sidebar for navigation and controls
with st.sidebar:
    st.header("👤 Your Profile")
    
    new_user_id = st.text_input("Your Name:", value=st.session_state.user_id)
    
    if new_user_id != st.session_state.user_id:
        st.session_state.user_id = new_user_id
        st.session_state.messages = []
        st.session_state.interview_started = False
        st.session_state.showing_welcome = False
        load_user_data()
        st.rerun()
    
    st.divider()
    
    # Management Section
    st.header("⚙️ Management")
    
    # Clear buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear Current Chapter", type="secondary"):
            clear_chapter(CHAPTERS[st.session_state.current_chapter]["id"])
            st.session_state.current_question = 0
            st.session_state.showing_welcome = False
            st.rerun()
    
    with col2:
        if st.button("Clear All", type="secondary"):
            clear_all()
            st.rerun()
    
    st.divider()
    
    st.header("📖 Chapter Progress")
    
    # Chapter progress tracker with management
    for i, chapter in enumerate(CHAPTERS):
        status = "✅" if st.session_state.responses[chapter["id"]]["completed"] else "🔄" if i == st.session_state.current_chapter else "⏳"
        
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(f"{status} Chapter {chapter['id']}: {chapter['title']}", 
                        key=f"select_{i}",
                        use_container_width=True):
                st.session_state.current_chapter = i
                st.session_state.current_question = 0
                st.session_state.showing_welcome = False
                st.rerun()
        
        with col2:
            # Review button
            if st.session_state.responses[chapter["id"]]["questions"]:
                if st.button("📝", key=f"review_{i}"):
                    st.session_state[f"show_review_{i}"] = True
        
        # Show progress within chapter
        if st.session_state.responses[chapter["id"]]["questions"]:
            progress = len(st.session_state.responses[chapter["id"]]["questions"]) / len(chapter["questions"])
            st.progress(progress)
            st.caption(f"{len(st.session_state.responses[chapter['id']]['questions'])}/{len(chapter['questions'])} questions answered")
        
        # Show review section if clicked
        if st.session_state.get(f"show_review_{i}", False):
            with st.expander(f"Review Chapter {chapter['id']} Responses", expanded=True):
                for question, data in st.session_state.responses[chapter["id"]]["questions"].items():
                    col_a, col_b = st.columns([4, 1])
                    with col_a:
                        st.text_area(f"Q: {question}", 
                                   value=data['answer'],
                                   height=100,
                                   key=f"review_{chapter['id']}_{question}",
                                   disabled=True)
                    with col_b:
                        if st.button("🗑️", 
                                   key=f"delete_{chapter['id']}_{question}",
                                   help="Delete this response"):
                            delete_response(chapter['id'], question)
                            st.rerun()
                if st.button("Close Review", key=f"close_review_{i}"):
                    st.session_state[f"show_review_{i}"] = False
                    st.rerun()
    
    st.divider()
    
    # Navigation controls
    st.subheader("Navigation")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Previous Chapter", disabled=st.session_state.current_chapter == 0):
            st.session_state.current_chapter = max(0, st.session_state.current_chapter - 1)
            st.session_state.current_question = 0
            st.session_state.showing_welcome = False
            st.rerun()
    with col2:
        if st.button("Next Chapter →", disabled=st.session_state.current_chapter >= len(CHAPTERS)-1):
            st.session_state.current_chapter = min(len(CHAPTERS)-1, st.session_state.current_chapter + 1)
            st.session_state.current_question = 0
            st.session_state.showing_welcome = False
            st.rerun()
    
    # Jump to specific chapter
    chapter_options = [f"Chapter {c['id']}: {c['title']}" for c in CHAPTERS]
    selected_chapter = st.selectbox("Jump to chapter:", chapter_options, index=st.session_state.current_chapter)
    if chapter_options.index(selected_chapter) != st.session_state.current_chapter:
        st.session_state.current_chapter = chapter_options.index(selected_chapter)
        st.session_state.current_question = 0
        st.session_state.showing_welcome = False
        st.rerun()
    
    st.divider()
    
    # Export section
    st.subheader("Export Options")
    if st.button("📥 Export Current Progress"):
        if st.session_state.responses:
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="Download as JSON",
                    data=export_json(),
                    file_name=f"autobiography_{datetime.now().date()}.json",
                    mime="application/json"
                )
            with col2:
                st.download_button(
                    label="Download as Text",
                    data=export_text(),
                    file_name=f"manuscript_{datetime.now().date()}.txt",
                    mime="text/plain"
                )
        else:
            st.warning("No responses to export yet.")
    
    st.divider()
    st.caption("Built with DeepSeek AI • Based on DeeperVault UK Legacy Interview")

# Main chat interface
col1, col2 = st.columns([3, 1])

with col1:
    # Display current chapter info
    current_chapter = CHAPTERS[st.session_state.current_chapter]
    
    # Show current question prominently
    current_question = current_chapter["questions"][st.session_state.current_question]
    
    # Progress header
    st.subheader(f"Chapter {current_chapter['id']}: {current_chapter['title']}")
    
    # Show progress within current chapter
    answered = len(st.session_state.responses[current_chapter["id"]]["questions"])
    total = len(current_chapter["questions"])
    st.progress(answered / total if total > 0 else 0)
    st.caption(f"Question {st.session_state.current_question + 1} of {total}")
    
    # Display current question prominently
    st.markdown(f"### {current_question}")
    
    # Only show welcome message ONCE when starting a new chapter
    if not st.session_state.showing_welcome and not st.session_state.responses[current_chapter["id"]]["questions"]:
        welcome_message = f"""Hello **{st.session_state.user_id}**! I'm here to help you document your story.

Let's begin with **{current_question}**"""
        
        # Add to messages for this chapter
        st.session_state.chapter_messages[current_chapter["id"]].append({"role": "assistant", "content": welcome_message})
        st.session_state.showing_welcome = True
    
    # Display messages for current chapter
    for message in st.session_state.chapter_messages.get(current_chapter["id"], []):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Show existing answer if already answered this question
    if current_question in st.session_state.responses[current_chapter["id"]]["questions"]:
        existing_answer = st.session_state.responses[current_chapter["id"]]["questions"][current_question]["answer"]
        with st.expander("Your previous answer:", expanded=False):
            st.markdown(existing_answer)
            
            col_a, col_b = st.columns([3, 1])
            with col_b:
                if st.button("Delete this answer", type="secondary"):
                    delete_response(current_chapter["id"], current_question)
                    st.rerun()

with col2:
    # Current chapter overview
    st.subheader("Current Chapter Questions")
    for i, question in enumerate(current_chapter["questions"]):
        status = "✅" if question in st.session_state.responses[current_chapter["id"]]["questions"] else "●"
        color = "green" if question in st.session_state.responses[current_chapter["id"]]["questions"] else "gray"
        is_current = i == st.session_state.current_question
        
        if is_current:
            st.markdown(f"<span style='color:blue; font-weight:bold;'>▶️ {question[:60]}...</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color:{color}'>{status} {question[:60]}...</span>", unsafe_allow_html=True)
    
    st.divider()
    
    # Quick actions
    if st.button("Complete Current Chapter", type="primary"):
        # Generate summary
        summary = generate_chapter_summary(current_chapter["id"])
        st.session_state.responses[current_chapter["id"]]["summary"] = summary
        st.session_state.responses[current_chapter["id"]]["completed"] = True
        
        # Move to next chapter if available
        if st.session_state.current_chapter < len(CHAPTERS) - 1:
            st.session_state.current_chapter += 1
            st.session_state.current_question = 0
            st.session_state.showing_welcome = False
        
        st.success(f"Chapter {current_chapter['id']} completed! Summary generated.")
        st.rerun()

# Chat input
if prompt := st.chat_input("Type your answer here..."):
    # Add user message to chapter messages
    st.session_state.chapter_messages[current_chapter["id"]].append({"role": "user", "content": prompt})
    
    # Store the response
    save_response(current_chapter["id"], current_question, prompt)
    
    # Move to next question in current chapter
    if st.session_state.current_question < len(current_chapter["questions"]) - 1:
        st.session_state.current_question += 1
        st.session_state.showing_welcome = False
    else:
        # All questions in chapter answered
        st.session_state.responses[current_chapter["id"]]["completed"] = True
    
    # Generate AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Get next question for the prompt
                next_question = current_chapter["questions"][st.session_state.current_question]
                
                # Prepare conversation history for context
                messages_for_api = [
                    {"role": "system", "content": get_system_prompt()},
                    *st.session_state.chapter_messages[current_chapter["id"]][-2:]  # Last exchange
                ]
                
                response = client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=messages_for_api,
                    temperature=0.7,
                    max_tokens=500
                )
                
                ai_response = response.choices[0].message.content
                st.markdown(ai_response)
                st.session_state.chapter_messages[current_chapter["id"]].append({"role": "assistant", "content": ai_response})
                
            except Exception as e:
                st.error(f"Error generating response: {e}")
                # Fallback response
                fallback_response = f"""Thank you for sharing that. 

Now, I'd love to hear about: {next_question}"""
                
                st.markdown(fallback_response)
                st.session_state.chapter_messages[current_chapter["id"]].append({"role": "assistant", "content": fallback_response})
    
    st.rerun()

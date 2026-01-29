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
    
    .chat-history {{
        min-height: 400px;
        max-height: 600px;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        margin-bottom: 1rem;
        background-color: #fafafa;
    }}
    
    .ai-message {{
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 15px 15px 15px 0;
        margin-bottom: 1rem;
        max-width: 80%;
        margin-right: auto;
    }}
    
    .user-message {{
        background-color: #dcf8c6;
        padding: 1rem;
        border-radius: 15px 15px 0 15px;
        margin-bottom: 1rem;
        max-width: 80%;
        margin-left: auto;
        position: relative;
    }}
    
    .user-message-with-edit {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
    }}
    
    .message-content {{
        flex: 1;
    }}
    
    .edit-button {{
        margin-left: 10px;
        background: none;
        border: none;
        color: #666;
        cursor: pointer;
        font-size: 0.9rem;
    }}
    
    .edit-button:hover {{
        color: #333;
    }}
    
    .edit-container {{
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border: 1px solid #ffeaa7;
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
if "responses" not in st.session_state:
    st.session_state.current_chapter = 0
    st.session_state.current_question = 0
    st.session_state.responses = {}
    st.session_state.user_id = "Guest"
    st.session_state.chapter_conversations = {}
    st.session_state.editing = None  # (chapter_id, message_index)
    st.session_state.edit_text = ""
    
    # Initialize for each chapter
    for chapter in CHAPTERS:
        chapter_id = chapter["id"]
        st.session_state.responses[chapter_id] = {
            "title": chapter["title"],
            "questions": {},
            "summary": "",
            "completed": False
        }
        st.session_state.chapter_conversations[chapter_id] = []

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
    st.session_state.editing = None
    st.session_state.edit_text = ""
    
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

# Dynamic system prompt
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
    
    for chapter in CHAPTERS:
        chapter_id = chapter["id"]
        chapter_data = st.session_state.responses.get(chapter_id, {})
        
        # Get all questions and answers for this chapter
        chapter_qa = {}
        
        # From saved responses
        for q, data in chapter_data.get("questions", {}).items():
            chapter_qa[q] = data.get("answer", "")
        
        # Also check conversation for additional answers
        conversation = st.session_state.chapter_conversations.get(chapter_id, [])
        if conversation:
            # Extract the main question from welcome message
            for msg in conversation:
                if msg["role"] == "assistant" and "Let's start with:" in msg["content"]:
                    question_match = msg["content"].split("Let's start with:")[-1].strip().strip('**')
                    if question_match and question_match not in chapter_qa:
                        # Find the corresponding user answer
                        msg_index = conversation.index(msg)
                        if msg_index + 1 < len(conversation) and conversation[msg_index + 1]["role"] == "user":
                            chapter_qa[question_match] = conversation[msg_index + 1]["content"]
                    break
        
        # Only include chapters with answers
        if chapter_qa:
            export_data["chapters"][str(chapter_id)] = {
                "title": chapter["title"],
                "questions": chapter_qa,
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
    
    has_content = False
    
    for chapter in CHAPTERS:
        chapter_id = chapter["id"]
        chapter_data = st.session_state.responses.get(chapter_id, {})
        
        # Get all Q&A for this chapter
        chapter_qa = {}
        
        # From saved responses
        for q, data in chapter_data.get("questions", {}).items():
            chapter_qa[q] = data.get("answer", "")
        
        # Also check conversation
        conversation = st.session_state.chapter_conversations.get(chapter_id, [])
        if conversation:
            for msg in conversation:
                if msg["role"] == "assistant" and "Let's start with:" in msg["content"]:
                    question_match = msg["content"].split("Let's start with:")[-1].strip().strip('**')
                    if question_match and question_match not in chapter_qa:
                        msg_index = conversation.index(msg)
                        if msg_index + 1 < len(conversation) and conversation[msg_index + 1]["role"] == "user":
                            chapter_qa[question_match] = conversation[msg_index + 1]["content"]
                    break
        
        # Only include chapters with answers
        if chapter_qa:
            has_content = True
            text += f"\nCHAPTER {chapter_id}: {chapter['title']}\n"
            text += "-" * 50 + "\n\n"
            
            # Add questions in order
            for question in chapter["questions"]:
                if question in chapter_qa:
                    text += f"Q: {question}\n"
                    text += f"A: {chapter_qa[question]}\n\n"
            
            summary = chapter_data.get("summary")
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

# Create main layout
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
    
    # Get conversation
    conversation = st.session_state.chapter_conversations.get(current_chapter_id, [])
    
    # Auto-start conversation if empty
    if not conversation:
        welcome_message = f"Hello **{st.session_state.user_id}**! I'm here to help you with your life story. Let's start with: **{current_question_text}**"
        st.session_state.chapter_conversations[current_chapter_id] = [{"role": "assistant", "content": welcome_message}]
        conversation = st.session_state.chapter_conversations[current_chapter_id]
        st.rerun()
    
    # Display conversation history using custom HTML (not st.chat_message)
    st.markdown('<div class="chat-history">', unsafe_allow_html=True)
    
    for i, message in enumerate(conversation):
        if message["role"] == "assistant":
            st.markdown(f'<div class="ai-message">{message["content"]}</div>', unsafe_allow_html=True)
        
        elif message["role"] == "user":
            is_editing = (st.session_state.editing == (current_chapter_id, i))
            
            if is_editing:
                # Edit mode
                st.markdown('<div class="edit-container">', unsafe_allow_html=True)
                new_text = st.text_area(
                    "Edit your answer:",
                    value=st.session_state.edit_text,
                    key=f"edit_area_{current_chapter_id}_{i}",
                    label_visibility="collapsed"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✓ Save", key=f"save_{current_chapter_id}_{i}", type="primary"):
                        # Save the edited answer
                        conversation[i]["content"] = new_text
                        st.session_state.chapter_conversations[current_chapter_id] = conversation
                        
                        # Also save to database if this is the main question answer
                        if i == 1:  # First user answer (right after welcome)
                            save_response(current_chapter_id, current_question_text, new_text)
                        
                        st.session_state.editing = None
                        st.rerun()
                with col2:
                    if st.button("✕ Cancel", key=f"cancel_{current_chapter_id}_{i}"):
                        st.session_state.editing = None
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                # Normal display with edit button
                st.markdown(f'''
                <div class="user-message">
                    <div class="user-message-with-edit">
                        <div class="message-content">{message["content"]}</div>
                        <button class="edit-button" onclick="window.editMessage({current_chapter_id}, {i})">✏️</button>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close chat-history
    
    # JavaScript for edit button
    st.markdown(f"""
    <script>
    function editMessage(chapter_id, message_index) {{
        // This will trigger a Streamlit rerun with the editing state
        const data = {{
            chapter_id: chapter_id,
            message_index: message_index
        }};
        
        // Send data to Streamlit
        const input = parent.document.getElementById('edit_trigger');
        if (input) {{
            input.value = JSON.stringify(data);
            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
        }}
    }}
    
    // Create hidden input for JavaScript to communicate with Streamlit
    const input = document.createElement('input');
    input.id = 'edit_trigger';
    input.type = 'hidden';
    document.body.appendChild(input);
    </script>
    """, unsafe_allow_html=True)
    
    # Check if JavaScript triggered an edit
    edit_trigger = st.text_input("Edit trigger", key="edit_trigger", label_visibility="collapsed")
    if edit_trigger:
        try:
            data = json.loads(edit_trigger)
            chapter_id = data.get("chapter_id")
            message_index = data.get("message_index")
            
            if chapter_id == current_chapter_id:
                conversation = st.session_state.chapter_conversations.get(chapter_id, [])
                if 0 <= message_index < len(conversation) and conversation[message_index]["role"] == "user":
                    st.session_state.editing = (chapter_id, message_index)
                    st.session_state.edit_text = conversation[message_index]["content"]
                    st.rerun()
        except:
            pass
    
    # Chat input for new messages
    if st.session_state.editing is None:
        user_input = st.chat_input("Type your answer here...")
        
        if user_input:
            current_chapter_id = current_chapter["id"]
            
            # Add to conversation
            conversation = st.session_state.chapter_conversations.get(current_chapter_id, [])
            conversation.append({"role": "user", "content": user_input})
            
            # Generate AI response using st.chat_message for new messages only
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
            
            # Save the first answer to database
            if len(conversation) == 2:  # Welcome + first answer
                save_response(current_chapter_id, current_question_text, user_input)
            
            # Update conversation
            st.session_state.chapter_conversations[current_chapter_id] = conversation
            st.rerun()

with col2:
    # Right sidebar content
    st.subheader("Current Questions")
    
    for i, question in enumerate(current_chapter["questions"]):
        is_current = i == st.session_state.current_question
        
        # Check if answered
        is_answered = question in chapter_data.get("questions", {})
        
        if is_current:
            st.markdown(f"<div style='color:blue; font-weight:bold; margin: 5px 0;'>▶️ {question[:50]}...</div>", unsafe_allow_html=True)
        elif is_answered:
            st.markdown(f"<div style='color:green; margin: 5px 0;'>✅ {question[:50]}...</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='color:gray; margin: 5px 0;'>○ {question[:50]}...</div>", unsafe_allow_html=True)
    
    st.divider()
    
    # Complete chapter button
    if st.button("✅ Complete Chapter", type="primary", use_container_width=True):
        if questions_answered > 0:
            summary = generate_chapter_summary(current_chapter_id)
            st.session_state.responses[current_chapter_id]["summary"] = summary
            st.session_state.responses[current_chapter_id]["completed"] = True
            st.success(f"Chapter {current_chapter_id} completed!")
            st.rerun()
        else:
            st.warning("Answer at least one question before completing the chapter.")

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
            st.session_state.editing = None
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
            st.session_state.editing = None
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
            st.session_state.editing = None
            st.rerun()
    with col2:
        if st.button("Next →", disabled=st.session_state.current_chapter >= len(CHAPTERS)-1):
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

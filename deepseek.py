import streamlit as st
import json
from datetime import datetime
from openai import OpenAI
import os
import sqlite3

# ────────────────────────────────────────────────
# CLEAN BRANDING WITH LOGO - FIXED SPACING
# ────────────────────────────────────────────────
LOGO_URL = "https://menuhunterai.com/wp-content/uploads/2026/01/logo.png"

# Clean CSS with fixed logo spacing
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
</style>
""", unsafe_allow_html=True)

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY")))

# Define the chapter structure with guidance text
CHAPTERS = [
    {
        "id": 1,
        "title": "Childhood",
        "guidance": "Welcome to the Childhood chapter—this is where your story begins! Think back to your early years with an open heart. Share memories as vividly as you can: sights, sounds, feelings, smells, and little moments that still stay with you. There's no right or wrong way—honest reflections make the best stories. Take your time; it's okay if some memories are joyful, others bittersweet. This section helps readers see the roots of who you became.",
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
        "guidance": "Now let's turn to Family & Relationships—the people who shaped so much of your world. These questions invite you to reflect on connections, traditions, joys, and even challenges. Be as open as feels right; writing with kindness and honesty (from your own perspective) brings depth and authenticity to your story. Share what matters most to you.",
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
        "guidance": "Here in Education & Growing Up, we're exploring your learning journey—from school days to any further steps you took. Think about what excited you, what challenged you, and the people or moments that made a difference. This part often reveals turning points and how you grew into yourself. Reflect freely—learning isn't just about qualifications; it's about discovery and growth.",
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
    st.session_state.chapter_conversations = {}  # {chapter_id: {question_text: conversation}}
    st.session_state.editing = None  # (chapter_id, question_text, message_index)
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
        st.session_state.chapter_conversations[chapter_id] = {}  # Empty dict for questions

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
            "completed": False
        }
        st.session_state.chapter_conversations[chapter_id] = {}
    
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

# Export functions - FIXED to include ALL chapters and ALL conversation answers
def export_json():
    """Export all responses as JSON - includes ALL chapters and ALL conversation answers"""
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
        conversations = st.session_state.chapter_conversations.get(chapter_id, {})
        
        # Get ALL Q&A for this chapter - include both main answers and conversation answers
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
                
                # If we have user answers, use them (prefer conversation over saved answer)
                if user_answers:
                    # Join all user answers with newlines
                    chapter_qa[question_text] = "\n".join(user_answers)
                elif main_answer:
                    # Use saved answer if no conversation
                    chapter_qa[question_text] = main_answer
            elif main_answer:
                # Use saved answer if no conversation exists
                chapter_qa[question_text] = main_answer
        
        # Only include chapters with ANY content (answers OR conversations)
        if chapter_qa or chapter_full_conversations:
            export_data["chapters"][str(chapter_id)] = {
                "title": chapter["title"],
                "guidance": chapter.get("guidance", ""),
                "questions": chapter_qa,
                "full_conversations": chapter_full_conversations,
                "summary": chapter_data.get("summary", ""),
                "completed": chapter_data.get("completed", False),
                "total_questions": len(chapter["questions"]),
                "answered_questions": len(chapter_qa)
            }
        else:
            # Include empty chapters for completeness
            export_data["chapters"][str(chapter_id)] = {
                "title": chapter["title"],
                "guidance": chapter.get("guidance", ""),
                "questions": {},
                "full_conversations": {},
                "summary": "",
                "completed": False,
                "total_questions": len(chapter["questions"]),
                "answered_questions": 0
            }
    
    return json.dumps(export_data, indent=2)

def export_text():
    """Export all responses as formatted text - includes ALL chapters and conversations"""
    text = "=" * 60 + "\n"
    text += "MY LIFE STORY\n"
    text += "=" * 60 + "\n\n"
    text += f"Author: {st.session_state.user_id}\n"
    text += f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n"
    
    has_content = False
    
    for chapter in CHAPTERS:
        chapter_id = chapter["id"]
        chapter_data = st.session_state.responses.get(chapter_id, {})
        conversations = st.session_state.chapter_conversations.get(chapter_id, {})
        
        # Check if this chapter has any content
        chapter_has_content = False
        chapter_content = []
        
        for question_text in chapter["questions"]:
            # Check for saved answer
            has_saved_answer = question_text in chapter_data.get("questions", {})
            
            # Check for conversation
            has_conversation = question_text in conversations and conversations[question_text]
            
            if has_saved_answer or has_conversation:
                chapter_has_content = True
                
                # Prepare question block
                q_block = f"Q: {question_text}\n"
                
                if has_conversation:
                    # Extract all user answers from conversation
                    user_answers = []
                    ai_messages = []
                    
                    for msg in conversations[question_text]:
                        if msg["role"] == "user":
                            user_answers.append(f"A: {msg['content']}")
                        elif msg["role"] == "assistant":
                            # Clean up the AI welcome message if it's just the generic one
                            if not ("I'd love to hear your thoughts about this question:" in msg['content'] and len(conversations[question_text]) == 1):
                                ai_messages.append(f"AI Follow-up: {msg['content']}")
                    
                    # Add all conversation content
                    if user_answers:
                        q_block += "\n".join(user_answers) + "\n"
                    if ai_messages:
                        q_block += "\n".join(ai_messages) + "\n"
                
                elif has_saved_answer:
                    # Use saved answer
                    q_block += f"A: {chapter_data['questions'][question_text].get('answer', '')}\n"
                
                chapter_content.append(q_block)
        
        # Always include the chapter, but mark if empty
        text += f"\n{'=' * 60}\n"
        text += f"CHAPTER {chapter_id}: {chapter['title']}\n"
        text += f"{'=' * 60}\n\n"
        
        # Add chapter guidance
        text += f"Chapter Introduction:\n{chapter.get('guidance', '')}\n\n"
        
        if chapter_has_content:
            has_content = True
            text += f"{'-' * 50}\n\n"
            
            # Add all questions and answers
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
# STREAMLIT UI
# ────────────────────────────────────────────────
st.set_page_config(page_title="LifeStory AI", page_icon="📖", layout="wide")

# Clean header with logo - FIXED SPACING
st.markdown(f"""
<div class="main-header">
    <img src="{LOGO_URL}" class="logo-img" alt="LifeStory AI Logo">
    <h2 style="margin: 0; line-height: 1.2;">LifeStory AI</h2>
    <p style="font-size: 0.9rem; color: #666; margin: 0; line-height: 1.2;">Preserve Your Legacy • Share Your Story</p>
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
            st.session_state.chapter_conversations[chapter_id] = {}
        
        load_user_data()
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
    
    # Navigation controls for moving between questions
    st.subheader("Question Navigation")
    
    # Show current question number - LARGER
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

# Main content area - FULL WIDTH
# Get current chapter
current_chapter = CHAPTERS[st.session_state.current_chapter]
current_chapter_id = current_chapter["id"]
current_question_text = current_chapter["questions"][st.session_state.current_question]

# Show chapter header and question number with navigation
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.subheader(f"Chapter {current_chapter['id']}: {current_chapter['title']}")
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

# Show progress
chapter_data = st.session_state.responses.get(current_chapter_id, {})
questions_answered = len(chapter_data.get("questions", {}))
total_questions = len(current_chapter["questions"])

if total_questions > 0:
    progress = questions_answered / total_questions
    st.progress(min(progress, 1.0))

# Show chapter guidance
st.markdown(f"""
<div class="chapter-guidance">
    {current_chapter.get('guidance', '')}
</div>
""", unsafe_allow_html=True)

# Show current question - IN A PROPER BOX
st.markdown(f"""
<div class="question-box">
    {current_question_text}
</div>
""", unsafe_allow_html=True)

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
    # Show AI welcome message for new questions
    with st.chat_message("assistant"):
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
                    with col2:
                        if st.button("✏️", key=f"edit_{current_chapter_id}_{hash(current_question_text)}_{i}"):
                            st.session_state.editing = (current_chapter_id, current_question_text, i)
                            st.session_state.edit_text = message["content"]
                            st.rerun()

# Chat input - ALWAYS SHOW when not editing
if st.session_state.editing is None:
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
        
        # Save to database
        save_response(current_chapter_id, current_question_text, user_input)
        
        # Update conversation
        st.session_state.chapter_conversations[current_chapter_id][current_question_text] = conversation
        st.rerun()



import streamlit as st
import json
from datetime import datetime
from openai import OpenAI
import os

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

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.current_chapter = 0  # Index in CHAPTERS list
    st.session_state.current_question = 0  # Index in current chapter's questions
    st.session_state.responses = {}
    st.session_state.interview_started = False
    
    # Initialize response structure
    for chapter in CHAPTERS:
        st.session_state.responses[chapter["id"]] = {
            "title": chapter["title"],
            "questions": {},
            "summary": "",
            "completed": False
        }

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

# Store response
def store_response(chapter_id, question, answer):
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
        "privacy_level": "Not set"  # Can be updated later
    }

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

# Streamlit UI
st.set_page_config(page_title="Autobiography Creator", page_icon="📖", layout="wide")

st.title("📖 Autobiography Creator")
st.caption("A guided journey through your life story")

# Sidebar for navigation and controls
with st.sidebar:
    st.header("Chapter Progress")
    
    # Chapter progress tracker
    for i, chapter in enumerate(CHAPTERS):
        status = "✅" if st.session_state.responses[chapter["id"]]["completed"] else "🔄" if i == st.session_state.current_chapter else "⏳"
        st.write(f"{status} Chapter {chapter['id']}: {chapter['title']}")
        
        # Show progress within chapter
        if st.session_state.responses[chapter["id"]]["questions"]:
            progress = len(st.session_state.responses[chapter["id"]]["questions"]) / len(chapter["questions"])
            st.progress(progress)
            st.caption(f"{len(st.session_state.responses[chapter['id']]['questions'])}/{len(chapter['questions'])} questions answered")
    
    st.divider()
    
    # Navigation controls
    st.subheader("Navigation")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Previous Chapter", disabled=st.session_state.current_chapter == 0):
            st.session_state.current_chapter = max(0, st.session_state.current_chapter - 1)
            st.session_state.current_question = 0
            st.rerun()
    with col2:
        if st.button("Next Chapter →", disabled=st.session_state.current_chapter >= len(CHAPTERS)-1):
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
    st.subheader(f"Chapter {current_chapter['id']}: {current_chapter['title']}")
    
    # Show progress within current chapter
    answered = len(st.session_state.responses[current_chapter["id"]]["questions"])
    total = len(current_chapter["questions"])
    st.progress(answered / total if total > 0 else 0)
    st.caption(f"Question {st.session_state.current_question + 1} of {total} in this chapter")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Auto-start interview if not started
    if not st.session_state.interview_started:
        welcome_message = f"""Hello! I'm your biographer, and I'm here to help you create a beautiful, authentic record of your life story.

We'll work through {len(CHAPTERS)} chapters together:
1. Childhood
2. Family & Relationships  
3. Education & Growing Up

Let's begin with **Chapter 1: Childhood**.

{current_chapter['questions'][st.session_state.current_question]}"""
        
        st.session_state.messages.append({"role": "assistant", "content": welcome_message})
        st.session_state.interview_started = True
        st.rerun()

with col2:
    # Current chapter overview
    st.subheader("Current Chapter Questions")
    for i, question in enumerate(current_chapter["questions"]):
        status = "✅" if question in st.session_state.responses[current_chapter["id"]]["questions"] else "●"
        color = "green" if question in st.session_state.responses[current_chapter["id"]]["questions"] else "gray"
        st.markdown(f"<span style='color:{color}'>{status} {question[:50]}...</span>", unsafe_allow_html=True)
    
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
        
        st.success(f"Chapter {current_chapter['id']} completed! Summary generated.")
        st.rerun()

# Chat input
if prompt := st.chat_input("Your response..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Store the response
    current_question_text = current_chapter["questions"][st.session_state.current_question]
    store_response(current_chapter["id"], current_question_text, prompt)
    
    # Move to next question in current chapter
    if st.session_state.current_question < len(current_chapter["questions"]) - 1:
        st.session_state.current_question += 1
    else:
        # All questions in chapter answered
        st.session_state.responses[current_chapter["id"]]["completed"] = True
    
    # Generate AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Get current question for the prompt
                new_question = current_chapter["questions"][st.session_state.current_question]
                
                # Prepare conversation history for context
                messages_for_api = [
                    {"role": "system", "content": get_system_prompt()},
                    *st.session_state.messages[-6:]  # Last 3 exchanges for context
                ]
                
                response = client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=messages_for_api,
                    temperature=0.7,
                    max_tokens=500
                )
                
                ai_response = response.choices[0].message.content
                st.markdown(ai_response)
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                
            except Exception as e:
                st.error(f"Error generating response: {e}")
                # Fallback response
                fallback_response = f"""Thank you for sharing that. Your memories are the foundation of your story.

Now, I'd love to hear about: {new_question}"""
                
                st.markdown(fallback_response)
                st.session_state.messages.append({"role": "assistant", "content": fallback_response})

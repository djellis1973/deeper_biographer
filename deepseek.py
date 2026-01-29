import streamlit as st
import json
from datetime import datetime
from openai import OpenAI
import os
import sqlite3
import base64

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
    
    .ghostwriter-tag {{
        font-size: 0.8rem;
        color: #666;
        font-style: italic;
        margin-top: 0.5rem;
    }}
    
    /* Speech recording button styles */
    .speech-button {{
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        border: none;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
    }}
    
    .speech-button-primary {{
        background-color: #4CAF50;
        color: white;
    }}
    
    .speech-button-primary:hover {{
        background-color: #45a049;
    }}
    
    .speech-button-recording {{
        background-color: #f44336;
        color: white;
        animation: pulse 1.5s infinite;
    }}
    
    @keyframes pulse {{
        0% {{ opacity: 1; }}
        50% {{ opacity: 0.7; }}
        100% {{ opacity: 1; }}
    }}
    
    .speech-status {{
        font-size: 0.9rem;
        padding: 0.5rem;
        border-radius: 5px;
        margin-top: 0.5rem;
        display: none;
    }}
    
    .speech-status-listening {{
        background-color: #e8f5e8;
        border-left: 4px solid #4CAF50;
        display: block;
    }}
    
    .speech-status-processing {{
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        display: block;
    }}
    
    .speech-status-error {{
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        display: block;
    }}
    
    .speech-preview {{
        background-color: #f9f9f9;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin-top: 1rem;
        font-size: 0.95rem;
        line-height: 1.5;
    }}
    
    .speech-controls {{
        display: flex;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }}
    
    .mic-icon {{
        font-size: 1.2rem;
    }}
</style>
""", unsafe_allow_html=True)

# JavaScript for Speech Recognition
SPEECH_JS = """
<script>
// Speech recognition setup
let recognition = null;
let isRecording = false;
let finalTranscript = '';
let interimTranscript = '';

// Initialize speech recognition
function initSpeechRecognition() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'en-GB'; // UK English
        
        recognition.onstart = function() {
            isRecording = true;
            updateRecordingStatus(true);
            updateStatus('listening', 'Listening... Speak now.');
        };
        
        recognition.onresult = function(event) {
            interimTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript;
                } else {
                    interimTranscript += transcript;
                }
            }
            
            // Update preview
            updatePreview(finalTranscript + interimTranscript);
            
            // Auto-stop after silence (if using continuous: false, this happens automatically)
            if (interimTranscript.includes('.') || interimTranscript.includes('?')) {
                // Could add auto-stop logic here
            }
        };
        
        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            updateStatus('error', 'Error: ' + event.error);
            stopRecording();
        };
        
        recognition.onend = function() {
            isRecording = false;
            updateRecordingStatus(false);
            
            if (finalTranscript.trim()) {
                updateStatus('processing', 'Processing speech...');
                // Submit the final transcript after a short delay
                setTimeout(() => {
                    submitTranscript(finalTranscript);
                }, 500);
            } else {
                updateStatus('error', 'No speech detected. Please try again.');
            }
        };
        
        return true;
    } else {
        console.error('Speech recognition not supported');
        updateStatus('error', 'Speech recognition is not supported in your browser. Please use Chrome, Edge, or Safari.');
        return false;
    }
}

// Start recording
function startRecording() {
    if (!recognition && !initSpeechRecognition()) {
        return;
    }
    
    finalTranscript = '';
    interimTranscript = '';
    updatePreview('');
    
    try {
        recognition.start();
    } catch (error) {
        console.error('Failed to start recording:', error);
        updateStatus('error', 'Failed to start recording. Please try again.');
    }
}

// Stop recording
function stopRecording() {
    if (recognition && isRecording) {
        try {
            recognition.stop();
        } catch (error) {
            console.error('Error stopping recording:', error);
        }
    }
}

// Update recording status UI
function updateRecordingStatus(recording) {
    const button = document.getElementById('speech-button');
    const status = document.getElementById('speech-status');
    
    if (button) {
        if (recording) {
            button.innerHTML = '<span class="mic-icon">●</span> Stop Recording';
            button.className = 'speech-button speech-button-recording';
        } else {
            button.innerHTML = '<span class="mic-icon">🎤</span> Speak Your Answer';
            button.className = 'speech-button speech-button-primary';
        }
    }
}

// Update status message
function updateStatus(type, message) {
    const status = document.getElementById('speech-status');
    if (status) {
        status.className = 'speech-status speech-status-' + type;
        status.textContent = message;
        status.style.display = 'block';
    }
}

// Update preview text
function updatePreview(text) {
    const preview = document.getElementById('speech-preview');
    if (preview) {
        if (text.trim()) {
            preview.textContent = text;
            preview.style.display = 'block';
        } else {
            preview.style.display = 'none';
        }
    }
}

// Submit transcript to Streamlit
function submitTranscript(transcript) {
    // Clean up the transcript
    const cleanTranscript = transcript.trim();
    
    if (cleanTranscript) {
        // Send to Streamlit
        const data = {
            transcript: cleanTranscript
        };
        
        // Use Streamlit's setComponentValue to pass data back
        if (window.parent) {
            window.parent.postMessage({
                type: 'streamlit:setComponentValue',
                data: data
            }, '*');
        }
        
        // Reset after submission
        finalTranscript = '';
        interimTranscript = '';
        updatePreview('');
        updateStatus('listening', 'Answer submitted!');
        
        // Hide status after delay
        setTimeout(() => {
            const status = document.getElementById('speech-status');
            if (status) {
                status.style.display = 'none';
            }
        }, 2000);
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Check for speech recognition support
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
        updateStatus('error', 'Speech recognition not supported in this browser. Please use Chrome, Edge, or Safari.');
    }
});

// Handle keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Spacebar to start/stop recording (when focused)
    if (event.code === 'Space' && !event.target.matches('input, textarea')) {
        event.preventDefault();
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    }
});
</script>
"""

# HTML for speech interface
SPEECH_HTML = """
<div style="margin: 1rem 0;">
    <div style="text-align: center;">
        <button id="speech-button" class="speech-button speech-button-primary" onclick="startRecording()">
            <span class="mic-icon">🎤</span> Speak Your Answer
        </button>
        <div style="font-size: 0.8rem; color: #666; margin-top: 0.25rem;">
            Press Spacebar to start/stop • Speak clearly in UK English
        </div>
    </div>
    
    <div id="speech-status" class="speech-status"></div>
    
    <div id="speech-preview" class="speech-preview" style="display: none;">
        <strong>Preview:</strong><br>
        <span id="preview-text"></span>
    </div>
    
    <div class="speech-controls" style="justify-content: center; margin-top: 1rem;">
        <button onclick="startRecording()" class="speech-button speech-button-primary" style="padding: 0.4rem 0.8rem;">
            <span class="mic-icon">🎤</span> Start
        </button>
        <button onclick="stopRecording()" class="speech-button" style="background-color: #666; color: white; padding: 0.4rem 0.8rem;">
            <span class="mic-icon">⏹️</span> Stop
        </button>
        <button onclick="submitTranscript(finalTranscript)" class="speech-button" style="background-color: #2196F3; color: white; padding: 0.4rem 0.8rem;">
            <span class="mic-icon">✓</span> Submit
        </button>
    </div>
</div>
"""

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
        "completed": False
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
        "completed": False
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
    st.session_state.ghostwriter_mode = True  # New: Professional mode toggle
    st.session_state.speech_input = ""  # New: Store speech input
    st.session_state.show_speech = True  # New: Control speech UI visibility
    
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
    st.session_state.speech_input = ""
    
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

# Post-processing for speech-to-text (basic cleanup)
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
                                ai_messages.append(f"Interviewer: {msg['content']}")
                    
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

st.caption("A professional guided journey through your life story")

# Inject JavaScript for speech recognition
st.markdown(SPEECH_JS, unsafe_allow_html=True)

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
        st.session_state.speech_input = ""
        
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
        help="Show speech-to-text interface for voice input"
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
    st.caption("Speech recognition uses browser's built-in Web Speech API")

# Main content area - FULL WIDTH
# Get current chapter
current_chapter = CHAPTERS[st.session_state.current_chapter]
current_chapter_id = current_chapter["id"]
current_question_text = current_chapter["questions"][st.session_state.current_question]

# Show chapter header and question number with navigation
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

# Show speech interface if enabled
if st.session_state.show_speech:
    st.markdown("### 🎤 Speak Your Answer")
    st.markdown("""
    <div style="background-color: #f0f7ff; padding: 1rem; border-radius: 8px; border-left: 4px solid #4CAF50; margin-bottom: 1rem;">
        <strong>Voice Input Instructions:</strong>
        <ul style="margin: 0.5rem 0 0 1rem; padding-left: 1rem;">
            <li>Click "Speak Your Answer" or press <strong>Spacebar</strong> to start recording</li>
            <li>Speak clearly in UK English for best results</li>
            <li>Click Stop or press Spacebar again when finished</li>
            <li>Review your text before submitting</li>
            <li>Works best in Chrome, Edge, or Safari browsers</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Speech interface
    st.markdown(SPEECH_HTML, unsafe_allow_html=True)
    
    # Manual text input option
    st.markdown("---")
    st.markdown("### ✏️ Or Type Manually")

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

Take your time with this—good biographies are built from thoughtful reflection rather than quick answers."""
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

# Check for speech input from JavaScript
if st.session_state.speech_input:
    # Clean the speech input
    cleaned_text = clean_speech_text(st.session_state.speech_input)
    
    # Show preview and confirmation
    st.info(f"**Speech recognized:** {cleaned_text}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Use This Text", type="primary"):
            user_input = cleaned_text
            # Process as regular input
            st.session_state.speech_input = ""  # Clear after use
    with col2:
        if st.button("❌ Discard"):
            st.session_state.speech_input = ""
            st.rerun()

# Chat input - ALWAYS SHOW when not editing
if st.session_state.editing is None:
    user_input = st.chat_input("Type your answer here...")
    
    # Check if we should use speech input instead
    if not user_input and st.session_state.speech_input:
        user_input = clean_speech_text(st.session_state.speech_input)
        # Clear after use
        st.session_state.speech_input = ""
    
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
                        *conversation[-5:]  # Last 5 messages for context (increased for richer conversation)
                    ]
                    
                    # Adjust parameters based on mode
                    if st.session_state.ghostwriter_mode:
                        temperature = 0.8  # Slightly more creative for professional responses
                        max_tokens = 400   # Allow longer, more thoughtful responses
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
        st.rerun()

# Note about speech recognition support
st.markdown("""
<div style="font-size: 0.8rem; color: #666; margin-top: 2rem; padding: 1rem; background-color: #f9f9f9; border-radius: 5px;">
    <strong>Note about Speech Recognition:</strong> This feature uses your browser's built-in Web Speech API. 
    It works best in Chrome, Edge, and Safari on desktop or mobile. 
    The recognition happens entirely in your browser—no audio is sent to any server. 
    Accuracy may vary based on microphone quality and background noise.
</div>
""", unsafe_allow_html=True)

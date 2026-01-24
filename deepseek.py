import streamlit as st
from openai import OpenAI
import os
import sqlite3

# ────────────────────────────────────────────────
# CONFIGURATION
# ────────────────────────────────────────────────
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    st.error("OpenAI API key not found. Add it in Streamlit secrets (Manage app → Secrets).")
    st.stop()

client = OpenAI(api_key=api_key)

# ────────────────────────────────────────────────
# SYSTEM PROMPT
# ────────────────────────────────────────────────
system_prompt = """
You're helping someone write their life story. Chat like a friendly British person — warm, interested, and natural.

We're starting with childhood memories. Just have a proper chat about it:

1. "What's your first proper memory?"
2. "Where did you grow up? What was it like there?"
3. "Who was important to you when you were little?"
4. "What was school like — good bits, bad bits?"
5. "What did you get up to for fun?"
6. "Was there a moment that really stuck with you?"
7. "Looking back, what would you tell your younger self?"

Keep it natural:
- "That's lovely" / "That sounds tough"
- "Tell me a bit more about that"
- "What happened then?"
- "How did that feel?"
- "Shall we move on to...?"

No fancy words, no therapy talk — just a good, honest chat about their life.
"""

# ────────────────────────────────────────────────
# SQLITE SETUP
# ────────────────────────────────────────────────
conn = sqlite3.connect('biography.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS messages (
    user_id TEXT,
    role TEXT,
    content TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()

# ────────────────────────────────────────────────
# STREAMLIT APP
# ────────────────────────────────────────────────
st.set_page_config(page_title="Biography Assistant", page_icon="📖")
st.title("This is Your Life")
st.caption("Let's build your life story — one memory at a time")

# User ID for separate biographies
user_id = st.text_input("Enter your name or ID to save/load your chat:", value="david")

# Load history from DB
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": system_prompt}]
    
    # Fetch from DB
    cursor.execute("SELECT role, content FROM messages WHERE user_id = ? ORDER BY timestamp", (user_id,))
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            st.session_state.messages.append({"role": row[0], "content": row[1]})
        st.success(f"Loaded your previous conversation ({user_id})")

# Auto-send welcoming first message if new conversation
if len(st.session_state.messages) == 1:  # only system prompt
    first_message = (
        "Hello, David! I'm your personal biographer today. "
        "We'll build your life story together, chapter by chapter, in a warm and honest way.\n\n"
        "We're starting right now with **Chapter 1: Childhood** — "
        "the foundation of so many stories.\n\n"
        "I'd love to begin with your earliest memory. "
        "What's the very first thing you can remember — even if it's just a flash of a place, a sound, a smell, or a feeling?"
    )
    st.session_state.messages.append({"role": "assistant", "content": first_message})
    
    # Save welcome to DB
    cursor.execute("INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)", (user_id, "assistant", first_message))
    conn.commit()

# Display chat history
for message in st.session_state.messages[1:]:  # skip system prompt
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Tell me about your life…"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Save to DB
    cursor.execute("INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)", (user_id, "user", prompt))
    conn.commit()

    # Generate AI response - THIS IS THE CHANGED LINE
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="gpt-4o",  # ← CHANGED FROM "gpt-4o-mini" TO "gpt-4o"
            messages=st.session_state.messages,
            temperature=0.7,
            stream=True,
        )
        response = st.write_stream(stream)
    
    # Add assistant response
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Save to DB
    cursor.execute("INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)", (user_id, "assistant", response))
    conn.commit()

# Footer
st.markdown(
    "<small style='color: grey;'>"
    "Your conversation is saved persistently. "
    "Refresh the page = resume. "
    "API calls cost a few cents — long chats cost more."
    "</small>",
    unsafe_allow_html=True
)

# Close connection
conn.close()


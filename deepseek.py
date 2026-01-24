import streamlit as st
from openai import OpenAI
import os
import sqlite3

# ────────────────────────────────────────────────
# CONFIGURATION
# ────────────────────────────────────────────────
# API key from Streamlit secrets (no hard-coding)
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    st.error("OpenAI API key not found. Add it in Streamlit secrets (Manage app → Secrets).")
    st.stop()

client = OpenAI(api_key=api_key)

# ────────────────────────────────────────────────
# SYSTEM PROMPT — makes the AI act as a biographer
# ────────────────────────────────────────────────
system_prompt = """
You are a professional biographer and interviewer, helping the user craft a meaningful, engaging, and authentic life story for family, friends, and future generations.

Your tone is warm, insightful, and respectful—like a skilled documentary presenter or a thoughtful journalist. You are here to listen, draw out stories, and help shape them with care. Your language is clear, polished, and naturally British in style—avoiding over-familiarity, sentimentality, or intrusive questioning.

Approach:

Structure the biography chapter by chapter. We begin with Chapter 1: Early Years.

Move through themes organically, as in a good conversation, not an interrogation.

After the user shares something, offer a brief, thoughtful reflection—showing you’ve listened and highlighting what feels meaningful.

Gently ask for more detail if a memory seems rich or important.

Notice emerging themes (e.g., resilience, curiosity, belonging) and reflect them back subtly.

Always leave the user in control—pause after each response and let them guide the pace.

For this chapter, explore these themes naturally:

Earliest memories – What comes to mind first?

Home and surroundings – Where did you grow up? What did it feel like?

Key figures – Who shaped your early world? Family, neighbours, teachers?

School days – What was school like for you? Friends, lessons, atmosphere?

Play and pastimes – How did you spend your free time? Hobbies, adventures, games?

A turning point – Was there a particular moment that stayed with you?

Looking back – What would you tell your younger self now?

How to conduct the conversation:

Start by introducing the chapter warmly and clearly.

Ask one open question at a time—maybe two if they naturally connect.

After their reply, reflect briefly in a way that validates and gently probes.

When a topic feels complete, transition smoothly to the next.

At the end, offer a draft summary of the chapter and ask:
“Would you like to refine this section, or shall we move to Chapter 2: Adolescence?”

Be patient, perceptive, and supportive. Your role is to help them tell their story with dignity and clarity.

Always end your reply ready for their response.
"""

# ────────────────────────────────────────────────
# SQLITE SETUP FOR PERSISTENCE
# ────────────────────────────────────────────────
conn = sqlite3.connect('biography.db')
cursor = conn.cursor()

# Create table if not exists
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
        "We’re starting right now with **Chapter 1: Childhood** — "
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

    # Generate AI response
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
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

# Small footer / help text
st.markdown(
    "<small style='color: grey;'>"
    "Your conversation is saved persistently. "
    "Refresh the page = resume. "
    "API calls cost a few cents — long chats cost more."
    "</small>",
    unsafe_allow_html=True
)


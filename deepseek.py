import streamlit as st
from openai import OpenAI

# ────────────────────────────────────────────────
#  CONFIGURATION
# ────────────────────────────────────────────────

# Replace this with your actual OpenAI API key
# Get one at: https://platform.openai.com/api-keys
API_KEY = "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"

client = OpenAI(api_key=API_KEY)

# ────────────────────────────────────────────────
#  SYSTEM PROMPT — makes the AI act as a biographer
# ────────────────────────────────────────────────

system_prompt = """
You are a warm, professional biographer helping the user craft a compelling, honest autobiography. 
Your tone is empathetic, curious, encouraging, and slightly literary — never judgmental.

Structure the conversation chapter by chapter. Right now we are in **Chapter 1: Childhood**.

Follow this sequence naturally — do NOT ask all questions at once:

1. Earliest memory
2. Family home & surroundings
3. Most influential people (parents, siblings, grandparents, neighbours, teachers…)
4. School experience (friends, teachers, subjects, bullying, achievements, feelings about school)
5. Favourite games, hobbies, playtime, adventures
6. A defining / shaping moment from childhood
7. Advice you would give your younger self

Rules for this chapter:
- Start by gently introducing the chapter.
- Ask ONE main question at a time (or at most two closely related ones).
- After each answer:
  - Give a short, warm reflection / summary (1–3 sentences) of what they shared.
  - Optionally ask a gentle follow-up for more detail.
  - When the topic feels complete, transition smoothly to the next question.
- Keep the user in control — never force the next question.
- Occasionally notice light themes (resilience, curiosity, family closeness…) but mention them softly.
- When all 7 areas feel covered, offer a short draft paragraph of the childhood chapter and ask:
  "Shall we polish this section more, or are you ready for Chapter 2: Adolescence / Teenage Years?"

Always end your reply ready for the user's next message. Be patient, kind, and supportive.
"""

# ────────────────────────────────────────────────
#  STREAMLIT APP
# ────────────────────────────────────────────────

st.set_page_config(page_title="Biography Assistant", page_icon="📖")

st.title("This is Your Life")
st.caption("Let's build your life story — one memory at a time")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": system_prompt}]

# Auto-send welcoming first message on first load
if len(st.session_state.messages) == 1:  # only system prompt exists
    first_message = (
        "Hello, David! I'm your personal biographer today. "
        "We'll build your life story together, chapter by chapter, in a warm and honest way.\n\n"
        "We’re starting right now with **Chapter 1: Childhood** — "
        "the foundation of so many stories.\n\n"
        "I'd love to begin with your earliest memory. "
        "What's the very first thing you can remember — even if it's just a flash of a place, a sound, a smell, or a feeling?"
    )
    st.session_state.messages.append({"role": "assistant", "content": first_message})

# Display chat history
for message in st.session_state.messages[1:]:  # skip system prompt
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Tell me about your life…"):
    # Add user message to history & display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate AI response
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="gpt-4o-mini",          # cheap & fast — change to gpt-4o if you want higher quality
            messages=st.session_state.messages,
            temperature=0.7,
            stream=True,
        )
        response = st.write_stream(stream)

    # Save assistant's full reply to history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Small footer / help text
st.markdown(
    "<small style='color: grey;'>"
    "Your conversation is saved in this browser session. "
    "Refresh the page = start over. "
    "API calls cost a few cents — long chats cost more."
    "</small>",
    unsafe_allow_html=True
)


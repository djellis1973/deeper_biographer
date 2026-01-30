# biography_publisher.py - STANDALONE PUBLISHER
import streamlit as st
from datetime import datetime

# ============================================================================
# 1. PAGE SETUP
# ============================================================================
st.set_page_config(page_title="Biography Publisher", layout="wide")
st.title("📖 Biography Publisher")
st.markdown("***Test this standalone tool first. It uses example stories.***")

# ============================================================================
# 2. EXAMPLE STORIES (MOCK DATA - REPLACE LATER)
# ============================================================================
EXAMPLE_STORIES = [
    {
        "session_title": "Childhood",
        "question": "What is your earliest memory?",
        "answer": "I remember sitting on my grandfather's lap while he read me stories. The book had red covers and smelled like old paper and his pipe tobacco."
    },
    {
        "session_title": "Childhood", 
        "question": "Can you describe your family home growing up?",
        "answer": "We lived in a small brick house with a big oak tree in the backyard. My room faced east, so I woke up with sunlight streaming through the white curtains every morning."
    },
    {
        "session_title": "Family & Relationships",
        "question": "How would you describe your relationship with your parents?",
        "answer": "My mother was a primary school teacher – incredibly patient and organized. My father worked in construction – he had strong, rough hands but the gentlest voice when he read to us at night."
    }
]

# ============================================================================
# 3. CORE PUBLISHING FUNCTION
# ============================================================================
def create_biography(stories, author_name="The Author"):
    """
    Takes a list of stories and an author's name.
    Returns a beautifully formatted biography text.
    """
    # Build the biography text
    bio_text = f"# The Life Story of {author_name}\n\n"
    bio_text += "_A personal biography, compiled from cherished memories._\n\n"
    bio_text += "---\n\n"
    
    # Group stories by session
    sessions = {}
    for story in stories:
        session = story["session_title"]
        if session not in sessions:
            sessions[session] = []
        sessions[session].append(story)
    
    # Write each session
    for session_title, session_stories in sessions.items():
        bio_text += f"## {session_title}\n\n"
        
        for story in session_stories:
            bio_text += f"### {story['question']}\n\n"
            # Format the answer into nice paragraphs
            answer_paragraphs = story['answer'].split('. ')
            for para in answer_paragraphs:
                if para.strip():  # Skip empty strings
                    bio_text += f"{para.strip()}.\n\n"
        
        bio_text += "---\n\n"
    
    # Add closing
    bio_text += "### Epilogue\n\n"
    bio_text += "This collection of memories forms a unique portrait of a life. "
    bio_text += "Each story is a thread in the tapestry of experience.\n\n"
    
    # Add generation info
    bio_text += f"\n\n---\n"
    bio_text += f"*Compiled on {datetime.now().strftime('%B %d, %Y')}.*\n"
    bio_text += "*For private reflection and legacy.*"
    
    return bio_text

# ============================================================================
# 4. USER INTERFACE
# ============================================================================
st.sidebar.header("🛠️ Publishing Settings")
author_name = st.sidebar.text_input("**Author's Name for the Cover:**", value="Alex Johnson")

st.sidebar.markdown("---")
st.sidebar.subheader("Example Stories Preview")
for i, story in enumerate(EXAMPLE_STORIES):
    st.sidebar.caption(f"**{story['session_title']}**")
    st.sidebar.write(f"*{story['question']}*")

# ============================================================================
# 5. MAIN AREA: PREVIEW & PUBLISH BUTTON
# ============================================================================
st.subheader("📋 Story Preview")

# Show the example stories in the main area
for i, story in enumerate(EXAMPLE_STORIES):
    with st.expander(f"**{story['session_title']}**: {story['question']}", expanded=False):
        st.info(story['answer'])
        st.caption(f"Example story #{i+1}")

st.markdown("---")
st.subheader("🚀 Generate Your Biography")

# THE BIG PUBLISH BUTTON
if st.button("🖨️ **PUBLISH NOW**", type="primary", use_container_width=True, help="Click to generate and download the biography"):
    
    with st.spinner("🔄 **Gathering stories and formatting your biography...**"):
        # CREATE THE BIOGRAPHY
        final_biography_text = create_biography(EXAMPLE_STORIES, author_name)
        
        # Show success message
        st.success("✅ **Biography created successfully!**")
        
        # Show a small preview
        with st.expander("📄 **Quick Preview (First 500 characters)**", expanded=True):
            st.text(final_biography_text[:500] + "...")
        
        st.balloons()  # Little celebration!
        
        # THE DOWNLOAD BUTTON
        st.markdown("---")
        st.subheader("📥 Download Your Biography")
        
        # Create a clean filename
        clean_author_name = author_name.replace(" ", "_")
        filename = f"{clean_author_name}_Life_Story.txt"
        
        st.download_button(
            label=f"**DOWNLOAD '{filename}'**",
            data=final_biography_text,
            file_name=filename,
            mime="text/plain",
            type="primary",
            use_container_width=True
        )
        
        st.caption("The file is a standard .txt file that can be opened in any text editor, word processor, or ebook reader.")

# ============================================================================
# 6. "WHAT'S NEXT" SECTION
# ============================================================================
st.markdown("---")
st.subheader("🔗 What's Next?")
st.markdown("""
Once this publisher works perfectly:

1.  **Test it** → Make sure the download button gives you a nice .txt file.
2.  **Deploy it** → Push this file to GitHub. Community Cloud will show it as a separate app.
3.  **Connect it** → Later, we'll add these functions to your main `deepseek.py` with **3 lines of code**.

**Your main interview app remains 100% untouched and working.**
""")

# Show the connection code for the future
with st.expander("🔮 **Future Connection Code (For Later)**"):
    st.code("""
# === IN YOUR MAIN deepseek.py (LATER) ===
# Just add this where you want the publish button:

# 1. Get the user's REAL stories from your app's memory
real_user_stories = []  # You'll fill this with actual data

# 2. Import the publishing function (after testing)
from biography_publisher import create_biography

# 3. Generate and offer download
if st.button("📖 Publish My Biography"):
    bio_text = create_biography(real_user_stories, user_name)
    st.download_button("Download", bio_text, "my_biography.txt")
    """, language="python")

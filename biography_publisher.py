# biography_publisher.py - REAL PUBLISHER WITH AUTO-FILLED NAME
import streamlit as st
import sqlite3
from datetime import datetime

# Page setup
st.set_page_config(page_title="Biography Publisher", layout="wide")
st.title("📖 Legacy Biography Publisher")

# ============================================================================
# 1. FUNCTION TO GET REAL DATA FROM YOUR DATABASE
# ============================================================================
def get_real_user_stories(user_name):
    """Get ACTUAL stories from your life_story.db database"""
    try:
        # Connect to your shared database
        conn = sqlite3.connect('life_story.db')
        cursor = conn.cursor()
        
        # Query to get all responses for this user
        cursor.execute("""
            SELECT session_id, question, answer, timestamp 
            FROM responses 
            WHERE user_id = ? 
            AND answer IS NOT NULL 
            AND answer != ''
            ORDER BY session_id, timestamp
        """, (user_name,))
        
        stories = cursor.fetchall()
        conn.close()
        
        # Format the data
        formatted_stories = []
        for session_id, question, answer, timestamp in stories:
            formatted_stories.append({
                "session": f"Chapter {session_id}",
                "question": question,
                "answer": answer,
                "date": timestamp[:10] if timestamp else ""
            })
        
        return formatted_stories
        
    except Exception as e:
        st.error(f"⚠️ Database error: {str(e)}")
        return []

# ============================================================================
# 2. FUNCTION TO CREATE BIOGRAPHY
# ============================================================================
def create_real_biography(stories, author_name):
    """Create biography from REAL user stories"""
    if not stories:
        return "No stories found to publish."
    
    bio_text = f"# The Life Story of {author_name}\n\n"
    bio_text += f"_Compiled on {datetime.now().strftime('%B %d, %Y')}_\n\n"
    bio_text += "---\n\n"
    
    # Group by session
    current_session = None
    story_count = 0
    for story in stories:
        story_count += 1
        if story["session"] != current_session:
            bio_text += f"## {story['session']}\n\n"
            current_session = story["session"]
        
        bio_text += f"### {story_count}. {story['question']}\n\n"
        bio_text += f"{story['answer']}\n\n"
    
    bio_text += "---\n\n"
    bio_text += f"*This personal biography contains {story_count} stories across {len(set(s['session'] for s in stories))} chapters.*\n"
    bio_text += "*Created to preserve your unique legacy.*"
    
    return bio_text

# ============================================================================
# 3. MAIN APP INTERFACE WITH URL PARAMETER SUPPORT
# ============================================================================
st.markdown("### 🔍 Find Your Real Stories")

# Try to get name from URL parameters first
try:
    query_params = st.experimental_get_query_params()
    url_name = query_params.get("name", [None])[0]
except:
    url_name = None

# User input - pre-fill if name came from URL
if url_name:
    st.info(f"📋 Name received from main app: **{url_name}**")
    # Pre-fill the input with the URL parameter
    user_name = st.text_input("**Your Name:**", value=url_name, key="real_name")
    auto_filled = True
else:
    st.write("**Enter your exact name** as used in the main interview app:")
    user_name = st.text_input("**Your Name:**", key="real_name", placeholder="e.g., David Ellis")
    auto_filled = False

# Search button
if st.button("🔎 Search Database", type="primary"):
    if user_name:
        with st.spinner("Searching database..."):
            # Get REAL stories from database
            real_stories = get_real_user_stories(user_name)
            
            if real_stories:
                st.session_state.real_stories = real_stories
                st.session_state.real_author = user_name
                
                if auto_filled:
                    st.success(f"✅ Found **{len(real_stories)}** stories for you, **{user_name}**!")
                else:
                    st.success(f"✅ Found **{len(real_stories)}** real story(s) for **{user_name}**!")
                
                # Show quick stats
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Stories", len(real_stories))
                with col2:
                    sessions = len(set(s["session"] for s in real_stories))
                    st.metric("Chapters", sessions)
                
                # Show preview
                with st.expander("📋 Preview First 3 Stories", expanded=True):
                    for i, story in enumerate(real_stories[:3]):
                        st.markdown(f"**{story['session']}**")
                        st.markdown(f"*{story['question']}*")
                        st.write(story['answer'][:150] + "..." if len(story['answer']) > 150 else story['answer'])
                        if i < 2:
                            st.divider()
            else:
                st.warning(f"❌ No stories found for '{user_name}'.")
                st.info("""
                **Possible reasons:**
                1. Use the **exact name** from your main app (check capitalization)
                2. Make sure you've saved stories in the main app first
                3. Wait a moment after saving before checking here
                """)
    else:
        st.info("Please enter your name first.")

# ============================================================================
# 4. PUBLISH REAL STORIES
# ============================================================================
if 'real_stories' in st.session_state and st.session_state.real_stories:
    st.markdown("---")
    st.subheader(f"🚀 Ready to Publish")
    
    if st.button("🖨️ Generate Biography", type="primary", use_container_width=True):
        with st.spinner("Creating your biography..."):
            biography = create_real_biography(
                st.session_state.real_stories,
                st.session_state.real_author
            )
        
        # Download button
        safe_name = st.session_state.real_author.replace(" ", "_")
        file_name = f"{safe_name}_Biography.txt"
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.download_button(
                label="📥 Download Biography",
                data=biography,
                file_name=file_name,
                mime="text/plain",
                type="primary",
                use_container_width=True
            )
        with col2:
            st.button("🔄 Search Again", on_click=lambda: st.session_state.clear())
        
        st.balloons()
        st.success("Your **real biography** is ready!")

# ============================================================================
# 5. FOOTER
# ============================================================================
st.markdown("---")
st.caption("📊 **Connected to real database** | Auto-fill enabled from main app")

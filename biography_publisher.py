# biography_publisher.py - REAL PUBLISHER (NO SAMPLE DATA)
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
        
        # DEBUG: Check what's in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        st.write(f"🔍 **Debug: Found tables:** {tables}")
        
        # Check if responses table exists
        if ('responses',) in tables:
            st.success("✅ Found 'responses' table!")
            
            # Show table structure
            cursor.execute("PRAGMA table_info(responses);")
            columns = cursor.fetchall()
            st.write(f"📋 **Table columns:** {[col[1] for col in columns]}")
            
            # Show all users in database
            cursor.execute("SELECT DISTINCT user_id FROM responses;")
            users = cursor.fetchall()
            st.write(f"👥 **Users in database:** {[user[0] for user in users]}")
            
            # Show count of stories for this user
            cursor.execute("SELECT COUNT(*) FROM responses WHERE user_id = ?", (user_name,))
            count = cursor.fetchone()[0]
            st.write(f"📊 **Stories for '{user_name}':** {count}")
            
            if count > 0:
                # Show sample of what we'll retrieve
                cursor.execute("SELECT session_id, question, answer, timestamp FROM responses WHERE user_id = ? LIMIT 2", (user_name,))
                samples = cursor.fetchall()
                st.write(f"📝 **Sample stories:**")
                for session_id, question, answer, timestamp in samples:
                    st.write(f"  - Session {session_id}: '{question[:50]}...'")
        else:
            st.error("❌ 'responses' table not found in database!")
            return []
        
        # Query to get all responses for this user (EXACT MATCH to your main app)
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
        
        st.write(f"✅ **Query successful! Found {len(stories)} raw records**")
        
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
        import traceback
        st.code(traceback.format_exc())
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
# 3. MAIN APP INTERFACE
# ============================================================================
st.markdown("### 🔍 Find Your Real Stories")
st.write("**Enter your exact name** as used in the main interview app:")

# User input
user_name = st.text_input("**Your Name:**", key="real_name", placeholder="e.g., David Ellis")

# Search button
if st.button("🔎 Search Database", type="primary"):
    if user_name:
        with st.spinner("Searching database..."):
            # Get REAL stories from database
            real_stories = get_real_user_stories(user_name)
            
            if real_stories:
                st.session_state.real_stories = real_stories
                st.session_state.real_author = user_name
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
                **Tips:**
                1. Use the **exact name** from your main app
                2. Check capitalization (David vs david)
                3. Make sure you've saved stories in the main app first
                4. Wait a moment after saving in main app before checking here
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
st.caption("📊 **Connected to real database** | Debug mode active")

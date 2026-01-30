# biography_publisher.py - PUBLISHER THAT READS DATA FROM URL
import streamlit as st
import json
import base64
from datetime import datetime

# Page setup
st.set_page_config(page_title="Biography Publisher", layout="wide")
st.title("📖 Legacy Biography Publisher")

def decode_stories_from_url():
    """Extract stories from URL parameter"""
    try:
        query_params = st.experimental_get_query_params()
        encoded_data = query_params.get("data", [None])[0]
        
        if not encoded_data:
            return None
            
        # Decode the data
        json_data = base64.b64decode(encoded_data).decode()
        stories_data = json.loads(json_data)
        
        return stories_data
    except:
        return None

def create_biography_from_data(stories_data):
    """Create biography from the provided data"""
    user_name = stories_data.get("user", "Unknown")
    stories_dict = stories_data.get("stories", {})
    
    bio_text = f"# The Life Story of {user_name}\n\n"
    bio_text += f"_Compiled on {datetime.now().strftime('%B %d, %Y')}_\n\n"
    bio_text += "---\n\n"
    
    # Format all stories
    all_stories = []
    for session_id, session_data in sorted(stories_dict.items()):
        session_title = session_data.get("title", f"Chapter {session_id}")
        
        for question, answer_data in session_data.get("questions", {}).items():
            all_stories.append({
                "session": session_title,
                "question": question,
                "answer": answer_data.get("answer", ""),
                "date": answer_data.get("timestamp", "")[:10]
            })
    
    # Add to biography
    current_session = None
    story_count = 0
    for story in all_stories:
        story_count += 1
        if story["session"] != current_session:
            bio_text += f"## {story['session']}\n\n"
            current_session = story["session"]
        
        bio_text += f"### {story_count}. {story['question']}\n\n"
        bio_text += f"{story['answer']}\n\n"
    
    bio_text += "---\n\n"
    bio_text += f"*This personal biography contains {story_count} stories across {len(set(s['session'] for s in all_stories))} chapters.*\n"
    bio_text += "*Created to preserve your unique legacy.*"
    
    return bio_text, all_stories, user_name

# ============================================================================
# MAIN APP INTERFACE
# ============================================================================
st.markdown("### 🔍 Your Biography Generator")

# Try to get data from URL first
stories_data = decode_stories_from_url()

if stories_data:
    # Auto-process data from URL
    user_name = stories_data.get("user", "Unknown")
    story_count = sum(len(session.get("questions", {})) for session in stories_data.get("stories", {}).values())
    
    st.success(f"✅ Welcome, **{user_name}**! Found **{story_count} stories** from your main app.")
    
    # Show preview
    with st.expander("📋 Preview Your Stories", expanded=True):
        all_stories = []
        for session_id, session_data in stories_data.get("stories", {}).items():
            st.markdown(f"**{session_data.get('title', f'Chapter {session_id}')}**")
            for question, answer_data in session_data.get("questions", {}).items():
                answer = answer_data.get("answer", "")
                st.write(f"**Q:** {question}")
                st.write(f"**A:** {answer[:150]}..." if len(answer) > 150 else answer)
                st.divider()
                all_stories.append({"question": question, "answer": answer})
    
    # Generate biography button
    if st.button("🖨️ Generate My Biography", type="primary", use_container_width=True):
        with st.spinner("Creating your beautiful biography..."):
            biography, all_stories_list, author_name = create_biography_from_data(stories_data)
        
        # Show the biography
        st.subheader("📖 Your Biography")
        st.markdown(biography)
        
        # Download button
        safe_name = author_name.replace(" ", "_")
        file_name = f"{safe_name}_Biography.txt"
        
        st.download_button(
            label="📥 Download Biography",
            data=biography,
            file_name=file_name,
            mime="text/plain",
            type="primary",
            use_container_width=True
        )
        
        st.balloons()
        st.success(f"✅ Biography created with **{len(all_stories_list)} stories**!")
        
    # Manual upload option as backup
    st.divider()
    st.markdown("### 📤 Alternative: Upload Your Export File")
    st.write("If the link didn't bring your data, upload the JSON file you downloaded from the main app:")
    
    uploaded_file = st.file_uploader("Choose your stories JSON file", type=['json'])
    if uploaded_file:
        try:
            uploaded_data = json.load(uploaded_file)
            st.success(f"✅ Loaded stories for **{uploaded_data.get('user', 'Unknown')}**")
            
            if st.button("Generate from Uploaded File", type="secondary"):
                biography, all_stories_list, author_name = create_biography_from_data(uploaded_data)
                
                st.download_button(
                    label="📥 Download Biography from Upload",
                    data=biography,
                    file_name=f"{author_name.replace(' ', '_')}_Biography.txt",
                    mime="text/plain"
                )
        except:
            st.error("❌ Invalid file format. Please upload the JSON file from the main app.")

else:
    # No data in URL - show manual options
    st.info("📋 **How to use this publisher:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🚀 **Automatic Method**
        1. Go to your main interview app
        2. Answer some questions
        3. Click the publisher link at the bottom
        4. Your data comes automatically!
        """)
    
    with col2:
        st.markdown("""
        ### 📤 **Manual Method**
        1. In main app, use **Export Current Progress**
        2. Download the JSON file
        3. Upload it here:
        """)
        
        uploaded_file = st.file_uploader("Upload your stories JSON file", type=['json'])
        if uploaded_file:
            try:
                uploaded_data = json.load(uploaded_file)
                st.success(f"✅ Loaded stories for **{uploaded_data.get('user', 'Unknown')}**")
                
                if st.button("Generate Biography from File", type="primary"):
                    biography, all_stories_list, author_name = create_biography_from_data(uploaded_data)
                    
                    st.download_button(
                        label="📥 Download Your Biography",
                        data=biography,
                        file_name=f"{author_name.replace(' ', '_')}_Biography.txt",
                        mime="text/plain"
                    )
            except:
                st.error("❌ Invalid file format. Please upload the JSON file from the main app.")

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.caption("✨ **No database needed** • Your data stays private • Works with your existing main app")

# biography_publisher.py - Fixed for new list format
import streamlit as st
import json
import base64
from datetime import datetime
import re
import os
import random
import io

# Page config
st.set_page_config(
    page_title="Biography Publisher",
    page_icon="📚",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 20px 20px;
        color: white;
    }
    .story-card {
        border-left: 4px solid #667eea;
        padding: 1rem;
        margin: 1rem 0;
        background: #f8f9fa;
        border-radius: 0 10px 10px 0;
    }
    .export-box {
        border: 2px solid #667eea;
        border-radius: 10px;
        padding: 2rem;
        margin: 2rem 0;
        background: white;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
<h1>📚 Biography Publisher</h1>
<p>Transform your stories into a beautifully formatted biography</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'stories_data' not in st.session_state:
    st.session_state.stories_data = None
if 'formatted_text' not in st.session_state:
    st.session_state.formatted_text = ""
if 'book_title' not in st.session_state:
    st.session_state.book_title = ""
if 'author_name' not in st.session_state:
    st.session_state.author_name = ""
if 'cover_color' not in st.session_state:
    st.session_state.cover_color = "#2c3e50"
if 'selected_format' not in st.session_state:
    st.session_state.selected_format = "interview"
if 'include_toc' not in st.session_state:
    st.session_state.include_toc = True
if 'include_dates' not in st.session_state:
    st.session_state.include_dates = False

# Check for URL data
query_params = st.query_params
if 'data' in query_params:
    try:
        encoded_data = query_params['data']
        decoded_data = base64.b64decode(encoded_data).decode('utf-8')
        st.session_state.stories_data = json.loads(decoded_data)
        st.success("✅ Stories loaded successfully!")
        
        # Auto-populate title and author
        if st.session_state.stories_data:
            user_profile = st.session_state.stories_data.get('user_profile', {})
            if user_profile:
                first_name = user_profile.get('first_name', '')
                last_name = user_profile.get('last_name', '')
                if first_name and last_name:
                    st.session_state.author_name = f"{first_name} {last_name}"
                    st.session_state.book_title = f"The Story of {first_name} {last_name}"
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Publication Settings")
    
    st.subheader("Book Details")
    st.session_state.book_title = st.text_input(
        "Book Title",
        value=st.session_state.book_title,
        placeholder="Enter book title"
    )
    
    st.session_state.author_name = st.text_input(
        "Author Name",
        value=st.session_state.author_name,
        placeholder="Enter author name"
    )
    
    st.session_state.cover_color = st.color_picker(
        "Cover Color",
        value=st.session_state.cover_color
    )
    
    st.subheader("Format Options")
    st.session_state.selected_format = st.radio(
        "Format Style",
        ["interview", "biography", "memoir"],
        format_func=lambda x: {
            "interview": "📝 Interview Q&A",
            "biography": "📖 Continuous Biography",
            "memoir": "📚 Chapter-based Memoir"
        }[x],
        index=0
    )
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.include_toc = st.checkbox("Table of Contents", value=True)
    with col2:
        st.session_state.include_dates = st.checkbox("Include Dates", value=False)
    
    st.divider()
    
    # File upload alternative
    st.subheader("📂 Upload Stories")
    uploaded_file = st.file_uploader("Upload your stories JSON", type=['json'])
    if uploaded_file is not None:
        try:
            stories_json = json.load(uploaded_file)
            st.session_state.stories_data = stories_json
            st.success("✅ File uploaded successfully!")
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

# Main content area
if st.session_state.stories_data:
    stories_data = st.session_state.stories_data
    user_id = stories_data.get('user', 'Unknown')
    user_profile = stories_data.get('user_profile', {})
    
    # Display user info
    with st.expander("👤 User Information", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("User ID", user_id)
        with col2:
            total_stories = stories_data.get('summary', {}).get('total_stories', 0)
            st.metric("Total Stories", total_stories)
        with col3:
            total_sessions = stories_data.get('summary', {}).get('total_sessions', 0)
            st.metric("Sessions", total_sessions)
        
        if user_profile:
            st.write("**Profile Details:**")
            profile_cols = st.columns(4)
            profile_keys = ['first_name', 'last_name', 'email', 'gender', 'birthdate']
            for i, key in enumerate(profile_keys):
                with profile_cols[i % 4]:
                    if key in user_profile:
                        st.text_input(key.replace('_', ' ').title(), 
                                    user_profile[key], disabled=True)
    
    # Process stories based on format
    st.subheader("📖 Story Preview")
    
    # FIXED: Handle both old dictionary format and new list format
    stories = stories_data.get("stories", {})
    
    if isinstance(stories, list):
        # NEW FORMAT: List of {"question": "...", "answer": "...", "session_id": 1, ...}
        st.info("📋 New List Format Detected")
        
        # Group by session for display
        grouped_stories = {}
        for story in stories:
            session_id = story.get("session_id", "1")
            if session_id not in grouped_stories:
                grouped_stories[session_id] = {
                    "title": story.get("session_title", f"Session {session_id}"),
                    "stories": []
                }
            grouped_stories[session_id]["stories"].append(story)
        
        # Display grouped stories
        for session_id, session_info in grouped_stories.items():
            with st.expander(f"📚 {session_info['title']} ({len(session_info['stories'])} stories)"):
                for i, story in enumerate(session_info["stories"]):
                    question = story.get("question", f"Story {i+1}")
                    answer = story.get("answer", "")
                    
                    if answer:
                        st.markdown(f"**{question}**")
                        st.text_area(f"Answer {i+1}", answer, height=100, 
                                    key=f"preview_{session_id}_{i}", disabled=True)
                        st.divider()
    else:
        # OLD FORMAT: Dictionary with session_id as keys
        st.info("📋 Old Dictionary Format Detected")
        
        for session_id, session_data in stories.items():
            session_title = session_data.get("title", f"Session {session_id}")
            questions = session_data.get("questions", {})
            
            with st.expander(f"📚 {session_title} ({len(questions)} questions)"):
                for question, answers in questions.items():
                    if isinstance(answers, list) and answers:
                        answer_text = answers[0].get("answer", "") if isinstance(answers[0], dict) else str(answers[0])
                    else:
                        answer_text = str(answers)
                    
                    st.markdown(f"**{question}**")
                    st.text_area(f"Answer", answer_text, height=100, 
                                key=f"preview_{session_id}_{hash(question)}", disabled=True)
                    st.divider()
    
    # Formatting and Export Section
    st.markdown("---")
    st.subheader("🖨️ Generate Biography")
    
    format_col1, format_col2, format_col3 = st.columns(3)
    
    with format_col1:
        if st.button("📄 Preview Text Format", use_container_width=True):
            with st.spinner("Formatting text..."):
                formatted_text = ""
                
                if isinstance(stories, list):
                    # Format for list structure
                    formatted_text += f"{st.session_state.book_title}\n"
                    formatted_text += f"by {st.session_state.author_name}\n\n"
                    formatted_text += "="*50 + "\n\n"
                    
                    if st.session_state.include_toc:
                        formatted_text += "TABLE OF CONTENTS\n\n"
                        current_session = None
                        story_num = 1
                        
                        for story in stories:
                            session_id = story.get("session_id", "1")
                            if session_id != current_session:
                                session_title = story.get("session_title", f"Session {session_id}")
                                formatted_text += f"\n{session_title}\n"
                                current_session = session_id
                            question = story.get("question", f"Story {story_num}")
                            formatted_text += f"  {story_num}. {question}\n"
                            story_num += 1
                        formatted_text += "\n" + "="*50 + "\n\n"
                    
                    # Content
                    current_session = None
                    for i, story in enumerate(stories):
                        session_id = story.get("session_id", "1")
                        if session_id != current_session:
                            session_title = story.get("session_title", f"Session {session_id}")
                            formatted_text += f"\n\n{session_title.upper()}\n"
                            formatted_text += "-"*len(session_title) + "\n\n"
                            current_session = session_id
                        
                        question = story.get("question", f"Memory {i+1}")
                        answer = story.get("answer", "")
                        
                        if st.session_state.selected_format == "interview":
                            formatted_text += f"Q: {question}\n\n"
                            formatted_text += f"A: {answer}\n\n"
                        elif st.session_state.selected_format == "biography":
                            formatted_text += f"{answer}\n\n"
                        else:  # memoir
                            formatted_text += f"Chapter {i+1}: {question}\n\n"
                            formatted_text += f"{answer}\n\n"
                
                else:
                    # Format for dictionary structure
                    formatted_text += f"{st.session_state.book_title}\n"
                    formatted_text += f"by {st.session_state.author_name}\n\n"
                    formatted_text += "="*50 + "\n\n"
                    
                    if st.session_state.include_toc:
                        formatted_text += "TABLE OF CONTENTS\n\n"
                        for session_id, session_data in stories.items():
                            session_title = session_data.get("title", f"Session {session_id}")
                            formatted_text += f"\n{session_title}\n"
                            questions = session_data.get("questions", {})
                            for j, (question, _) in enumerate(questions.items(), 1):
                                formatted_text += f"  {j}. {question}\n"
                        formatted_text += "\n" + "="*50 + "\n\n"
                    
                    # Content
                    for session_id, session_data in stories.items():
                        session_title = session_data.get("title", f"Session {session_id}")
                        formatted_text += f"\n\n{session_title.upper()}\n"
                        formatted_text += "-"*len(session_title) + "\n\n"
                        
                        questions = session_data.get("questions", {})
                        for i, (question, answers) in enumerate(questions.items(), 1):
                            if isinstance(answers, list) and answers:
                                answer_text = answers[0].get("answer", "") if isinstance(answers[0], dict) else str(answers[0])
                            else:
                                answer_text = str(answers)
                            
                            if st.session_state.selected_format == "interview":
                                formatted_text += f"Q: {question}\n\n"
                                formatted_text += f"A: {answer_text}\n\n"
                            elif st.session_state.selected_format == "biography":
                                formatted_text += f"{answer_text}\n\n"
                            else:  # memoir
                                formatted_text += f"Chapter {i}: {question}\n\n"
                                formatted_text += f"{answer_text}\n\n"
                
                st.session_state.formatted_text = formatted_text
                st.success("Text formatted successfully!")
    
    with format_col2:
        if st.button("📊 Generate PDF", type="primary", use_container_width=True):
            st.warning("PDF generation requires reportlab library. Please install with: pip install reportlab")
    
    with format_col3:
        if st.button("📧 Share Link", type="secondary", use_container_width=True):
            # Create shareable link
            encoded_data = base64.b64encode(json.dumps(stories_data).encode()).decode()
            share_url = f"{st.query_params.get('app_url', st.experimental_get_query_params().get('app_url', [''])[0])}?data={encoded_data}"
            
            st.code(share_url, language="text")
            st.caption("Copy this URL to share your formatted biography")
    
    # Preview formatted text
    if st.session_state.formatted_text:
        with st.expander("📄 Formatted Text Preview", expanded=False):
            st.text_area("Preview", st.session_state.formatted_text, height=400)
            
            # Download text file
            text_filename = f"{st.session_state.book_title.replace(' ', '_')}_formatted.txt"
            st.download_button(
                label="📥 Download Text",
                data=st.session_state.formatted_text,
                file_name=text_filename,
                mime="text/plain",
                use_container_width=True
            )

else:
    # No data loaded yet
    st.info("📚 Welcome to the Biography Publisher!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### How to use:
        
        1. **Export from Tell My Story**  
           Click "Publish Biography" in the sidebar
        
        2. **Upload directly**  
           Use the file uploader in the sidebar
        
        3. **Share with others**  
           Send them the generated link
        
        ### Features:
        
        • Multiple format styles  
        • Professional PDF generation  
        • Customizable book details  
        • Table of contents  
        • Shareable links
        """)
    
    with col2:
        st.markdown("""
        ### Format Options:
        
        **📝 Interview Q&A**  
        Questions and answers format
        
        **📖 Continuous Biography**  
        Seamless narrative flow
        
        **📚 Chapter-based Memoir**  
        Organized by chapters
        
        ### Export Options:
        
        • Download as PDF  
        • Download as text  
        • Shareable URL  
        • Customizable styling
        """)

# Footer
st.markdown("---")
st.caption(f"Biography Publisher • {datetime.now().year} • Data format: List format compatible")

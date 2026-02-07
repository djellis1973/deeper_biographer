# biography_publisher.py - FIXED VERSION
import streamlit as st
import json
import base64
from datetime import datetime
import time
import tempfile
import os

# Try to import docx
try:
    from docx import Document
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# Page setup
st.set_page_config(page_title="Biography Publisher", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .main-title {
        text-align: center;
        color: #2c3e50;
        font-size: 3em;
        margin-bottom: 0.5em;
    }
    .subtitle {
        text-align: center;
        color: #7f8c8d;
        font-size: 1.2em;
        margin-bottom: 2em;
    }
</style>
""", unsafe_allow_html=True)

def show_celebration():
    """Show celebration effects"""
    st.balloons()
    st.markdown("""
    <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; color: white; margin: 2rem 0;">
        <h1 style="color: white; font-size: 2.5em;">🎉 Biography Created! 🎉</h1>
    </div>
    """, unsafe_allow_html=True)

def decode_stories_from_url():
    """Extract stories from URL parameter"""
    try:
        if hasattr(st, 'query_params'):
            query_params = st.query_params.to_dict()
            encoded_data = query_params.get("data")
            if isinstance(encoded_data, list):
                encoded_data = encoded_data[0]
        else:
            query_params = st.experimental_get_query_params()
            encoded_data = query_params.get("data", [None])[0]
        
        if not encoded_data:
            return None
            
        json_data = base64.b64decode(encoded_data).decode()
        stories_data = json.loads(json_data)
        return stories_data
    except Exception as e:
        return None

def create_beautiful_biography(stories_data):
    """Create a professionally formatted biography"""
    bio_text = ""
    
    user_profile = stories_data.get("user_profile", {})
    first_name = user_profile.get('first_name', '')
    last_name = user_profile.get('last_name', '')
    display_name = f"{first_name} {last_name}".strip() or stories_data.get("user", "Unknown")
    
    stories_dict = stories_data.get("stories", {})
    
    if not stories_dict:
        return "No stories found.", [], display_name, 0, 0, 0
    
    images_data = []
    if "images" in stories_data:
        images_data = stories_data.get("images", [])
    
    all_stories = []
    try:
        sorted_sessions = sorted(stories_dict.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0)
    except:
        sorted_sessions = stories_dict.items()
    
    for session_id, session_data in sorted_sessions:
        session_title = session_data.get("title", f"Chapter {session_id}")
        
        for question, answer_data in session_data.get("questions", {}).items():
            if isinstance(answer_data, dict):
                answer = answer_data.get("answer", "")
            else:
                answer = str(answer_data)
                
            if answer.strip():
                all_stories.append({
                    "session": session_title,
                    "question": question,
                    "answer": answer,
                    "session_id": session_id
                })
    
    if not all_stories:
        return "No stories found.", [], display_name, 0, 0, 0
    
    # ========== CREATE BIOGRAPHY ==========
    bio_text = "=" * 70 + "\n"
    bio_text += f"{'TELL MY STORY':^70}\n"
    bio_text += f"{'A PERSONAL BIOGRAPHY':^70}\n"
    bio_text += "=" * 70 + "\n\n"
    
    bio_text += f"THE LIFE STORY OF\n{display_name.upper()}\n\n"
    bio_text += "-" * 70 + "\n\n"
    
    # Personal Information
    if user_profile:
        bio_text += "PERSONAL INFORMATION\n"
        bio_text += "-" * 40 + "\n"
        if user_profile.get('birthdate'):
            bio_text += f"Date of Birth: {user_profile.get('birthdate')}\n"
        if user_profile.get('gender'):
            bio_text += f"Gender: {user_profile.get('gender')}\n"
        bio_text += "\n"
    
    # PHOTO STORIES SECTION
    if images_data:
        bio_text += "PHOTO STORIES\n"
        bio_text += "-" * 40 + "\n"
        
        images_by_session = {}
        for img in images_data:
            session_id = str(img.get("session_id", "0"))
            images_by_session.setdefault(session_id, []).append(img)
        
        for session_id, images in images_by_session.items():
            session_title = f"Session {session_id}"
            for story in all_stories:
                if str(story.get("session_id")) == session_id:
                    session_title = story["session"]
                    break
            
            bio_text += f"\n{session_title}:\n"
            for img in images:
                bio_text += f"  • {img.get('original_filename', 'Photo')}"
                if img.get('story'):
                    bio_text += f": {img.get('story')}"
                bio_text += "\n"
        
        bio_text += "\n"
    
    # Table of Contents
    bio_text += "TABLE OF CONTENTS\n"
    bio_text += "-" * 40 + "\n\n"
    
    current_session = None
    chapter_num = 0
    for story in all_stories:
        if story["session"] != current_session:
            chapter_num += 1
            bio_text += f"Chapter {chapter_num}: {story['session']}\n"
            current_session = story["session"]
    
    bio_text += "\n" + "=" * 70 + "\n\n"
    
    # Introduction
    bio_text += "INTRODUCTION\n\n"
    bio_text += f"This biography captures the life journey of {display_name}.\n\n"
    
    bio_text += "=" * 70 + "\n\n"
    
    # Chapters with stories
    current_session = None
    chapter_num = 0
    story_num = 0
    
    for story in all_stories:
        if story["session"] != current_session:
            chapter_num += 1
            bio_text += "\n" + "=" * 70 + "\n"
            bio_text += f"CHAPTER {chapter_num}: {story['session'].upper()}\n"
            bio_text += "=" * 70 + "\n\n"
            current_session = story["session"]
        
        story_num += 1
        bio_text += f"Story {story_num}: {story['question']}\n"
        bio_text += "-" * 40 + "\n"
        
        answer = story['answer'].strip()
        paragraphs = answer.split('\n')
        
        for para in paragraphs:
            if para.strip():
                bio_text += f"{para.strip()}\n\n"
        
        bio_text += "\n"
    
    # Statistics
    bio_text += "=" * 70 + "\n\n"
    bio_text += "BIOGRAPHY STATISTICS\n"
    bio_text += "-" * 40 + "\n"
    bio_text += f"• Total Stories: {story_num}\n"
    bio_text += f"• Total Chapters: {chapter_num}\n"
    
    total_words = sum(len(story['answer'].split()) for story in all_stories)
    bio_text += f"• Total Words: {total_words:,}\n"
    
    if images_data:
        bio_text += f"• Photo Stories: {len(images_data)}\n"
    
    bio_text += f"• Compiled: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n"
    bio_text += "-" * 70 + "\n\n"
    
    bio_text += "Created with Tell My Story Biographer.\n\n"
    bio_text += "=" * 70
    
    return bio_text, all_stories, display_name, story_num, chapter_num, total_words

def create_docx_biography(stories_data):
    """Create a DOCX version - FIXED STYLE ERROR"""
    if not DOCX_AVAILABLE:
        return None, "DOCX export not available"
    
    bio_text, all_stories, author_name, story_num, chapter_num, total_words = create_beautiful_biography(stories_data)
    
    doc = Document()
    
    # Title
    title = doc.add_heading(f"{author_name}'s Biography", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Subtitle
    subtitle = doc.add_paragraph(f"Created on {datetime.now().strftime('%B %d, %Y')}")
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_page_break()
    
    # Add chapters
    chapters = {}
    for story in all_stories:
        chapter_title = story['session']
        if chapter_title not in chapters:
            chapters[chapter_title] = []
        chapters[chapter_title].append(story)
    
    for i, (chapter_title, stories) in enumerate(chapters.items(), 1):
        doc.add_heading(f"Chapter {i}: {chapter_title}", level=1)
        
        for j, story in enumerate(stories, 1):
            doc.add_heading(f"Story {j}: {story['question']}", level=2)
            
            for paragraph in story['answer'].split('\n'):
                if paragraph.strip():
                    p = doc.add_paragraph(paragraph.strip())
                    p.paragraph_format.space_after = Pt(12)
            
            doc.add_paragraph()
    
    # Add photo stories
    images_data = stories_data.get("images", [])
    if images_data:
        doc.add_page_break()
        doc.add_heading('Photo Stories', level=1)
        
        images_by_session = {}
        for img in images_data:
            session_id = str(img.get("session_id", "0"))
            images_by_session.setdefault(session_id, []).append(img)
        
        for session_id, images in images_by_session.items():
            session_title = f"Session {session_id}"
            for story in all_stories:
                if str(story.get("session_id")) == session_id:
                    session_title = story['session']
                    break
            
            doc.add_heading(session_title, level=2)
            
            for img in images:
                item = doc.add_paragraph()
                runner = item.add_run(f"• {img.get('original_filename', 'Photo')}: ")
                runner.bold = True
                
                if img.get('story'):
                    item.add_run(img.get('story'))
    
    # Save to temp file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
    doc.save(temp_file.name)
    
    with open(temp_file.name, 'rb') as f:
        docx_content = f.read()
    
    os.unlink(temp_file.name)
    
    return docx_content, author_name

# ============================================================================
# MAIN APP
# ============================================================================

st.markdown('<h1 class="main-title">📖 Biography Creator</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Create your biography from stories</p>', unsafe_allow_html=True)

stories_data = decode_stories_from_url()

if stories_data:
    user_profile = stories_data.get("user_profile", {})
    images_data = stories_data.get("images", [])
    
    story_count = 0
    for session_id, session_data in stories_data.get("stories", {}).items():
        story_count += len(session_data.get("questions", {}))
    
    if story_count > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            if user_profile and user_profile.get('first_name'):
                st.success(f"✅ **{user_profile.get('first_name')} {user_profile.get('last_name', '')}**")
        
        with col2:
            st.metric("Total Stories", story_count)
        
        if images_data:
            st.info(f"📷 Includes {len(images_data)} photo stories")
        
        if st.button("✨ Create Biography", type="primary", use_container_width=True):
            with st.spinner("Creating..."):
                bio_text, all_stories, author_name, story_num, chapter_num, total_words = create_beautiful_biography(stories_data)
                
                show_celebration()
                
                st.subheader("📖 Biography Preview")
                
                col_preview1, col_preview2 = st.columns([2, 1])
                
                with col_preview1:
                    preview_text = bio_text[:1000] + "..." if len(bio_text) > 1000 else bio_text
                    st.text(preview_text)
                
                with col_preview2:
                    st.metric("Chapters", chapter_num)
                    st.metric("Stories", story_num)
                    st.metric("Words", f"{total_words:,}")
                    if images_data:
                        st.metric("Photo Stories", len(images_data))
                
                st.subheader("📥 Download")
                
                safe_name = author_name.replace(" ", "_")
                
                col_dl1, col_dl2, col_dl3 = st.columns(3)
                
                with col_dl1:
                    st.download_button(
                        label="📄 Text",
                        data=bio_text,
                        file_name=f"{safe_name}_Biography.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                
                with col_dl2:
                    if DOCX_AVAILABLE:
                        docx_content, _ = create_docx_biography(stories_data)
                        if docx_content:
                            st.download_button(
                                label="📝 DOCX",
                                data=docx_content,
                                file_name=f"{safe_name}_Biography.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True
                            )
                    else:
                        st.button(
                            "📝 DOCX (Install python-docx)",
                            disabled=True,
                            use_container_width=True
                        )
                
                with col_dl3:
                    json_data = json.dumps(stories_data, indent=2)
                    st.download_button(
                        label="📊 JSON",
                        data=json_data,
                        file_name=f"{safe_name}_Data.json",
                        mime="application/json",
                        use_container_width=True
                    )
                
                st.success(f"✅ Biography created with {story_num} stories!")
    
    else:
        st.warning("No stories found.")
        
else:
    st.info("Load stories from the main app or upload JSON:")
    
    uploaded_file = st.file_uploader("Upload JSON", type=['json'])
    if uploaded_file:
        try:
            uploaded_data = json.load(uploaded_file)
            story_count = sum(len(session.get("questions", {})) for session in uploaded_data.get("stories", {}).values())
            st.success(f"✅ Loaded {story_count} stories")
            
            if st.button("Create Biography", type="primary"):
                bio_text, all_stories, author_name, story_num, chapter_num, total_words = create_beautiful_biography(uploaded_data)
                
                safe_name = author_name.replace(" ", "_")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📄 Text",
                        data=bio_text,
                        file_name=f"{safe_name}_Biography.txt",
                        mime="text/plain"
                    )
                with col2:
                    if DOCX_AVAILABLE:
                        docx_content, _ = create_docx_biography(uploaded_data)
                        if docx_content:
                            st.download_button(
                                label="📝 DOCX",
                                data=docx_content,
                                file_name=f"{safe_name}_Biography.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                
                st.success(f"Biography created!")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")

st.markdown("---")
st.caption("Tell My Story Biography Publisher")

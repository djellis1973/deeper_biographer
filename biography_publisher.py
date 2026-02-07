# biography_publisher.py - COMPLETE WORKING VERSION WITH DOCX
import streamlit as st
import json
import base64
from datetime import datetime
import time
import tempfile
import os

# Try to import docx, but handle if it's not installed
try:
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.style import WD_STYLE_TYPE
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    st.warning("⚠️ DOCX export not available. Please install 'python-docx' package.")

# Page setup
st.set_page_config(page_title="Biography Publisher", layout="wide")
st.title("📖 Beautiful Biography Creator")

# Custom CSS for better styling
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
    .story-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #3498db;
    }
    .download-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 8px;
        font-size: 1.1em;
        font-weight: 600;
        cursor: pointer;
        width: 100%;
        margin-top: 1rem;
        transition: transform 0.2s;
    }
    .download-btn:hover {
        transform: translateY(-2px);
    }
    .stats-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        border-top: 4px solid #2ecc71;
    }
    .preview-box {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px dashed #dee2e6;
        font-family: 'Courier New', monospace;
        font-size: 0.9em;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

def show_celebration():
    """Show celebration effects"""
    # Balloons
    st.balloons()
    
    # Success message
    st.markdown("""
    <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; color: white; margin: 2rem 0;">
        <h1 style="color: white; font-size: 2.5em;">🎉 Biography Created! 🎉</h1>
        <p style="font-size: 1.2em;">Your beautiful life story is ready to share!</p>
    </div>
    """, unsafe_allow_html=True)

def decode_stories_from_url():
    """Extract stories from URL parameter"""
    try:
        # Try new method first (Streamlit 1.28+)
        if hasattr(st, 'query_params'):
            query_params = st.query_params.to_dict()
            encoded_data = query_params.get("data")
            
            if isinstance(encoded_data, list):
                encoded_data = encoded_data[0]
        else:
            # Fall back to experimental method
            query_params = st.experimental_get_query_params()
            encoded_data = query_params.get("data", [None])[0]
        
        if not encoded_data:
            return None
            
        # Decode the data
        json_data = base64.b64decode(encoded_data).decode()
        stories_data = json.loads(json_data)
        
        return stories_data
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

def create_beautiful_biography(stories_data):
    """Create a professionally formatted biography"""
    # Initialize bio_text at the VERY BEGINNING
    bio_text = ""
    
    # Get user info FIRST
    user_profile = stories_data.get("user_profile", {})
    
    # Get display name
    if user_profile and 'first_name' in user_profile:
        first_name = user_profile.get('first_name', '')
        last_name = user_profile.get('last_name', '')
        display_name = f"{first_name} {last_name}".strip()
    else:
        display_name = stories_data.get("user", "Unknown")
    
    # Get stories
    stories_dict = stories_data.get("stories", {})
    
    if not stories_dict:
        return "No stories found to publish.", [], display_name, 0, 0, 0
    
    # Try multiple possible locations for the image data
    images_data = []
    if "images" in stories_data:
        images_data = stories_data.get("images", [])
    elif "summary" in stories_data and "images" in stories_data["summary"]:
        images_data = stories_data["summary"].get("images", [])
    
    # Collect all stories
    all_stories = []
    try:
        # Sort sessions numerically
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
                    "date": answer_data.get("timestamp", datetime.now().isoformat())[:10] 
                             if isinstance(answer_data, dict) else datetime.now().isoformat()[:10],
                    "session_id": session_id
                })
    
    if not all_stories:
        return "No stories found to publish.", [], display_name, 0, 0, 0
    
    # ========== CREATE BEAUTIFUL BIOGRAPHY ==========
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
    
    # Image References (if available)
    if images_data:
        bio_text += "PHOTO REFERENCES\n"
        bio_text += "-" * 40 + "\n"
        
        # Group images by session
        images_by_session = {}
        for img in images_data:
            session_id = str(img.get("session_id", "0"))
            images_by_session.setdefault(session_id, []).append(img)
        
        # Add image references by session
        for session_id, images in images_by_session.items():
            session_title = "Unknown Session"
            for story in all_stories:
                if str(story.get("session_id")) == session_id:
                    session_title = story["session"]
                    break
            
            bio_text += f"\n{session_title}:\n"
            for img in images:
                bio_text += f"  • {img.get('original_filename', 'Photo')}"
                if img.get('description'):
                    bio_text += f": {img.get('description')}"
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
    bio_text += f"This biography captures the unique life journey of {display_name}, "
    bio_text += f"compiled from personal reflections shared on {datetime.now().strftime('%B %d, %Y')}. "
    bio_text += "Each chapter represents a different phase of life, preserved here for future generations.\n\n"
    
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
        bio_text += f"Story {story_num}\n"
        bio_text += f"Topic: {story['question']}\n"
        
        if story['date']:
            bio_text += f"Recorded: {story['date']}\n"
        
        bio_text += "-" * 40 + "\n"
        
        # Format the answer with proper paragraphs
        answer = story['answer'].strip()
        paragraphs = answer.split('\n')
        
        for para in paragraphs:
            if para.strip():
                bio_text += f"{para.strip()}\n\n"
        
        bio_text += "\n"
    
    # Conclusion
    bio_text += "=" * 70 + "\n\n"
    bio_text += "CONCLUSION\n\n"
    bio_text += f"This collection contains {story_num} stories across {chapter_num} chapters, "
    bio_text += f"each one a piece of {display_name}'s unique mosaic of memories. "
    bio_text += "These reflections will continue to resonate long into the future.\n\n"
    
    # Statistics
    bio_text += "-" * 70 + "\n"
    bio_text += "BIOGRAPHY STATISTICS\n"
    bio_text += "-" * 40 + "\n"
    bio_text += f"• Total Stories: {story_num}\n"
    bio_text += f"• Total Chapters: {chapter_num}\n"
    
    # Calculate word count
    total_words = sum(len(story['answer'].split()) for story in all_stories)
    bio_text += f"• Total Words: {total_words:,}\n"
    
    # Add image count if available
    if images_data:
        bio_text += f"• Photo References: {len(images_data)}\n"
    
    # Find longest story
    if all_stories:
        longest = max(all_stories, key=lambda x: len(x['answer'].split()))
        bio_text += f"• Longest Story: \"{longest['question'][:50]}...\" ({len(longest['answer'].split())} words)\n"
    
    bio_text += f"• Compiled: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n"
    bio_text += "-" * 70 + "\n\n"
    
    # Final note
    bio_text += "This digital legacy was created with Tell My Story Biographer.\n\n"
    bio_text += "=" * 70
    
    return bio_text, all_stories, display_name, story_num, chapter_num, total_words

def create_html_biography(stories_data):
    """Create an HTML version with beautiful formatting"""
    bio_text, all_stories, display_name, story_num, chapter_num, total_words = create_beautiful_biography(stories_data)
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{display_name}'s Biography</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Crimson+Text:ital,wght@0,400;0,600;0,700;1,400&family=Open+Sans:wght@300;400;600&display=swap');
        
        body {{
            font-family: 'Crimson Text', serif;
            line-height: 1.8;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #fefefe;
        }}
        .header {{
            text-align: center;
            padding: 40px 0;
            border-bottom: 3px double #2c5282;
            margin-bottom: 40px;
        }}
        h1 {{
            font-size: 2.8em;
            color: #2c5282;
            margin-bottom: 10px;
        }}
        .subtitle {{
            font-family: 'Open Sans', sans-serif;
            font-size: 1.2em;
            color: #666;
        }}
        .chapter {{
            margin: 50px 0;
        }}
        .chapter-title {{
            color: #2c5282;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        .story {{
            margin: 30px 0;
            padding: 25px;
            background: #f8fafc;
            border-radius: 8px;
            border-left: 4px solid #4299e1;
        }}
        .question {{
            font-weight: 700;
            color: #2d3748;
            margin-bottom: 15px;
            font-size: 1.2em;
        }}
        .answer {{
            white-space: pre-line;
            font-size: 1.1em;
        }}
        .stats {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            margin: 40px 0;
        }}
        .stat-item {{
            display: inline-block;
            margin: 0 20px;
        }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: 700;
            display: block;
        }}
        .footer {{
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #e2e8f0;
            color: #718096;
        }}
        @media print {{
            body {{ padding: 0; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{display_name}'s Life Story</h1>
        <div class="subtitle">A Personal Biography • {datetime.now().strftime('%B %d, %Y')}</div>
    </div>
    
    <div class="stats">
        <div class="stat-item">
            <span class="stat-number">{chapter_num}</span>
            <span>Chapters</span>
        </div>
        <div class="stat-item">
            <span class="stat-number">{story_num}</span>
            <span>Stories</span>
        </div>
        <div class="stat-item">
            <span class="stat-number">{total_words:,}</span>
            <span>Words</span>
        </div>
    </div>
    
    <div class="content">
'''

    # Add chapters
    current_session = None
    chapter_num = 0
    
    for story in all_stories:
        if story["session"] != current_session:
            chapter_num += 1
            current_session = story["session"]
            html += f'''
            <div class="chapter">
                <h2 class="chapter-title">Chapter {chapter_num}: {story['session']}</h2>
            '''
        
        html += f'''
        <div class="story">
            <div class="question">✏️ {story['question']}</div>
            <div class="answer">{story['answer']}</div>
        '''
        
        if story['date']:
            html += f'''
            <div style="margin-top: 15px; font-size: 0.9em; color: #718096;">
                Recorded: {story['date']}
            </div>
            '''
        
        html += '</div>'
        
        # Close chapter if next story is different session or last story
        next_idx = all_stories.index(story) + 1
        if next_idx >= len(all_stories) or all_stories[next_idx]["session"] != current_session:
            html += '</div>'

    html += f'''
    </div>
    
    <div class="footer">
        <p>Created with Tell My Story Biographer</p>
        <p>{datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
    </div>
    
    <div class="no-print" style="text-align: center; margin-top: 40px;">
        <button onclick="window.print()" style="
            background: #48bb78;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 1.1em;
            cursor: pointer;
            margin: 20px;
        ">
            🖨️ Print This Biography
        </button>
    </div>
</body>
</html>'''
    
    return html, display_name

def create_docx_biography(stories_data):
    """Create a DOCX version of the biography"""
    if not DOCX_AVAILABLE:
        return None, "DOCX export not available"
    
    # Get the text biography first
    bio_text, all_stories, author_name, story_num, chapter_num, total_words = create_beautiful_biography(stories_data)
    
    # Create a new Document
    doc = Document()
    
    # Add a title
    title = doc.add_heading(f"{author_name}'s Biography", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Add subtitle
    subtitle = doc.add_paragraph(f"Created on {datetime.now().strftime('%B %d, %Y')}")
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_page_break()
    
    # Add table of contents
    doc.add_heading('Table of Contents', level=1)
    
    # Group stories by session/chapter
    chapters = {}
    for story in all_stories:
        chapter_title = story['session']
        if chapter_title not in chapters:
            chapters[chapter_title] = []
        chapters[chapter_title].append(story)
    
    # Add chapter headings to TOC
    for i, (chapter_title, stories) in enumerate(chapters.items(), 1):
        doc.add_paragraph(f"Chapter {i}: {chapter_title}")
    
    doc.add_page_break()
    
    # Add each chapter
    for i, (chapter_title, stories) in enumerate(chapters.items(), 1):
        doc.add_heading(f"Chapter {i}: {chapter_title}", level=1)
        
        for j, story in enumerate(stories, 1):
            doc.add_heading(f"Story {j}: {story['question']}", level=2)
            
            # Add the story text
            for paragraph in story['answer'].split('\n'):
                if paragraph.strip():
                    p = doc.add_paragraph(paragraph.strip())
                    p.paragraph_format.space_after = Pt(12)
            
            # Add story date if available
            if story.get('date'):
                date_para = doc.add_paragraph(f"Recorded: {story['date']}")
                date_para.style = 'Emphasis'
            
            doc.add_paragraph()  # Add space between stories
    
    # Add image references if available
    images_data = stories_data.get("images", [])
    if images_data:
        doc.add_page_break()
        doc.add_heading('Photo References', level=1)
        
        # Group images by session
        images_by_session = {}
        for img in images_data:
            session_id = str(img.get("session_id", "0"))
            images_by_session.setdefault(session_id, []).append(img)
        
        # Add image references
        for session_id, images in images_by_session.items():
            # Find session title
            session_title = f"Session {session_id}"
            for story in all_stories:
                if str(story.get("session_id")) == session_id:
                    session_title = story['session']
                    break
            
            doc.add_heading(session_title, level=2)
            
            for img in images:
                item = doc.add_paragraph(style='List Bullet')
                runner = item.add_run(f"{img.get('original_filename', 'Photo')}")
                runner.bold = True
                
                if img.get('description'):
                    item.add_run(f": {img.get('description')}")
    
    # Add statistics page
    doc.add_page_break()
    doc.add_heading('Biography Statistics', level=1)
    
    stats = doc.add_table(rows=5, cols=2)
    stats.style = 'Light Grid'
    
    # Fill the table
    cells = [
        ["Total Stories:", str(story_num)],
        ["Total Chapters:", str(chapter_num)],
        ["Total Words:", f"{total_words:,}"],
        ["Photo References:", str(len(images_data)) if images_data else "0"],
        ["Compiled on:", datetime.now().strftime('%B %d, %Y at %I:%M %p')]
    ]
    
    for i, row in enumerate(stats.rows):
        for j, cell in enumerate(row.cells):
            cell.text = cells[i][j]
    
    # Save to a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
    doc.save(temp_file.name)
    
    # Read the file content
    with open(temp_file.name, 'rb') as f:
        docx_content = f.read()
    
    # Clean up
    os.unlink(temp_file.name)
    
    return docx_content, author_name

# ============================================================================
# MAIN APP INTERFACE
# ============================================================================

st.markdown('<h1 class="main-title">📖 Beautiful Biography Creator</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Transform your life stories into a professionally formatted book</p>', unsafe_allow_html=True)

# Try to get data from URL first
stories_data = decode_stories_from_url()

if stories_data:
    # Auto-process data from URL
    user_name = stories_data.get("user", "Unknown")
    user_profile = stories_data.get("user_profile", {})
    summary = stories_data.get("summary", {})
    images_data = stories_data.get("images", [])
    
    # Count stories
    story_count = 0
    for session_id, session_data in stories_data.get("stories", {}).items():
        story_count += len(session_data.get("questions", {}))
    
    if story_count > 0:
        # Display user info
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if user_profile and user_profile.get('first_name'):
                st.success(f"✅ Welcome, **{user_profile.get('first_name')} {user_profile.get('last_name', '')}**!")
            else:
                st.success(f"✅ Welcome, **{user_name}**!")
        
        with col2:
            st.metric("Total Sessions", len(stories_data.get("stories", {})))
        
        with col3:
            st.metric("Total Stories", story_count)
        
        # Show image count if available
        if images_data:
            st.info(f"📷 Includes {len(images_data)} photo references")
        
        # Generate biography button
        if st.button("✨ Create Beautiful Biography", type="primary", use_container_width=True):
            with st.spinner("🖋️ Crafting your beautiful biography..."):
                time.sleep(1)
                
                # Create text version
                bio_text, all_stories, author_name, story_num, chapter_num, total_words = create_beautiful_biography(stories_data)
                
                # Create HTML version
                html_bio, html_name = create_html_biography(stories_data)
            
            # Show celebration
            show_celebration()
            
            # Show preview
            st.subheader("📖 Your Biography Preview")
            
            col_preview1, col_preview2 = st.columns([2, 1])
            
            with col_preview1:
                st.markdown('<div class="preview-box">', unsafe_allow_html=True)
                preview_text = bio_text[:1500] + "..." if len(bio_text) > 1500 else bio_text
                st.text(preview_text)
                st.markdown('</div>', unsafe_allow_html=True)
                st.caption(f"Preview of {len(preview_text):,} characters out of {len(bio_text):,} total")
            
            with col_preview2:
                st.markdown('<div class="stats-card">', unsafe_allow_html=True)
                st.metric("📚 Chapters", chapter_num)
                st.metric("📝 Stories", story_num)
                st.metric("📊 Total Words", f"{total_words:,}")
                st.metric("📏 Biography Size", f"{len(bio_text):,} chars")
                if images_data:
                    st.metric("📷 Photo References", len(images_data))
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Download options
            st.subheader("📥 Download Your Biography")
            
            col_dl1, col_dl2, col_dl3 = st.columns(3)
            
            with col_dl1:
                safe_name = author_name.replace(" ", "_")
                st.download_button(
                    label="📄 Text Version",
                    data=bio_text,
                    file_name=f"{safe_name}_Biography.txt",
                    mime="text/plain",
                    use_container_width=True,
                    type="primary"
                )
                st.caption("Plain text format")
            
            with col_dl2:
                st.download_button(
                    label="🌐 HTML Version",
                    data=html_bio,
                    file_name=f"{safe_name}_Biography.html",
                    mime="text/html",
                    use_container_width=True,
                    type="secondary"
                )
                st.caption("Web format - ready to print")
            
            with col_dl3:
                if DOCX_AVAILABLE:
                    docx_content, _ = create_docx_biography(stories_data)
                    if docx_content:
                        st.download_button(
                            label="📝 DOCX Version",
                            data=docx_content,
                            file_name=f"{safe_name}_Biography.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True,
                            type="secondary"
                        )
                        st.caption("Microsoft Word format")
                else:
                    st.button(
                        "📝 DOCX (Not Available)",
                        disabled=True,
                        use_container_width=True,
                        help="Install 'python-docx' package to enable DOCX export"
                    )
                    st.caption("Requires python-docx package")
            
            # Additional download options
            st.markdown("---")
            col_md, col_json = st.columns(2)
            
            with col_md:
                # Markdown version
                md_bio = bio_text.replace("=" * 70, "#" * 3)
                st.download_button(
                    label="📋 Markdown",
                    data=md_bio,
                    file_name=f"{safe_name}_Biography.md",
                    mime="text/markdown",
                    use_container_width=True
                )
                st.caption("For easy editing")
            
            with col_json:
                # JSON export
                json_data = json.dumps(stories_data, indent=2)
                st.download_button(
                    label="📊 JSON Data",
                    data=json_data,
                    file_name=f"{safe_name}_Stories.json",
                    mime="application/json",
                    use_container_width=True
                )
                st.caption("Complete data backup")
            
            st.success(f"✨ Biography created! **{story_num} stories** across **{chapter_num} chapters** ({total_words:,} words)")
    
    else:
        st.warning("Found your profile but no stories yet.")
        st.info("Go back to the main app and save some stories first!")
        
else:
    # Manual upload option
    st.info("📋 **How to create your biography:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🚀 **Automatic Method**
        1. Go to your Tell My Story app
        2. Answer questions and save your responses
        3. Click the **Publish Biography** button
        4. Your stories will automatically appear here
        """)
    
    with col2:
        st.markdown("""
        ### 📤 **Manual Upload**
        If you have exported your stories as JSON:
        1. Download the JSON file from the main app
        2. Upload it here:
        """)
        
        uploaded_file = st.file_uploader("Choose a JSON file", type=['json'], label_visibility="collapsed")
        if uploaded_file:
            try:
                uploaded_data = json.load(uploaded_file)
                story_count = sum(len(session.get("questions", {})) for session in uploaded_data.get("stories", {}).values())
                st.success(f"✅ Loaded {story_count} stories")
                
                if st.button("Create Biography from File", type="primary", use_container_width=True):
                    bio_text, all_stories, author_name, story_num, chapter_num, total_words = create_beautiful_biography(uploaded_data)
                    
                    safe_name = author_name.replace(" ", "_")
                    
                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        st.download_button(
                            label="📥 Download Text",
                            data=bio_text,
                            file_name=f"{safe_name}_Biography.txt",
                            mime="text/plain"
                        )
                    with col_dl2:
                        html_bio, _ = create_html_biography(uploaded_data)
                        st.download_button(
                            label="🌐 Download HTML",
                            data=html_bio,
                            file_name=f"{safe_name}_Biography.html",
                            mime="text/html"
                        )
                    
                    show_celebration()
                    st.success(f"Biography created for {author_name}!")
                    
            except Exception as e:
                st.error(f"❌ Error processing file: {str(e)}")

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.caption("✨ **Tell My Story Biography Publisher** • Create beautiful books from your life stories • Professional formatting • Celebration effects included")

# biography_publisher.py - BEAUTIFUL BIOGRAPHY PUBLISHER
import streamlit as st
import json
import base64
from datetime import datetime

# Page setup
st.set_page_config(page_title="Biography Publisher", layout="wide")
st.title("📖 Beautiful Biography Creator")

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

def create_beautiful_biography(stories_data):
    """Create a professionally formatted biography"""
    user_name = stories_data.get("user", "Unknown")
    stories_dict = stories_data.get("stories", {})
    
    # Collect all stories
    all_stories = []
    for session_id, session_data in sorted(stories_dict.items()):
        session_title = session_data.get("title", f"Chapter {session_id}")
        
        for question, answer_data in session_data.get("questions", {}).items():
            answer = answer_data.get("answer", "")
            if answer.strip():  # Only include non-empty answers
                all_stories.append({
                    "session": session_title,
                    "question": question,
                    "answer": answer,
                    "date": answer_data.get("timestamp", "")[:10]
                })
    
    if not all_stories:
        return "No stories found to publish.", [], user_name, 0, 0, 0
    
    # ========== CREATE BEAUTIFUL BIOGRAPHY ==========
    bio_text = "=" * 60 + "\n"
    bio_text += f"{'THE LIFE STORY OF':^60}\n"
    bio_text += f"{user_name.upper():^60}\n"
    bio_text += "=" * 60 + "\n\n"
    
    # Table of Contents
    bio_text += "TABLE OF CONTENTS\n"
    bio_text += "-" * 40 + "\n"
    
    current_session = None
    chapter_num = 0
    for i, story in enumerate(all_stories):
        if story["session"] != current_session:
            chapter_num += 1
            bio_text += f"\nChapter {chapter_num}: {story['session']}\n"
            current_session = story["session"]
    
    bio_text += "\n" + "=" * 60 + "\n\n"
    
    # Introduction
    bio_text += "FOREWORD\n\n"
    bio_text += f"This biography captures the unique life journey of {user_name}, "
    bio_text += f"compiled from personal reflections shared on {datetime.now().strftime('%B %d, %Y')}. "
    bio_text += "Each chapter represents a different phase of life, preserved here for future generations.\n\n"
    
    bio_text += "=" * 60 + "\n\n"
    
    # Chapters with stories
    current_session = None
    chapter_num = 0
    story_num = 0
    
    for story in all_stories:
        if story["session"] != current_session:
            chapter_num += 1
            bio_text += "\n" + "-" * 60 + "\n"
            bio_text += f"CHAPTER {chapter_num}\n"
            bio_text += f"{story['session'].upper()}\n"
            bio_text += "-" * 60 + "\n\n"
            current_session = story["session"]
        
        story_num += 1
        bio_text += f"STORY {story_num}\n"
        bio_text += f"Topic: {story['question']}\n"
        
        if story['date']:
            bio_text += f"Date Recorded: {story['date']}\n"
        
        bio_text += "-" * 40 + "\n"
        
        # Format the answer with proper paragraphs
        answer = story['answer'].strip()
        paragraphs = answer.split('\n')
        
        for para in paragraphs:
            if para.strip():
                # Add proper indentation for paragraphs
                bio_text += f"  {para.strip()}\n\n"
        
        bio_text += "\n"
    
    # Conclusion
    bio_text += "=" * 60 + "\n\n"
    bio_text += "EPILOGUE\n\n"
    bio_text += f"This collection contains {story_num} stories across {chapter_num} chapters, "
    bio_text += f"each one a piece of {user_name}'s unique mosaic of memories. "
    bio_text += "Stories have the power to connect generations, and these reflections "
    bio_text += "will continue to resonate long into the future.\n\n"
    
    # Statistics
    bio_text += "-" * 60 + "\n"
    bio_text += "BIOGRAPHY STATISTICS\n"
    bio_text += f"• Total Stories: {story_num}\n"
    bio_text += f"• Chapters: {chapter_num}\n"
    
    # Calculate word count
    total_words = sum(len(story['answer'].split()) for story in all_stories)
    bio_text += f"• Total Words: {total_words:,}\n"
    
    # Find longest story
    if all_stories:
        longest = max(all_stories, key=lambda x: len(x['answer'].split()))
        bio_text += f"• Longest Story: \"{longest['question'][:50]}...\" ({len(longest['answer'].split())} words)\n"
    
    bio_text += f"• Compiled: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n"
    bio_text += "-" * 60 + "\n\n"
    
    # Final note
    bio_text += "This digital legacy was created with the DeepVault UK Legacy Builder, "
    bio_text += "preserving personal history for generations to come.\n\n"
    bio_text += "=" * 60
    
    return bio_text, all_stories, user_name, story_num, chapter_num, total_words

# ============================================================================
# MAIN APP INTERFACE
# ============================================================================
st.markdown("### 🎨 Create Your Beautiful Biography")

# Try to get data from URL first
stories_data = decode_stories_from_url()

if stories_data:
    # Auto-process data from URL
    user_name = stories_data.get("user", "Unknown")
    story_count = sum(len(session.get("questions", {})) for session in stories_data.get("stories", {}).values())
    
    if story_count > 0:
        st.success(f"✅ Welcome back, **{user_name}**! Found **{story_count} stories** ready to become your biography.")
        
        # Show formatting options
        st.markdown("### 🎯 Formatting Options")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            include_toc = st.checkbox("Table of Contents", value=True)
        with col2:
            include_stats = st.checkbox("Statistics Page", value=True)
        with col3:
            include_date = st.checkbox("Story Dates", value=True)
        
        # Generate biography button
        if st.button("✨ Create Beautiful Biography", type="primary", use_container_width=True):
            with st.spinner("Crafting your beautiful biography..."):
                biography, all_stories, author_name, story_num, chapter_num, total_words = create_beautiful_biography(stories_data)
            
            # Show preview
            st.subheader("📖 Your Biography Preview")
            
            # Display in columns for better layout
            col_preview1, col_preview2 = st.columns([2, 1])
            
            with col_preview1:
                # Show first 1000 characters as preview
                st.text_area("Preview (first 1000 characters):", 
                           biography[:1000] + "..." if len(biography) > 1000 else biography,
                           height=300)
            
            with col_preview2:
                st.metric("Total Stories", story_num)
                st.metric("Chapters", chapter_num)
                st.metric("Total Words", f"{total_words:,}")
                st.metric("Biography Size", f"{len(biography):,} chars")
            
            # Download options
            st.subheader("📥 Download Your Biography")
            
            col_dl1, col_dl2, col_dl3 = st.columns(3)
            
            with col_dl1:
                # Plain text version
                safe_name = author_name.replace(" ", "_")
                st.download_button(
                    label="📄 Download as Text",
                    data=biography,
                    file_name=f"{safe_name}_Biography.txt",
                    mime="text/plain",
                    type="primary",
                    use_container_width=True
                )
            
            with col_dl2:
                # Markdown version
                md_biography = biography.replace("=" * 60, "#" * 60)
                st.download_button(
                    label="📝 Download as Markdown",
                    data=md_biography,
                    file_name=f"{safe_name}_Biography.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            
            with col_dl3:
                # Simple HTML version
                html_biography = f"""<!DOCTYPE html>
<html>
<head>
    <title>{author_name}'s Biography</title>
    <style>
        body {{ font-family: Georgia, serif; line-height: 1.6; margin: 40px; }}
        h1 {{ text-align: center; border-bottom: 3px double #333; padding-bottom: 20px; }}
        .chapter {{ margin-top: 40px; border-top: 2px solid #333; padding-top: 20px; }}
        .story {{ margin: 20px 0; }}
        .question {{ font-weight: bold; color: #2c5282; }}
        .stats {{ background: #f8f9fa; padding: 20px; border-left: 4px solid #4a5568; margin: 30px 0; }}
    </style>
</head>
<body>
    <h1>{author_name}'s Life Story</h1>
    <pre>{biography}</pre>
</body>
</html>"""
                st.download_button(
                    label="🌐 Download as HTML",
                    data=html_biography,
                    file_name=f"{safe_name}_Biography.html",
                    mime="text/html",
                    use_container_width=True
                )
            
            st.balloons()
            st.success(f"✨ Biography created! **{story_num} stories** across **{chapter_num} chapters** ({total_words:,} words)")
            
            # Shareable link
            st.markdown("---")
            st.markdown("### 🔗 Share Your Achievement")
            st.code(f"I've created my life story biography with {story_num} stories! #LifeStory #Biography", language="markdown")
        
        # Story preview
        with st.expander("📋 Preview Your Stories", expanded=True):
            for session_id, session_data in stories_data.get("stories", {}).items():
                st.markdown(f"### {session_data.get('title', f'Chapter {session_id}')}")
                
                for question, answer_data in session_data.get("questions", {}).items():
                    answer = answer_data.get("answer", "")
                    if answer.strip():
                        word_count = len(answer.split())
                        st.markdown(f"**{question}**")
                        st.write(f"{answer[:200]}..." if len(answer) > 200 else answer)
                        st.caption(f"{word_count} words")
                        st.divider()
    else:
        st.warning(f"Found your profile (**{user_name}**) but no stories yet.")
        st.info("Go back to the main app and save some stories first!")
        
else:
    # Manual upload option
    st.info("📋 **How to create your biography:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🚀 **Automatic Method**
        1. Go to your main interview app
        2. Answer questions and save stories
        3. Click the **publisher link** at the bottom
        4. Your biography creates itself!
        """)
    
    with col2:
        st.markdown("""
        ### 📤 **Manual Upload**
        1. In main app, use **Export Current Progress**
        2. Download the JSON file
        3. Upload it here:
        """)
        
        uploaded_file = st.file_uploader("Upload stories JSON", type=['json'])
        if uploaded_file:
            try:
                uploaded_data = json.load(uploaded_file)
                st.success(f"✅ Loaded stories for **{uploaded_data.get('user', 'Unknown')}**")
                
                if st.button("Create Biography from File", type="primary"):
                    biography, all_stories, author_name, story_num, chapter_num, total_words = create_beautiful_biography(uploaded_data)
                    
                    safe_name = author_name.replace(" ", "_")
                    st.download_button(
                        label="📥 Download Your Biography",
                        data=biography,
                        file_name=f"{safe_name}_Biography.txt",
                        mime="text/plain"
                    )
            except:
                st.error("❌ Invalid file format.")

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.caption("✨ **Professional formatting** • Multiple download formats • Your story, beautifully preserved")

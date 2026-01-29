# Remove all FPDF related code and replace the export section with:

st.markdown("### 📤 Export Options")
export_format = st.radio("Format:", ["HTML", "Text", "JSON"], horizontal=True)

if st.button("📥 Export Now", use_container_width=True, type="primary"):
    with st.spinner(f"Creating {export_format} document..."):
        if export_format == "HTML":
            st.download_button(
                label="Download HTML",
                data=export_html(),
                file_name=f"LifeStory_{st.session_state.user_id}.html",
                mime="text/html",
                use_container_width=True
            )
        elif export_format == "Text":
            st.download_button(
                label="Download Text",
                data=export_text(),
                file_name=f"LifeStory_{st.session_state.user_id}.txt",
                mime="text/plain",
                use_container_width=True
            )
        else:  # JSON
            st.download_button(
                label="Download JSON",
                data=export_json(),
                file_name=f"LifeStory_{st.session_state.user_id}.json",
                mime="application/json",
                use_container_width=True
            )

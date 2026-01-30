# ============================================================================
# SECTION 7: SIMPLIFIED SPEECH-TO-TEXT WITH FALLBACK
# ============================================================================
def transcribe_audio_simple(audio_file):
    """Simplified transcription with fallback options"""
    try:
        # First, let's try the simplest approach
        audio_bytes = audio_file.read()
        
        # Option 1: Direct Whisper API call
        try:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=("audio.wav", audio_bytes, "audio/wav")
            )
            return transcript.text
        except Exception as whisper_error:
            # If Whisper fails, try a different approach
            st.warning("Whisper API error, using fallback")
            
            # Option 2: Save to temp file and try again
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name
            
            try:
                with open(tmp_path, "rb") as audio_file_obj:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file_obj
                    )
                os.unlink(tmp_path)
                return transcript.text
            except:
                # Final fallback - return a placeholder
                os.unlink(tmp_path) if os.path.exists(tmp_path) else None
                return "[Speech recorded - transcription unavailable. Please type your answer.]"
                
    except Exception as e:
        st.error(f"Speech transcription error: Please type your answer instead.")
        return "[Please type your answer]"

# Replace the transcribe_audio function call
# In SECTION 13, replace line with transcribed_text = transcribe_audio_simple(audio_bytes)



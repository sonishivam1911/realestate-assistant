import streamlit as st
from typing import Dict
import base64
import html


def display_email_section(email_data: Dict, reflection_result: Dict = None):
    """
    Display generated email with copy button in Streamlit
    
    Args:
        email_data: Dict with 'subject' and 'body'
        reflection_result: Optional reflection metrics
    """
    
    print(f"\n📧 DISPLAY EMAIL DEBUG:")
    print(f"   email_data type: {type(email_data)}")
    print(f"   email_data keys: {list(email_data.keys()) if isinstance(email_data, dict) else 'Not a dict'}")
    print(f"   email_data: {email_data}")
    
    if not email_data or not isinstance(email_data, dict):
        st.error(f"❌ Invalid email data: {type(email_data)}")
        if email_data:
            st.json(email_data)
        return
    
    if 'subject' not in email_data and 'body' not in email_data:
        st.warning("📧 No email data available")
        st.json(email_data)  # Show what we got
        return
    
    # Quality indicator if reflection result available
    if reflection_result:
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            score = reflection_result.get('final_quality_score', 0)
            ready = reflection_result.get('ready_to_send', False)
            
            if ready:
                st.markdown(f"**Quality Score: {score}/10** ✅ Ready to send")
            else:
                st.markdown(f"**Quality Score: {score}/10** ⚠️ Review recommended")
        
        with col2:
            iterations = reflection_result.get('reflection_iterations', 0)
            st.markdown(f"**Refinements:** {iterations} iteration(s)")
        
        with col3:
            if reflection_result.get('reflection_notes'):
                st.info(f"💡 Improvements: Check reflection notes below")
    
    st.divider()
    
    # Email container with tabs
    tab1, tab2, tab3 = st.tabs(["📨 Email Preview", "✏️ Edit Email", "📋 Copy Email"])
    
    with tab1:
        # Display email in a nice format
        subject = email_data.get('subject', 'N/A')
        body = email_data.get('body', 'N/A')
        
        print(f"   Subject: {subject}")
        print(f"   Body length: {len(str(body)) if body else 0}")
        
        st.markdown("### Subject")
        st.write(subject)
        
        st.markdown("### Body")
        st.write(body)
        
        # Also show in a text area for better readability
        st.text_area(
            "Email Body (Full Text):",
            value=str(body),
            height=300,
            disabled=True
        )
        
        # Debug: Show raw values if body is empty
        if not body or body == 'N/A':
            st.warning("⚠️ Email body is empty. Check logs for generation errors.")
            st.json(email_data)  # Show raw data for debugging
    
    with tab2:
        # Editable email section
        st.markdown("### Edit Email Template")
        st.info("💡 Make any changes you'd like, then copy from the 'Copy Email' tab")
        
        # Initialize session state for edits if not present
        if 'email_subject_edit' not in st.session_state:
            st.session_state.email_subject_edit = email_data.get('subject', '')
        if 'email_body_edit' not in st.session_state:
            st.session_state.email_body_edit = email_data.get('body', '')
        
        # Editable subject
        edited_subject = st.text_input(
            "Subject Line:",
            value=st.session_state.email_subject_edit,
            key="subject_edit_input"
        )
        st.session_state.email_subject_edit = edited_subject
        
        st.markdown("---")
        
        # Editable body
        edited_body = st.text_area(
            "Email Body:",
            value=st.session_state.email_body_edit,
            height=400,
            key="body_edit_input"
        )
        st.session_state.email_body_edit = edited_body
        
        # Show character count
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Subject Length", f"{len(edited_subject)} characters")
        with col2:
            st.metric("Body Length", f"{len(edited_body)} characters")
    
    with tab3:
        # Provide copyable text with edited version
        full_email = f"""SUBJECT: {st.session_state.email_subject_edit}

---

{st.session_state.email_body_edit}"""
        
        # Text area for easy copying
        st.text_area(
            "Copy the email below (includes your edits):",
            value=full_email,
            height=400,
            disabled=True,
            key="email_copy_area"
        )
        
        # Copy button using Streamlit's native copy functionality
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.button(
                "📋 Copy to Clipboard",
                on_click=_copy_to_clipboard,
                args=(full_email,),
                width='stretch'
            )
        
        with col2:
            # Download as text file
            st.download_button(
                label="📥 Download as Text",
                data=full_email,
                file_name="client_email.txt",
                mime="text/plain",
                width='stretch'
            )
    
    # Show reflection notes if available
    if reflection_result and reflection_result.get('reflection_notes'):
        st.divider()
        with st.expander("🤖 AI Reflection Notes"):
            st.markdown(reflection_result.get('reflection_notes', 'No notes available'))


def _copy_to_clipboard(text: str):
    """Copy text to clipboard (works via browser)"""
    st.write("✅ Text ready to copy! Use the text area above to select and copy.")


def display_email_input_form() -> str:
    """
    Display form to collect email recipient name
    
    Returns:
        str: Recipient name or None
    """
    st.markdown("### 📝 Email Recipient Information (Optional)")
    
    recipient_name = st.text_input(
        "Recipient Name (Client Name)",
        value="",
        placeholder="Leave blank for 'Valued Client'",
        help="Enter the name of the person receiving this valuation email (optional)"
    )
    
    # Return None if empty, so workflow can use default "Valued Client"
    return recipient_name.strip() if recipient_name.strip() else None

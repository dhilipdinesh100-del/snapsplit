"""
app.py - SnapSplit: AI Receipt & Expense Tracker / Bill Splitter
A clean, student-friendly Streamlit web application powered by Google Gemini Vision.
"""

import os
import smtplib
from email.mime.text import MIMEText
import streamlit as st
from google import genai
from google.genai import types

from prompts import (
    SYSTEM_PROMPT,
    WELCOME_MESSAGE_TEMPLATE,
    SUMMARY_REQUEST_PROMPT,
)

# ==============================================================================
# SECRETS MANAGEMENT
# ==============================================================================
def get_secret(key: str, default: str = "") -> str:
    """Safely fetch a secret from Streamlit secrets or OS environment variables."""
    try:
        if key in st.secrets:
            val = st.secrets[key]
            if val and not str(val).startswith("your-"):
                return str(val).strip()
    except Exception:
        pass
    env_val = os.environ.get(key, default)
    if env_val and not str(env_val).startswith("your-"):
        return str(env_val).strip()
    return default


# ==============================================================================
# CONFIGURATION & CONSTANTS
# ==============================================================================
# Easily configurable model name for multimodal vision + chat
# 'gemini-3-flash-preview' is the current active multimodal Flash model.
MODEL_NAME = get_secret("GEMINI_MODEL", "gemini-3-flash-preview")
PAGE_TITLE = "SnapSplit — AI Receipt & Expense Tracker"
PAGE_ICON = "🥧"

# Configure the Streamlit page layout
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==============================================================================
# GEMINI CLIENT (CACHED)
# ==============================================================================
@st.cache_resource
def get_gemini_client(api_key: str):
    """
    Initializes and caches the Google GenAI client instance.
    Uses st.cache_resource so the client is not recreated on every rerun.
    """
    return genai.Client(api_key=api_key)


# ==============================================================================
# CHAT HELPER FUNCTIONS
# ==============================================================================
def render_message(message: dict):
    """
    Renders a stored chat message in the Streamlit UI.
    Supports both 'text' and 'image' kinds for user and assistant roles.
    """
    role = message.get("role", "assistant")
    kind = message.get("kind", "text")
    content = message.get("content")

    with st.chat_message(role):
        if kind == "text":
            st.markdown(content)
        elif kind == "image":
            st.image(content, caption="Uploaded Receipt", use_container_width=True)


def add_message(role: str, kind: str, content):
    """
    Appends a new message to session state and immediately renders it.
    """
    msg = {"role": role, "kind": kind, "content": content}
    st.session_state.messages.append(msg)
    render_message(msg)


def create_chat_session(client, preferred_model: str = MODEL_NAME):
    """
    Initializes a new Gemini chat session with automatic model fallback
    if a specific model is busy or unavailable.
    """
    candidates = [preferred_model, "gemini-3-flash-preview", "gemini-flash-latest"]
    seen = set()
    models_to_try = [m for m in candidates if not (m in seen or seen.add(m))]

    last_error = None
    for model_name in models_to_try:
        try:
            chat = client.chats.create(
                model=model_name,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.2,
                ),
            )
            return chat, model_name
        except Exception as e:
            last_error = e
            continue

    raise last_error or RuntimeError("Could not create Gemini chat session.")


def ask_gemini(chat, contents) -> str:
    """
    Sends text or multimodal contents (Part + text) to the Gemini chat session.
    Automatically retries across active multimodal models (gemini-flash-latest / gemini-3-flash-preview)
    if Google returns temporary 503 high demand or 404 errors.
    Reveals the actual exception if all fail, while sanitizing credentials.
    """
    fallback_models = ["gemini-flash-latest", "gemini-3-flash-preview"]
    current_model = getattr(chat, "_model", "gemini-flash-latest")
    models_to_try = [current_model] + [m for m in fallback_models if m != current_model]

    last_exc = None
    for model_name in models_to_try:
        try:
            chat._model = model_name
            response = chat.send_message(contents)
            if response and response.text:
                return response.text
            return "Sorry, I couldn't read the receipt clearly. Please try uploading a sharper image."
        except Exception as exc:
            last_exc = exc
            continue

    # If all models failed, report the actual exception without leaking credentials
    err_msg = str(last_exc)
    for secret_key in ["GEMINI_API_KEY", "GMAIL_APP_PASSWORD"]:
        val = get_secret(secret_key)
        if val and len(val) > 4:
            err_msg = err_msg.replace(val, "[REDACTED]")

    st.error(f"⚠️ Gemini API Error: {err_msg}")
    return f"Sorry, I couldn't analyze that receipt right now.\n\n**Error details:** {err_msg}"


# ==============================================================================
# EMAIL FUNCTIONS (SMTP SSL)
# ==============================================================================
def clean_email_text(text: str) -> str:
    """
    Cleans and formats generated summary text for email readability.
    Removes extraneous blank lines and trims leading/trailing whitespace.
    """
    lines = [line.rstrip() for line in text.strip().splitlines()]
    cleaned_lines = []
    prev_blank = False
    for line in lines:
        if not line:
            if not prev_blank:
                cleaned_lines.append("")
                prev_blank = True
        else:
            cleaned_lines.append(line)
            prev_blank = False
    return "\n".join(cleaned_lines).strip()


def send_email(to_address: str, subject: str, body: str) -> tuple[bool, str]:
    """
    Sends an email using Python's built-in smtplib via Gmail SMTP (port 465 SSL).
    Reads credentials securely from Streamlit secrets.
    Never exposes passwords or sensitive keys in error outputs.
    """
    gmail_address = get_secret("GMAIL_ADDRESS")
    gmail_app_password = get_secret("GMAIL_APP_PASSWORD")

    if not gmail_address or not gmail_app_password:
        return (
            False,
            "Couldn't send the email. Please check your email configuration and try again. (GMAIL_ADDRESS or GMAIL_APP_PASSWORD not set in secrets.toml)",
        )

    try:
        cleaned_body = clean_email_text(body)
        msg = MIMEText(cleaned_body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = gmail_address
        msg["To"] = to_address

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_address, gmail_app_password)
            server.send_message(msg)

        return True, "Summary sent to your email 📧"
    except smtplib.SMTPAuthenticationError:
        return (
            False,
            "Couldn't send the email. Gmail authentication failed. Ensure you are using a 16-character App Password, not your normal password.",
        )
    except Exception:
        return (
            False,
            "Couldn't send the email. Please check your email configuration and try again.",
        )


# ==============================================================================
# INITIALIZE SESSION STATE
# ==============================================================================
if "onboarded" not in st.session_state:
    st.session_state.onboarded = False

if "name" not in st.session_state:
    st.session_state.name = ""

if "email" not in st.session_state:
    st.session_state.email = ""

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat" not in st.session_state:
    st.session_state.chat = None


# ==============================================================================
# SCREEN 1: ONBOARDING SCREEN
# ==============================================================================
if not st.session_state.onboarded:
    col_left, col_center, col_right = st.columns([1, 2, 1])

    with col_center:
        st.write("")
        st.write("")
        st.title("🥧 SnapSplit")
        st.subheader("Snap it. Split it. Send it.")
        st.write(
            "Welcome! SnapSplit is your AI-powered receipt and expense assistant. "
            "Upload any bill or receipt to automatically extract items, calculate splits, and email summaries."
        )

        # Check for Gemini API key configuration
        api_key = get_secret("GEMINI_API_KEY")
        if not api_key:
            st.warning(
                "⚠️ **Gemini API Key Missing**: Please set `GEMINI_API_KEY` in `.streamlit/secrets.toml` "
                "or configure it in your environment before getting started."
            )

        with st.form("onboarding_form", clear_on_submit=False):
            name_input = st.text_input("Your Name", placeholder="e.g. Alex Johnson")
            email_input = st.text_input(
                "Email Address (where receipt summaries will be sent)",
                placeholder="e.g. alex@example.com",
            )
            submit_button = st.form_submit_button("Let's go 🚀", use_container_width=True)

            if submit_button:
                clean_name = name_input.strip()
                clean_email = email_input.strip()

                if not clean_name or not clean_email:
                    st.warning("Please enter both your name and email address.")
                elif "@" not in clean_email or "." not in clean_email:
                    st.warning("Please enter a valid email address.")
                elif not api_key:
                    st.error("Please add your GEMINI_API_KEY to `.streamlit/secrets.toml` first.")
                else:
                    # Initialize Gemini Client & Chat session with resilient fallback
                    try:
                        client = get_gemini_client(api_key)
                        chat_session, model_used = create_chat_session(client, MODEL_NAME)

                        st.session_state.name = clean_name
                        st.session_state.email = clean_email
                        st.session_state.chat = chat_session
                        st.session_state.messages = []

                        # Add the initial personalized welcome message
                        welcome_text = WELCOME_MESSAGE_TEMPLATE.format(
                            name=clean_name, email=clean_email
                        )
                        st.session_state.messages.append(
                            {"role": "assistant", "kind": "text", "content": welcome_text}
                        )

                        st.session_state.onboarded = True
                        st.rerun()

                    except Exception as err:
                        st.error(f"Error starting AI session: {str(err)}. Please verify your API key.")


# ==============================================================================
# SCREEN 2: MAIN APPLICATION (POST-ONBOARDING)
# ==============================================================================
else:
    # Ensure any previous session with deprecated model name is cleanly updated
    if st.session_state.chat is not None:
        current_model = getattr(st.session_state.chat, "_model", "")
        if current_model not in ["gemini-flash-latest", "gemini-3-flash-preview"]:
            st.session_state.chat._model = "gemini-flash-latest"
    # --------------------------------------------------------------------------
    # SIDEBAR
    # --------------------------------------------------------------------------
    with st.sidebar:
        st.title("🥧 SnapSplit")
        st.markdown("**AI Receipt & Expense Assistant**")
        st.divider()

        st.markdown(f"👤 **User:** {st.session_state.name}")
        st.markdown(f"📧 **Email:** `{st.session_state.email}`")
        st.caption("Receipt summaries will be emailed to this address.")

        st.divider()
        st.markdown("### 💡 Quick Tips")
        st.markdown(
            """
            - 📸 **Upload receipt**: Click the **+** paperclip in the chat input.
            - 🔍 **Item details**: Ask *"How much was the drinks?"*
            - 👥 **Bill split**: Say *"Split between 4 people"*.
            - 📧 **Send email**: Click **Send Summary to Email** above.
            """
        )

        st.divider()
        # Reset session button
        if st.button("🔄 Start New Session", use_container_width=True):
            st.session_state.onboarded = False
            st.session_state.messages = []
            st.session_state.chat = None
            st.rerun()

    # --------------------------------------------------------------------------
    # MAIN HEADER & EMAIL ACTION BAR
    # --------------------------------------------------------------------------
    header_col1, header_col2 = st.columns([3, 2])

    with header_col1:
        st.title("🥧 SnapSplit")
        st.caption("AI Receipt & Expense Tracker / Bill Splitter")
        st.write(f"Logged in as **{st.session_state.name}**")

    with header_col2:
        st.write("")
        st.write("")
        # Enable email button only if user has interacted (uploaded receipt or asked a question)
        has_user_interaction = any(m.get("role") == "user" for m in st.session_state.messages)

        send_email_clicked = st.button(
            "📧 Send Summary to Email",
            disabled=not has_user_interaction,
            help=(
                "Generates an itemized receipt & split summary and emails it to you"
                if has_user_interaction
                else "Upload a receipt or ask a question first to enable email summary"
            ),
            use_container_width=True,
        )

    # --------------------------------------------------------------------------
    # HANDLE EMAIL SUMMARY ACTION
    # --------------------------------------------------------------------------
    if send_email_clicked:
        if not st.session_state.chat:
            st.error("AI session is not active. Please start a new session.")
        else:
            with st.spinner("Generating clean expense summary and sending email..."):
                summary_text = ask_gemini(st.session_state.chat, SUMMARY_REQUEST_PROMPT)

                if "Sorry, I couldn't analyze" in summary_text:
                    st.error("Couldn't generate the email summary right now. Please try again.")
                else:
                    success, email_msg = send_email(
                        to_address=st.session_state.email,
                        subject="SnapSplit Receipt & Expense Summary",
                        body=summary_text,
                    )
                    if success:
                        st.success(f"{email_msg} ({st.session_state.email})")
                        # Add notification in the chat
                        add_message(
                            role="assistant",
                            kind="text",
                            content=(
                                f"✅ **Receipt Summary sent to {st.session_state.email}!**\n\n"
                                f"```text\n{summary_text}\n```"
                            ),
                        )
                    else:
                        st.error(email_msg)

    st.divider()

    # --------------------------------------------------------------------------
    # DISPLAY CHAT HISTORY
    # --------------------------------------------------------------------------
    for msg in st.session_state.messages:
        render_message(msg)

    # --------------------------------------------------------------------------
    # CHAT INPUT (SUPPORTS TEXT AND RECEIPT IMAGE ATTACHMENTS)
    # --------------------------------------------------------------------------
    chat_prompt = st.chat_input(
        placeholder="Ask a question, split the bill, or attach a receipt image...",
        accept_file=True,
        file_type=["jpg", "jpeg", "png"],
    )

    if chat_prompt:
        # Extract potential text and attached file(s)
        user_text = ""
        uploaded_files = []

        if isinstance(chat_prompt, str):
            user_text = chat_prompt.strip()
        else:
            user_text = getattr(chat_prompt, "text", "") or ""
            user_text = user_text.strip()
            try:
                uploaded_files = getattr(chat_prompt, "files", []) or []
            except AttributeError:
                uploaded_files = []

        # ----------------------------------------------------------------------
        # SCENARIO 1: RECEIPT IMAGE UPLOADED (WITH OR WITHOUT TEXT)
        # ----------------------------------------------------------------------
        if uploaded_files:
            for uploaded_file in uploaded_files:
                # Use getvalue() for reliable byte access in Streamlit
                photo_bytes = (
                    uploaded_file.getvalue()
                    if hasattr(uploaded_file, "getvalue")
                    else uploaded_file.read()
                )
                mime_type = getattr(uploaded_file, "type", None) or "image/jpeg"
                if mime_type not in ["image/jpeg", "image/png", "image/webp", "image/gif"]:
                    mime_type = "image/jpeg"

                # 1. Render and store user's receipt image
                add_message(role="user", kind="image", content=photo_bytes)

                # 2. Convert to Gemini Vision Part
                image_part = types.Part.from_bytes(
                    data=photo_bytes,
                    mime_type=mime_type,
                )

                # 3. Determine instructions for Gemini Vision
                if user_text:
                    add_message(role="user", kind="text", content=user_text)
                    gemini_payload = [image_part, user_text]
                else:
                    default_instruction = (
                        "Analyze this receipt. Extract the readable items, prices, subtotal, "
                        "tax, fees, discounts, and total. Clearly identify any uncertain values."
                    )
                    gemini_payload = [image_part, default_instruction]

                # 4. Request Gemini Vision analysis
                with st.spinner("Analyzing receipt with Gemini Vision..."):
                    reply = ask_gemini(st.session_state.chat, gemini_payload)
                    add_message(role="assistant", kind="text", content=reply)

        # ----------------------------------------------------------------------
        # SCENARIO 2: TEXT ONLY (FOLLOW-UP QUESTION OR BILL SPLIT REQUEST)
        # ----------------------------------------------------------------------
        elif user_text:
            add_message(role="user", kind="text", content=user_text)

            with st.spinner("Thinking..."):
                reply = ask_gemini(st.session_state.chat, user_text)
                add_message(role="assistant", kind="text", content=reply)

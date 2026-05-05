import json
import os
import shutil
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from body_type_assessment import DoshaAssessment, get_dosha_color, get_dosha_icon
from model import handle_query


# ------------------------- Helper Functions -------------------------

def convert_to_serializable(obj):
    """Convert non-serializable objects to serializable format"""
    if hasattr(obj, "__dict__"):
        return {key: convert_to_serializable(value) for key, value in obj.__dict__.items()}
    if hasattr(obj, "to_dict"):
        return convert_to_serializable(obj.to_dict())
    if isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    return str(obj)


def get_user_id_from_url():
    query_params = st.query_params
    user_id = query_params.get("userId")
    if isinstance(user_id, list):
        return user_id[0] if user_id else None
    return user_id


def get_chat_history_file(user_id):
    """Return a unique filename per user"""
    if not os.path.exists("chat_histories"):
        os.makedirs("chat_histories")
    return f"chat_histories/chat_history_{user_id}.json"


def load_chat_history(user_id):
    file_path = get_chat_history_file(user_id)
    if os.path.exists(file_path):
        try:
            if os.path.getsize(file_path) == 0:
                return []

            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except (json.JSONDecodeError, ValueError) as exc:
            print(f"Warning: Chat history file is corrupted. Starting fresh. Error: {exc}")
            backup_path = f"{file_path}.backup"
            try:
                os.rename(file_path, backup_path)
                print(f"Corrupted file backed up as: {backup_path}")
            except Exception:
                pass
            return []
        except Exception as exc:
            print(f"Error loading chat history: {exc}")
            return []
    return []


def save_chat_history(chat_history, user_id):
    file_path = get_chat_history_file(user_id)
    try:
        serializable_history = []
        for chat in chat_history:
            serializable_chat = {}
            for key, value in chat.items():
                serializable_chat[key] = convert_to_serializable(value)
            serializable_history.append(serializable_chat)

        temp_file_path = f"{file_path}.tmp"
        with open(temp_file_path, "w", encoding="utf-8") as file:
            json.dump(serializable_history, file, indent=2)

        shutil.move(temp_file_path, file_path)

    except Exception as exc:
        print(f"Error saving chat history: {exc}")
        temp_file_path = f"{file_path}.tmp"
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


def clear_chat_history(user_id):
    file_path = get_chat_history_file(user_id)
    if os.path.exists(file_path):
        os.remove(file_path)


def get_user_profile_file(user_id):
    """Return a unique profile filename per user."""
    if not os.path.exists("user_profiles"):
        os.makedirs("user_profiles")
    return f"user_profiles/user_profile_{user_id}.json"


def load_user_profile(user_id):
    file_path = get_user_profile_file(user_id)
    if os.path.exists(file_path):
        try:
            if os.path.getsize(file_path) == 0:
                return {}

            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except (json.JSONDecodeError, ValueError) as exc:
            print(f"Warning: User profile file is corrupted. Starting fresh. Error: {exc}")
            backup_path = f"{file_path}.backup"
            try:
                os.rename(file_path, backup_path)
                print(f"Corrupted profile backed up as: {backup_path}")
            except Exception:
                pass
            return {}
        except Exception as exc:
            print(f"Error loading user profile: {exc}")
            return {}
    return {}


def save_user_profile(profile_data, user_id):
    file_path = get_user_profile_file(user_id)
    try:
        temp_file_path = f"{file_path}.tmp"
        with open(temp_file_path, "w", encoding="utf-8") as file:
            json.dump(convert_to_serializable(profile_data), file, indent=2)

        shutil.move(temp_file_path, file_path)
    except Exception as exc:
        print(f"Error saving user profile: {exc}")
        temp_file_path = f"{file_path}.tmp"
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


def clear_user_profile(user_id):
    file_path = get_user_profile_file(user_id)
    if os.path.exists(file_path):
        os.remove(file_path)


def format_bot_response(response_data, body_type=None):
    result = response_data.get("result", "")
    response_body_type = body_type or response_data.get("body_type")
    body_type_note = ""
    if response_body_type:
        body_type_note = f"<p style='font-weight:bold; color:#22543D;'>Your body type: {response_body_type}</p>"

    disclaimer = "<hr><p style='text-align:center; font-weight:bold;'>These remedies are complementary. Consult a healthcare provider for persistent issues.</p>"
    return f"""
    <div style="background-color:#F0FCED; padding:10px; border-radius:10px; margin:5px 0;">
        <b>VedaBot:</b>
        {body_type_note}
        <p>{result}</p>
        {disclaimer}
    </div>
    """


def format_user_query(query):
    return f"""
    <div style="background-color:#CFEBCF; padding:10px; border-radius:10px; margin:5px 0; text-align:right;">
        <b>You:</b>
        <p>{query}</p>
    </div>
    """


def load_css(file_name):
    if os.path.exists(file_name):
        with open(file_name, encoding="utf-8") as file:
            st.markdown(f"<style>{file.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"CSS file '{file_name}' not found.")


def create_chat_id():
    """Create a unique chat ID based on timestamp"""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def render_dosha_result(result):
    primary_dosha = result.get("primary_dosha", "")
    color = get_dosha_color(primary_dosha)
    icon = get_dosha_icon(primary_dosha)
    percentage = result.get("percentages", {}).get(primary_dosha, 0)

    st.markdown(
        f"""
        <div style="background-color:{color}; padding:18px; border-radius:10px; border-left:5px solid #22543D; margin-bottom:18px;">
            <h3 style="margin:0; color:#22543D;">{icon} Saved Body Type: {primary_dosha}</h3>
            <p style="margin:8px 0 0 0; font-weight:bold;">Primary dosha strength: {percentage}%</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(result.get("analysis", ""))


def render_body_type_assessment(user_id, session_key_dosha_results, session_key_show_assessment):
    st.markdown(
        """
        <style>
        div[data-testid="stRadio"] {
            background-color: #F8FFF6;
            border: 1px solid #D7EAD2;
            border-radius: 10px;
            padding: 12px;
            margin-bottom: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    saved_result = st.session_state.get(session_key_dosha_results)
    if saved_result:
        render_dosha_result(saved_result)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Retake Assessment", use_container_width=True, type="primary"):
                st.session_state[session_key_dosha_results] = None
                clear_user_profile(user_id)
                st.rerun()
        with col2:
            if st.button("Back to Chat", use_container_width=True):
                st.session_state[session_key_show_assessment] = False
                st.rerun()
        return

    st.markdown(
        """
        <div style="background-color:#FFF8E1; border:2px solid #D6A100; border-radius:10px; padding:16px; margin-bottom:18px;">
            <h3 style="color:#22543D; margin:0;">Complete Your Body Type Assessment First</h3>
            <p style="margin:8px 0 0 0; font-weight:bold;">
                VedaBot personalizes Ayurvedic guidance by your dosha. Please complete this assessment before starting a chat.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    assessment = DoshaAssessment(form_key=f"dosha_assessment_{user_id}")
    result = assessment.run_assessment()

    if result:
        st.session_state[session_key_dosha_results] = result
        save_user_profile(result, user_id)
        st.rerun()



# ------------------------- Main App -------------------------

def main():
    load_dotenv()

    st.set_page_config(
        page_title="VedaBot",
        page_icon="https://res.cloudinary.com/dokavb4tb/image/upload/v1757239450/healthai-favicon_ovvzqj.png",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    load_css("style.css")

    # Get user ID from iframe query params (required by design).
    user_id = get_user_id_from_url()
    if not user_id:
        st.error("Missing required query parameter: userId")
        st.caption("This app is intentionally coupled to an upstream web app/iframe.")
        st.code("?userId=<your-user-id>")
        st.stop()
        return

    session_key_chat = f"chat_history_{user_id}"
    session_key_responses = f"responses_{user_id}"
    session_key_current_chat = f"current_chat_{user_id}"
    session_key_selected_chat = f"selected_chat_{user_id}"
    session_key_viewing_history = f"viewing_history_{user_id}"
    session_key_loading = f"loading_{user_id}"
    session_key_dosha_results = f"dosha_results_{user_id}"
    session_key_show_assessment = f"show_body_type_assessment_{user_id}"

    if session_key_chat not in st.session_state:
        st.session_state[session_key_chat] = load_chat_history(user_id)
    if session_key_responses not in st.session_state:
        st.session_state[session_key_responses] = []
    if session_key_current_chat not in st.session_state:
        st.session_state[session_key_current_chat] = None
    if session_key_selected_chat not in st.session_state:
        st.session_state[session_key_selected_chat] = None
    if session_key_viewing_history not in st.session_state:
        st.session_state[session_key_viewing_history] = False
    if session_key_loading not in st.session_state:
        st.session_state[session_key_loading] = False
    if session_key_dosha_results not in st.session_state:
        st.session_state[session_key_dosha_results] = load_user_profile(user_id) or None
    if session_key_show_assessment not in st.session_state:
        st.session_state[session_key_show_assessment] = False

    if not st.session_state[session_key_dosha_results]:
        st.session_state[session_key_show_assessment] = True
        st.session_state[session_key_viewing_history] = False

    st.markdown(
        """
    <style>
    .selected-chat {
        background-color: #E6F4EA;
        border-left: 3px solid #22543D;
        padding-left: 10px;
        margin-left: -10px;
    }
    .stContainer {
        scroll-behavior: smooth;
    }
    .stTextInput input:disabled {
        background-color: #f0f0f0 !important;
        color: #888 !important;
        cursor: not-allowed !important;
    }
    .stButton button:disabled {
        background-color: #f0f0f0 !important;
        color: #888 !important;
        cursor: not-allowed !important;
        border: 1px solid #ccc !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class="main-header" style="align-items: center; text-align: center; margin-top: -45px; margin-bottom: 25px;">
        <div style="font-size:52px; font-weight:bold;">Welcome to VedaBot</div>
        <div style="font-size:32px; font-weight:bold;">Take your health into your hands</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("<h2 style='color:#22543D;text-align:center; font-weight:bold;'>VedaBot</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-weight:bold;'>Take your health into your hands</p>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)

        if st.button("Know Your Body Type", use_container_width=True, disabled=st.session_state[session_key_loading]):
            st.session_state[session_key_show_assessment] = True
            st.session_state[session_key_viewing_history] = False
            st.session_state[session_key_selected_chat] = None
            st.rerun()

        if st.button("New Chat", use_container_width=True, type="primary", disabled=st.session_state[session_key_loading]):
            st.session_state[session_key_responses] = []
            st.session_state[session_key_current_chat] = None
            st.session_state[session_key_selected_chat] = None
            st.session_state[session_key_viewing_history] = False
            st.session_state[session_key_show_assessment] = False
            st.session_state[session_key_loading] = False
            st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<b style='color:#22543D; font-weight:bold;'>Instructions:</b>", unsafe_allow_html=True)
        st.markdown(
            """
        <ul style='padding-left:20px; font-weight:bold;'>
            <li>Enter queries related to your health.</li>
            <li>Receive ayurvedic insights from our bot.</li>
            <li>In severe cases, consult your nearest doctor.</li>
        </ul>
        """,
            unsafe_allow_html=True,
        )
        st.markdown("<hr>", unsafe_allow_html=True)

        if st.session_state[session_key_chat]:
            st.markdown("<b style='font-size:18px; font-weight:bold;'>Chat History</b>", unsafe_allow_html=True)

            for idx, chat in enumerate(reversed(st.session_state[session_key_chat])):
                chat_preview = chat["question"][:50] + "..." if len(chat["question"]) > 50 else chat["question"]
                chat_time = chat["time"]

                row_container = st.container()
                with row_container:
                    col1 = st.columns([1])[0]
                    with col1:
                        is_selected = st.session_state[session_key_selected_chat] == len(st.session_state[session_key_chat]) - 1 - idx

                        if st.button(
                            f"{chat_preview}",
                            key=f"chat_{idx}_{chat_time}",
                            use_container_width=True,
                            disabled=is_selected or st.session_state[session_key_loading],
                        ):
                            actual_idx = len(st.session_state[session_key_chat]) - 1 - idx
                            selected_chat = st.session_state[session_key_chat][actual_idx]

                            st.session_state[session_key_responses] = []
                            st.session_state[session_key_responses].append(format_user_query(selected_chat["question"]))
                            st.session_state[session_key_responses].append(format_bot_response(selected_chat["response"]))

                            st.session_state[session_key_current_chat] = selected_chat.get("chat_id", chat_time)
                            st.session_state[session_key_selected_chat] = actual_idx
                            st.session_state[session_key_viewing_history] = True
                            st.session_state[session_key_show_assessment] = False
                            st.session_state[session_key_loading] = False
                            st.rerun()

            st.markdown("<hr>", unsafe_allow_html=True)

            if st.button("Clear All History", use_container_width=True, disabled=st.session_state[session_key_loading]):
                clear_chat_history(user_id)
                st.session_state[session_key_chat].clear()
                st.session_state[session_key_responses].clear()
                st.session_state[session_key_current_chat] = None
                st.session_state[session_key_selected_chat] = None
                st.session_state[session_key_viewing_history] = False
                st.session_state[session_key_show_assessment] = False
                st.session_state[session_key_loading] = False
                st.success("Chat History has been cleared.")
                st.rerun()

    if st.session_state[session_key_show_assessment]:
        render_body_type_assessment(user_id, session_key_dosha_results, session_key_show_assessment)
        return

    chat_container = st.container()

    for resp in st.session_state[session_key_responses]:
        chat_container.markdown(resp, unsafe_allow_html=True)

    if not st.session_state[session_key_responses]:
        chat_container.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)

    if not st.session_state[session_key_viewing_history]:
        with chat_container.form("query_form", clear_on_submit=True):
            col1, col2 = st.columns([6, 1])
            with col1:
                user_query = st.text_input(
                    label="Ask VedaBot:",
                    placeholder="e.g., What are Ayurvedic remedies for cold?" if not st.session_state[session_key_loading] else "Please wait while we load the response...",
                    label_visibility="collapsed",
                    key="input_text",
                    disabled=st.session_state[session_key_loading],
                )
            with col2:
                submitted = st.form_submit_button(
                    "Submit" if not st.session_state[session_key_loading] else "Loading...",
                    use_container_width=True,
                    disabled=st.session_state[session_key_loading],
                )

        loader_placeholder = chat_container.empty()

        if submitted and not st.session_state[session_key_loading]:
            q = (user_query or "").strip()
            if q:
                st.session_state[session_key_loading] = True
                st.session_state[session_key_responses].append(format_user_query(q))
                st.rerun()

        if st.session_state[session_key_loading] and st.session_state[session_key_responses]:
            last_response = st.session_state[session_key_responses][-1]
            if "You:" in last_response and "VedaBot:" not in last_response:
                import re

                query_match = re.search(r"<p>(.*?)</p>", last_response)
                if query_match:
                    current_query = query_match.group(1)
                    dosha_result = st.session_state.get(session_key_dosha_results)
                    primary_dosha = dosha_result.get("primary_dosha") if dosha_result else None

                    with loader_placeholder, st.spinner("Finding the best Ayurvedic insights..."):
                        if primary_dosha:
                            response_data = handle_query(current_query, body_type=primary_dosha)
                        else:
                            response_data = handle_query(current_query)

                    loader_placeholder.empty()

                    chat_id = create_chat_id()
                    chat_entry = {
                        "chat_id": chat_id,
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "question": current_query,
                    }

                    if response_data:
                        serializable_response = convert_to_serializable(response_data)
                        if primary_dosha:
                            serializable_response["body_type"] = primary_dosha
                        st.session_state[session_key_responses].append(format_bot_response(response_data, primary_dosha))
                        chat_entry["response"] = serializable_response
                    else:
                        error_response = {"result": "No relevant insights found. Please refine your query."}
                        if primary_dosha:
                            error_response["body_type"] = primary_dosha
                        st.session_state[session_key_responses].append(format_bot_response(error_response, primary_dosha))
                        chat_entry["response"] = error_response

                    st.session_state[session_key_chat].append(chat_entry)
                    save_chat_history(st.session_state[session_key_chat], user_id)

                    st.session_state[session_key_current_chat] = chat_id
                    st.session_state[session_key_selected_chat] = len(st.session_state[session_key_chat]) - 1
                    st.session_state[session_key_viewing_history] = False
                    st.session_state[session_key_loading] = False

                    st.rerun()
    else:
        chat_container.markdown(
            """
        <div style='background-color:#DFF6E0; padding:15px; border-radius:10px; margin:20px 0; text-align:center;'>
            <b style='font-weight:bold;'>Viewing Chat History</b><br>
            <p style='margin-top:10px; font-weight:bold;'>Click "New Chat" to start a new conversation</p>
        </div>
        """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()

import streamlit as st
import os
import json
import shutil
from datetime import datetime
from dotenv import load_dotenv
from model import handle_query
from urllib.parse import urlparse, parse_qs

# ------------------------- Helper Functions -------------------------

def convert_to_serializable(obj):
    """Convert non-serializable objects to serializable format"""
    if hasattr(obj, '__dict__'):
        return {key: convert_to_serializable(value) for key, value in obj.__dict__.items()}
    elif hasattr(obj, 'to_dict'):
        return convert_to_serializable(obj.to_dict())
    elif isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        return str(obj)

def get_user_id_from_url():
    query_params = st.query_params
    user_id = query_params.get("userId", None)
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
            
            with open(file_path, "r") as file:
                content = file.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Warning: Chat history file is corrupted. Starting fresh. Error: {e}")
            backup_path = f"{file_path}.backup"
            try:
                os.rename(file_path, backup_path)
                print(f"Corrupted file backed up as: {backup_path}")
            except:
                pass
            return []
        except Exception as e:
            print(f"Error loading chat history: {e}")
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
        with open(temp_file_path, "w") as file:
            json.dump(serializable_history, file, indent=2)
        
        shutil.move(temp_file_path, file_path)
        
    except Exception as e:
        print(f"Error saving chat history: {e}")
        temp_file_path = f"{file_path}.tmp"
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

def clear_chat_history(user_id):
    file_path = get_chat_history_file(user_id)
    if os.path.exists(file_path):
        os.remove(file_path)

def format_bot_response(response_data):
    result = response_data.get("result", "")
    disclaimer = "<hr><p style='text-align:center; font-weight:bold;'>These remedies are complementary. Consult a healthcare provider for persistent issues.</p>"
    return f"""
    <div style="background-color:#F0FCED; padding:10px; border-radius:10px; margin:5px 0;">
        <b>VedaBot:</b>
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
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"CSS file '{file_name}' not found.")

def create_chat_id():
    """Create a unique chat ID based on timestamp"""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")

# ------------------------- Main App -------------------------

def main():
    load_dotenv()

    st.set_page_config(
        page_title="VedaBot",
        page_icon='https://res.cloudinary.com/dokavb4tb/image/upload/v1757239450/healthai-favicon_ovvzqj.png',
        layout="wide",
        initial_sidebar_state="expanded"
    )

    load_css("style.css")

    # Get user ID from iframe query params
    user_id = get_user_id_from_url()
    if not user_id:
        st.error("User ID not found. Chat history cannot be loaded.")
        st.stop()
        return

    # Initialize session state with user-specific keys
    session_key_chat = f"chat_history_{user_id}"
    session_key_responses = f"responses_{user_id}"
    session_key_current_chat = f"current_chat_{user_id}"
    session_key_selected_chat = f"selected_chat_{user_id}"
    session_key_viewing_history = f"viewing_history_{user_id}"
    session_key_loading = f"loading_{user_id}"  # ADD THIS LINE - for loading state
    
    # Initialize chat history
    if session_key_chat not in st.session_state:
        st.session_state[session_key_chat] = load_chat_history(user_id)
    
    # Initialize current chat responses
    if session_key_responses not in st.session_state:
        st.session_state[session_key_responses] = []
    
    # Initialize current chat ID (for tracking which chat is being displayed)
    if session_key_current_chat not in st.session_state:
        st.session_state[session_key_current_chat] = None
    
    # Initialize selected chat index
    if session_key_selected_chat not in st.session_state:
        st.session_state[session_key_selected_chat] = None
    
    # Initialize viewing history flag
    if session_key_viewing_history not in st.session_state:
        st.session_state[session_key_viewing_history] = False

    # Initialize loading state - ADD THIS BLOCK
    if session_key_loading not in st.session_state:
        st.session_state[session_key_loading] = False

    # Add custom CSS for auto-focus and scrolling
    st.markdown("""
    <style>
    /* Highlight selected chat in sidebar */
    .selected-chat {
        background-color: #E6F4EA;
        border-left: 3px solid #22543D;
        padding-left: 10px;
        margin-left: -10px;
    }
    
    /* Auto-scroll to bottom of chat */
    .stContainer {
        scroll-behavior: smooth;
    }
    
    /* Disabled input styling */
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
    
    <script>
    // Auto-focus on input field when page loads
    window.addEventListener('DOMContentLoaded', (event) => {
        setTimeout(() => {
            const input = document.querySelector('input[type="text"]');
            if (input && !input.disabled) {
                input.focus();
                input.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }, 500);
    });
    </script>
    """, unsafe_allow_html=True)

    # ------------------------- Main Header -------------------------
    st.markdown("""
    <div class="main-header" style="align-items: center; text-align: center;">
        <div style="font-size:52px; font-weight:bold;">Welcome to VedaBot</div>
        <div style="font-size:32px; font-weight:bold;">Take your health into your hands</div>
    </div>
    """, unsafe_allow_html=True)

    # ------------------------- Sidebar -------------------------
    with st.sidebar:
        st.markdown("<h2 style='color:#22543D;text-align:center; font-weight:bold;'>VedaBot</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-weight:bold;'>Take your health into your hands</p>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # New Chat Button - DISABLE WHEN LOADING
        if st.button("New Chat", use_container_width=True, type="primary", disabled=st.session_state[session_key_loading]):
            st.session_state[session_key_responses] = []
            st.session_state[session_key_current_chat] = None
            st.session_state[session_key_selected_chat] = None
            st.session_state[session_key_viewing_history] = False
            st.session_state[session_key_loading] = False  # Reset loading state
            st.rerun()
        
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<b style='color:#22543D; font-weight:bold;'>Instructions:</b>", unsafe_allow_html=True)
        st.markdown("""
        <ul style='padding-left:20px; font-weight:bold;'>
            <li>Enter queries related to your health.</li>
            <li>Receive ayurvedic insights from our bot.</li>
            <li>In severe cases, consult your nearest doctor.</li>
        </ul>
        """, unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)

        # Chat History Section
        if st.session_state[session_key_chat]:
            st.markdown("<b style='font-size:18px; font-weight:bold;'>Chat History</b>", unsafe_allow_html=True)
            
            # Create columns for chat history items
            for idx, chat in enumerate(reversed(st.session_state[session_key_chat])):
                # Create a unique key for each chat button
                chat_preview = chat['question'][:50] + "..." if len(chat['question']) > 50 else chat['question']
                chat_time = chat['time']
                
                # Create a container for each chat item
                chat_container = st.container()
                with chat_container:
                    col1 = st.columns([1])[0]
                    with col1:
                        # Check if this is the selected chat
                        is_selected = st.session_state[session_key_selected_chat] == len(st.session_state[session_key_chat]) - 1 - idx
                        
                        # DISABLE HISTORY BUTTONS WHEN LOADING
                        if st.button(
                            f"{chat_preview}",
                            key=f"chat_{idx}_{chat_time}",
                            use_container_width=True,
                            disabled=is_selected or st.session_state[session_key_loading],
                        ):
                            # Load the selected chat
                            actual_idx = len(st.session_state[session_key_chat]) - 1 - idx
                            selected_chat = st.session_state[session_key_chat][actual_idx]
                            
                            # Clear current responses and load selected chat
                            st.session_state[session_key_responses] = []
                            st.session_state[session_key_responses].append(format_user_query(selected_chat['question']))
                            st.session_state[session_key_responses].append(format_bot_response(selected_chat['response']))
                            
                            # Update current chat tracking
                            st.session_state[session_key_current_chat] = selected_chat.get('chat_id', chat_time)
                            st.session_state[session_key_selected_chat] = actual_idx
                            st.session_state[session_key_viewing_history] = True
                            st.session_state[session_key_loading] = False  # Reset loading state
                            
                            st.rerun()

            st.markdown("<hr>", unsafe_allow_html=True)
            
            # Clear All History Button - DISABLE WHEN LOADING
            if st.button("Clear All History", use_container_width=True, disabled=st.session_state[session_key_loading]):
                clear_chat_history(user_id)
                st.session_state[session_key_chat].clear()
                st.session_state[session_key_responses].clear()
                st.session_state[session_key_current_chat] = None
                st.session_state[session_key_selected_chat] = None
                st.session_state[session_key_viewing_history] = False
                st.session_state[session_key_loading] = False  # Reset loading state
                st.success("Chat History has been cleared.")
                st.rerun()
        
    # ------------------------- Chat Display -------------------------
    chat_container = st.container()
    
    # Display current chat responses
    for resp in st.session_state[session_key_responses]:
        chat_container.markdown(resp, unsafe_allow_html=True)
    
    # Add some space before the input
    if not st.session_state[session_key_responses]:
        chat_container.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)

    # ------------------------- Input Form (only show if not viewing history) -------------------------
    if not st.session_state[session_key_viewing_history]:
        with chat_container.form("query_form", clear_on_submit=True):
            col1, col2 = st.columns([6, 1])
            with col1:
                user_query = st.text_input(
                    label="Ask VedaBot:",
                    placeholder="e.g., What are Ayurvedic remedies for cold?" if not st.session_state[session_key_loading] else "Please wait while we load the response...",
                    label_visibility="collapsed",
                    key="input_text",
                    disabled=st.session_state[session_key_loading]  # DISABLE INPUT WHEN LOADING
                )
            with col2:
                submitted = st.form_submit_button(
                    "Submit" if not st.session_state[session_key_loading] else "Loading...",
                    use_container_width=True,
                    disabled=st.session_state[session_key_loading]  # DISABLE SUBMIT WHEN LOADING
                )

        loader_placeholder = chat_container.empty()

        if submitted and not st.session_state[session_key_loading]:  # CHECK LOADING STATE
            q = (user_query or "").strip()
            if q:
                # SET LOADING STATE TO TRUE
                st.session_state[session_key_loading] = True
                
                st.session_state[session_key_responses].append(format_user_query(q))
                
                # Create chat entry with unique ID
                chat_id = create_chat_id()
                chat_entry = {
                    "chat_id": chat_id,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "question": q
                }

                # RERUN TO UPDATE UI WITH DISABLED STATE
                st.rerun()

        # Handle the actual API call if loading is true and we have a pending query
        if st.session_state[session_key_loading] and st.session_state[session_key_responses] and len(st.session_state[session_key_responses]) > 0:
            # Get the last user query from responses
            last_response = st.session_state[session_key_responses][-1]
            if "You:" in last_response and "VedaBot:" not in st.session_state[session_key_responses][-1]:
                # Extract query from the formatted response
                import re
                query_match = re.search(r'<p>(.*?)</p>', last_response)
                if query_match:
                    current_query = query_match.group(1)
                    
                    with loader_placeholder, st.spinner("Finding the best Ayurvedic insights..."):
                        response_data = handle_query(current_query)

                    loader_placeholder.empty()
                    
                    # Create chat entry
                    chat_id = create_chat_id()
                    chat_entry = {
                        "chat_id": chat_id,
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "question": current_query
                    }

                    if response_data:
                        serializable_response = convert_to_serializable(response_data)
                        st.session_state[session_key_responses].append(format_bot_response(response_data))
                        chat_entry["response"] = serializable_response
                    else:
                        error_response = {
                            "result": "No relevant insights found. Please refine your query."
                        }
                        st.session_state[session_key_responses].append(format_bot_response(error_response))
                        chat_entry["response"] = error_response

                    # Save to chat history
                    st.session_state[session_key_chat].append(chat_entry)
                    save_chat_history(st.session_state[session_key_chat], user_id)
                    
                    # Update current chat tracking
                    st.session_state[session_key_current_chat] = chat_id
                    st.session_state[session_key_selected_chat] = len(st.session_state[session_key_chat]) - 1
                    st.session_state[session_key_viewing_history] = False
                    
                    # RESET LOADING STATE
                    st.session_state[session_key_loading] = False

                    st.rerun()
    else:
        # Show a message when viewing history
        chat_container.markdown("""
        <div style='background-color:#DFF6E0; padding:15px; border-radius:10px; margin:20px 0; text-align:center;'>
            <b style=' font-weight:bold;'>Viewing Chat History</b><br>
            <p style='margin-top:10px; font-weight:bold;'>Click "New Chat" to start a new conversation</p>
        </div>
        """, unsafe_allow_html=True)

    # Auto-scroll to bottom JavaScript
    chat_container.markdown("""
    <script>
    window.scrollTo(0, document.body.scrollHeight);
    </script>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
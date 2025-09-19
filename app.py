import streamlit as st
import os
from openai import OpenAI
from datetime import datetime
import csv
import re

# -------------------------
# 1. Setup OpenAI API
# -------------------------
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("OpenAI API key not found! Set OPENAI_API_KEY as environment variable.")
    st.stop()

client = OpenAI(api_key=api_key)

# -------------------------
# 2. Initialize session state
# -------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processing" not in st.session_state:
    st.session_state.processing = False

# -------------------------
# 3. Strip HTML if sneaks in
# -------------------------
def strip_html_tags(text):
    return re.sub(r'<.*?>', '', text)

# -------------------------
# 4. Streamlit interface
# -------------------------
st.title("Inclusive UX Research Assistant")

# -------------------------
# 5. Display chat messages
# -------------------------
chat_placeholder = st.container()

def display_chat(max_messages=10):
    messages_to_display = st.session_state.messages[-max_messages:]
    with chat_placeholder:
        for msg in messages_to_display:
            role = msg["role"]
            content = msg["content"]
            timestamp = msg["time"].split("T")[1][:5]  # HH:MM only

            if role == "user":
                st.markdown(
                    f"""
                    <div style="
                        background-color: #f0f0f0;
                        padding: 10px 14px;
                        border-radius: 12px;
                        margin: 8px 0;
                        text-align: left;
                        max-width: 70%;
                        float: right;
                        clear: both;
                        word-wrap: break-word;">
                        <div style="font-size:14px; color:#333;">{content}</div>
                        <div style="font-size:10px; color:#888; margin-top:4px; text-align:right;">You • {timestamp}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:  # assistant
                st.markdown(
                    f"""
                    <div style="
                        background-color: #e0f7fa;
                        padding: 10px 14px;
                        border-radius: 12px;
                        margin: 8px 0;
                        text-align: left;
                        max-width: 70%;
                        float: left;
                        clear: both;
                        word-wrap: break-word;">
                        <div style="font-size:14px; color:#333;">{content}</div>
                        <div style="font-size:10px; color:#888; margin-top:4px; text-align:left;">Assistant • {timestamp}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.markdown("<div id='chat-bottom'></div>", unsafe_allow_html=True)

display_chat()

# -------------------------
# 6. User input form at bottom
# -------------------------
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("You:", placeholder="Type your message here...")
    submit_button = st.form_submit_button("Send")

if submit_button and user_input:
    timestamp = datetime.now().isoformat()
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "time": timestamp
    })
    st.session_state.processing = True

# -------------------------
# 7. Process user input with sliding window
# -------------------------
MAX_HISTORY = 6
if st.session_state.processing:
    bot_placeholder = st.empty()
    bot_placeholder.info("processing...")

    history_for_api = st.session_state.messages[-MAX_HISTORY:]

    system_message = {
        "role": "system",
        "content": """You are a helpful assistant. Always respond in plain text. You follow values of diversity, equity and inclusion.Exclusion happens when we solve problems using our own biases. We seek out exclusions, and use them as opportunities to create new and better experiences.

        Recognize exclusion
        We acknowledge bias and recognize exclusions that happen because of mismatches between people and experience.
        
        Learn from diversity
        Inclusive Design puts people in the center throughout the process. Their fresh, diverse perspectives are the key to true insight.
        
        Solve for one, extend to many
        Everyone has abilities and limits. Creating products for people with permanent disabilities creates results that benefit everyone.
        """
    }

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[system_message] + [
            {"role": m["role"], "content": m["content"]} for m in history_for_api
        ]
    )

    bot_message = response.choices[0].message.content
    bot_message = strip_html_tags(bot_message)  # clean any HTML

    timestamp = datetime.now().isoformat()
    st.session_state.messages.append({
        "role": "assistant",
        "content": bot_message,
        "time": timestamp
    })

    st.session_state.processing = False
    bot_placeholder.empty()

# -------------------------
# 8. Refresh chat display
# -------------------------
display_chat(max_messages=MAX_HISTORY)

# -------------------------
# 9. Save chat history
# -------------------------
def save_chat_history_csv(messages):
    filename = "chat_history.csv"
    file_exists = os.path.isfile(filename)
    with open(filename, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["timestamp", "role", "content"])
        if not file_exists:
            writer.writeheader()
        for msg in messages:
            writer.writerow({
                "timestamp": msg["time"],
                "role": msg["role"],
                "content": msg["content"]
            })

if st.session_state.messages:
    save_chat_history_csv(st.session_state.messages)

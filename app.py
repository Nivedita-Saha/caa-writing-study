import streamlit as st
import time
import os
import csv
import json
from datetime import datetime
from groq import Groq

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

import gspread
from google.oauth2.service_account import Credentials

# Connect to Google Sheets using the service account key.
@st.cache_resource
def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(
        ".streamlit/service_account.json", scopes=scopes
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(st.secrets["SHEET_ID"])
    worksheet = sh.sheet1
    # Add a header row once, if the sheet is empty.
    if worksheet.row_count == 0 or not worksheet.get_all_values():
        worksheet.append_row([
            "participant_id", "group", "start_time", "duration_seconds",
            "essay_word_count", "interaction_count", "essay_text",
            "conversation_json",
        ])
    return worksheet


DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Hide the Streamlit menu, toolbar, and footer for a clean study interface.
# This also removes the keyboard shortcuts that caused the clear cache popup.
st.set_page_config(page_title="CAA Writing Space", initial_sidebar_state="expanded")
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stToolbar"] {display: none;}

    /* Deeper warm terracotta-sand background across the whole page */
    .stApp {
        background: linear-gradient(135deg, #E8C9A8 0%, #DDB892 50%, #D4A276 100%);
    }

    /* Content card: warm cream, clearly sitting on the coloured page */
    .block-container {
        background-color: #FFF8EF;
        padding: 2.5rem 3rem;
        border-radius: 20px;
        max-width: 850px;
        margin-top: 2rem;
        box-shadow: 0 6px 30px rgba(120, 80, 50, 0.25);
    }

    h1, h2, h3 {
        color: #7A4E32 !important;
        font-family: "Georgia", serif;
    }

    p, label, span, div {
        color: #4A3F35;
    }

    /* Buttons: warm terracotta */
    .stButton > button {
        background-color: #C9805A;
        color: #FFFFFF;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1.2rem;
        font-weight: 600;
        transition: background-color 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #A85D3A;
        color: #FFFFFF;
    }

    /* Writing and input areas: warm cream, soft border */
    textarea, input {
        border-radius: 10px !important;
        border: 1px solid #D9C2A8 !important;
        background-color: #FFFDF8 !important;
    }

    /* Info and success boxes: warm tint */
    [data-testid="stAlert"] {
        border-radius: 12px;
        background-color: #F6E4CE !important;
    }

    /* The bottom chat bar: warm rather than grey */
    [data-testid="stChatInput"] {
        background-color: #FFF8EF !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


st.title("CAA Writing Space")

st.write("**Researcher: assign this participant to a group**")
mode = st.radio(
    label="Group",
    options=["Writing Helper", "Thinking Partner"],
    index=0,
    horizontal=True,
    label_visibility="collapsed",
)

st.session_state["mode"] = mode
st.divider()

participant_id = st.text_input(
    label="Participant ID",
    placeholder="e.g. P01",
)

if not participant_id:
    st.info("Please enter your Participant ID to begin.")
    st.stop()

st.session_state["participant_id"] = participant_id

if "start_time" not in st.session_state:
    st.session_state["start_time"] = time.time()
    st.session_state["start_time_readable"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

st.info(
    "How this works: this tool is here to help you think, not to do the work "
    "for you. Please write the essay in your own words. You can ask for help "
    "as you go. Your responses will be used for research and kept anonymous."
)

st.subheader("Essay question")
st.write(
    "Should students be allowed to use AI tools in their learning? "
    "Give your view and explain your reasons."
)

st.write("Write your essay in the box below. Take your time and think it through.")

essay = st.text_area(
    label="Your essay",
    height=300,
    placeholder="Start writing here...",
)

st.session_state["essay"] = essay

st.write("Word count:", len(essay.split()))

elapsed_seconds = int(time.time() - st.session_state["start_time"])
minutes, seconds = divmod(elapsed_seconds, 60)
st.write(f"Time on task so far: {minutes} min {seconds} sec")

st.divider()


NO_ANSWER_RULE = (
    "You are a THINKING PARTNER for a student writing an essay. "
    "You are allowed to answer a genuine FACTUAL question briefly, in at most "
    "two short sentences, to give the student a fact they are missing (for "
    "example a date, a definition, or a simple piece of background). "
    "But you must NEVER write any part of their essay, NEVER give sentences or "
    "paragraphs they could copy, NEVER list arguments or points for them, and "
    "NEVER state your own opinion on the essay topic. "
    "You do not answer the essay question itself and you do not take a side. "
    "Apart from brief facts, you help by asking questions and giving small "
    "hints that make the STUDENT think and produce their own ideas. "
    "If the student asks you to write the essay, to give arguments, to give "
    "their view, or to structure it for them, you must REFUSE and reply only "
    "with something like: 'I can't write that for you, but I can help you think "
    "it through. What is your own first reaction to the question?' "
    "IMPORTANT: Use very simple, plain English. Keep replies short and easy to "
    "understand. Never write more than two short sentences."
)

MEMORY_RULE = (
    " As you reply, pay close attention to the student's essay and to the "
    "earlier things they have said in this conversation. When it helps, gently "
    "remind them of one of their own earlier points and ask how their current "
    "thinking connects to it. Always build on what they have already written or "
    "said, so the conversation feels connected."
)


REQUEST_PATTERNS = [
    "write my essay", "write the essay", "write this essay", "write it for me",
    "write for me", "draft my essay", "draft the essay",
    "give me arguments", "give me points", "give arguments",
    "what should i write", "structure my essay", "structure the essay",
    "your opinion", "your view",
]


def looks_like_answer_request(text):
    lowered = text.lower()
    return any(p in lowered for p in REQUEST_PATTERNS)


FIXED_REFUSAL = (
    "I can't write that for you, but I can help you think it through. "
    "What is your own first reaction to the question?"
)


def reflection_prompt(current_essay):
    instruction = (
        NO_ANSWER_RULE
        + " Read what the student has written so far. Ask them ONE short, simple "
        "question that pushes them to think more deeply or see another side. "
        "Ask only the question, nothing else."
    )
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": instruction},
            {"role": "user", "content": f"Here is my essay so far: {current_essay}"},
        ],
        max_tokens=80,
    )
    return response.choices[0].message.content


def analogy_generate(concept):
    instruction = (
        NO_ANSWER_RULE
        + " The student names a concept they find hard. Offer ONE simple "
        "everyday analogy that helps them understand it, in plain English. "
        "Do not write essay text. Give only the analogy in one or two sentences."
    )
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": instruction},
            {"role": "user", "content": f"The concept I find hard is: {concept}"},
        ],
        max_tokens=100,
    )
    return response.choices[0].message.content


def writing_helper_reply(history):
    system = {
        "role": "system",
        "content": (
            "You are a helpful AI assistant supporting a student who is "
            "writing an essay. Answer their questions clearly and helpfully."
        ),
    }
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[system] + history,
        max_tokens=400,
    )
    return response.choices[0].message.content


def thinking_partner_reply(history, current_essay):
    if history and looks_like_answer_request(history[-1]["content"]):
        return FIXED_REFUSAL
    system = {
        "role": "system",
        "content": (
            NO_ANSWER_RULE
            + MEMORY_RULE
            + f" For context, here is the student's current essay: {current_essay}"
        ),
    }
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[system] + history,
        max_tokens=150,
    )
    return response.choices[0].message.content


def save_session():
    pid = st.session_state.get("participant_id", "unknown")
    grp = st.session_state.get("mode", "unknown")
    essay_text = st.session_state.get("essay", "")
    start_readable = st.session_state.get("start_time_readable", "")
    duration = int(time.time() - st.session_state["start_time"])
    word_count = len(essay_text.split())

    if grp == "Writing Helper":
        conversation = st.session_state.get("helper_messages", [])
    else:
        conversation = st.session_state.get("partner_messages", [])
    interaction_count = sum(1 for m in conversation if m["role"] == "user")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"{pid}_{stamp}"

    txt_path = os.path.join(DATA_DIR, base + ".txt")
    with open(txt_path, "w") as f:
        f.write(f"Participant ID: {pid}\n")
        f.write(f"Group: {grp}\n")
        f.write(f"Start time: {start_readable}\n")
        f.write(f"Duration (seconds): {duration}\n")
        f.write(f"Essay word count: {word_count}\n")
        f.write(f"Number of interactions: {interaction_count}\n")
        f.write("\n----- ESSAY -----\n")
        f.write(essay_text + "\n")
        f.write("\n----- CONVERSATION -----\n")
        for m in conversation:
            f.write(f"{m['role'].upper()}: {m['content']}\n")

    csv_path = os.path.join(DATA_DIR, "all_sessions.csv")
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "participant_id", "group", "start_time", "duration_seconds",
                "essay_word_count", "interaction_count", "essay_text",
                "conversation_json",
            ])
        writer.writerow([
            pid, grp, start_readable, duration, word_count, interaction_count,
            essay_text, json.dumps(conversation),
        ])

    # Also append this session as a row in the Google Sheet.
    try:
        worksheet = get_sheet()
        worksheet.append_row([
            pid, grp, start_readable, duration, word_count, interaction_count,
            essay_text, json.dumps(conversation),
        ])
        sheet_ok = True
    except Exception as e:
        sheet_ok = False
        st.session_state["sheet_error"] = str(e)

    return txt_path, csv_path


if mode == "Writing Helper":
    st.subheader("Writing Helper")
    st.write("Ask the assistant anything to help with your essay.")

    if "helper_messages" not in st.session_state:
        st.session_state["helper_messages"] = []

    for m in st.session_state["helper_messages"]:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    user_msg = st.chat_input("Type your question here...")
    if user_msg:
        st.session_state["helper_messages"].append({"role": "user", "content": user_msg})
        with st.spinner("Thinking..."):
            reply = writing_helper_reply(st.session_state["helper_messages"])
        st.session_state["helper_messages"].append({"role": "assistant", "content": reply})
        st.rerun()

else:
    st.subheader("Thinking Partner")
    st.write("Chat with your thinking partner as you write. Use the buttons for a quick nudge.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Reflection question"):
            if len(essay.split()) < 5:
                st.warning("Write a little more first.")
            else:
                with st.spinner("Thinking..."):
                    st.session_state["last_tool_output"] = reflection_prompt(essay)

    with col2:
        concept = st.text_input("Concept you find hard:", key="analogy_concept")
        if st.button("Give an analogy"):
            if not concept.strip():
                st.warning("Type a concept first.")
            else:
                with st.spinner("Thinking..."):
                    st.session_state["last_tool_output"] = analogy_generate(concept)

    if st.session_state.get("last_tool_output"):
        st.info(st.session_state["last_tool_output"])

    if "partner_messages" not in st.session_state:
        st.session_state["partner_messages"] = []

    for m in st.session_state["partner_messages"]:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    partner_msg = st.chat_input("Ask your thinking partner...")
    if partner_msg:
        st.session_state["partner_messages"].append({"role": "user", "content": partner_msg})
        with st.spinner("Thinking..."):
            reply = thinking_partner_reply(st.session_state["partner_messages"], essay)
        st.session_state["partner_messages"].append({"role": "assistant", "content": reply})
        st.rerun()

st.divider()

if st.button("Submit and save my work"):
    if len(essay.split()) < 5:
        st.warning("Please write your essay before submitting.")
    else:
        save_session()
        st.success("Your work has been saved. Thank you.")

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarize import summarise, title
from core.extractor import (
    extract_action_items,
    extract_key_decisions,
    extract_questions,
)
from core.rag import build_rag_chain, ask_question


# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="AI Video Assistant",
    page_icon="🎥",
    layout="wide",
)


# =====================================================
# CUSTOM CSS
# =====================================================

st.markdown("""
<style>

.block-container{
    padding-top:2rem;
    padding-bottom:2rem;
}

.hero-title{
    font-size:3.5rem;
    font-weight:800;
    text-align:center;
    background: linear-gradient(
        90deg,
        #00C6FF,
        #0072FF
    );
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
}

.hero-subtitle{
    text-align:center;
    color:#9CA3AF;
    margin-bottom:2rem;
}

.metric-card{
    padding:20px;
    border-radius:18px;
    background:#161B22;
    border:1px solid #2D333B;
}

.stTabs [data-baseweb="tab-list"]{
    gap:12px;
}

.stTabs [data-baseweb="tab"]{
    border-radius:12px;
    padding:10px 18px;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# SESSION STATE
# =====================================================

if "result" not in st.session_state:
    st.session_state.result = None

if "rag_chain" not in st.session_state:
    st.session_state.rag_chain = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# =====================================================
# HEADER
# =====================================================

st.markdown(
    """
    <div class="hero-title">
        🎥 AI Video Assistant
    </div>

    <div class="hero-subtitle">
        Transcribe • Summarize • Extract Insights • Chat with Videos
    </div>
    """,
    unsafe_allow_html=True
)


# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.title("⚙️ Controls")

    source = st.text_input(
        "YouTube URL / Local File Path",
        placeholder="https://youtube.com/watch?v=..."
    )

    language = st.selectbox(
        "Language",
        ["english", "hinglish"]
    )

    run_btn = st.button(
        "🚀 Process Video",
        use_container_width=True
    )


# =====================================================
# PROCESS
# =====================================================

if run_btn:

    if not source:
        st.warning("Please enter a source.")
        st.stop()

    with st.status(
        "Processing Video...",
        expanded=True
    ) as status:

        status.write("🎵 Extracting audio...")
        chunks = process_input(source)

        status.write("📝 Generating transcript...")
        transcript = transcribe_all(
            chunks,
            language
        )

        status.write("📌 Generating title...")
        generated_title = title(transcript)

        status.write("📋 Generating summary...")
        summary = summarise(transcript)

        status.write("✅ Extracting action items...")
        actions = extract_action_items(transcript)

        status.write("🔑 Extracting decisions...")
        decisions = extract_key_decisions(transcript)

        status.write("❓ Extracting questions...")
        questions = extract_questions(transcript)

        status.write("🧠 Building RAG index...")
        rag_chain = build_rag_chain(transcript)

        status.update(
            label="Processing Complete!",
            state="complete"
        )

    st.session_state.result = {
        "title": generated_title,
        "transcript": transcript,
        "summary": summary,
        "actions": actions,
        "decisions": decisions,
        "questions": questions,
    }

    st.session_state.rag_chain = rag_chain


# =====================================================
# RESULTS
# =====================================================

if st.session_state.result:

    result = st.session_state.result

    st.success("Video processed successfully.")

    st.markdown(
        f"## 📌 {result['title']}"
    )

    # =========================================
    # METRICS
    # =========================================

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Words",
            len(result["transcript"].split())
        )

    with c2:
        st.metric(
            "Action Items",
            len(str(result["actions"]).split("\n"))
        )

    with c3:
        st.metric(
            "Questions",
            len(str(result["questions"]).split("\n"))
        )

    with c4:
        st.metric(
            "Decisions",
            len(str(result["decisions"]).split("\n"))
        )

    st.divider()

    # =========================================
    # DOWNLOADS
    # =========================================

    d1, d2 = st.columns(2)

    with d1:
        st.download_button(
            "📥 Download Summary",
            result["summary"],
            file_name="summary.txt"
        )

    with d2:
        st.download_button(
            "📥 Download Transcript",
            result["transcript"],
            file_name="transcript.txt"
        )

    st.divider()

    # =========================================
    # TABS
    # =========================================

    summary_tab, transcript_tab, actions_tab, decisions_tab, questions_tab = st.tabs(
        [
            "📋 Summary",
            "📝 Transcript",
            "✅ Actions",
            "🔑 Decisions",
            "❓ Questions"
        ]
    )

    with summary_tab:
        st.markdown(result["summary"])

    with transcript_tab:

        with st.expander(
            "View Transcript",
            expanded=True
        ):
            st.write(result["transcript"])

    with actions_tab:
        st.markdown(result["actions"])

    with decisions_tab:
        st.markdown(result["decisions"])

    with questions_tab:
        st.markdown(result["questions"])

    st.divider()

    # =========================================
    # CHAT
    # =========================================

    st.subheader("💬 Chat With Video")

    for message in st.session_state.chat_history:

        with st.chat_message(
            message["role"]
        ):
            st.markdown(
                message["content"]
            )

    query = st.chat_input(
        "Ask anything about the video..."
    )

    if query:

        st.session_state.chat_history.append(
            {
                "role": "user",
                "content": query
            }
        )

        with st.chat_message("user"):
            st.markdown(query)

        with st.chat_message("assistant"):

            with st.spinner("Thinking..."):

                answer = ask_question(
                    st.session_state.rag_chain,
                    query
                )

                st.markdown(answer)

        st.session_state.chat_history.append(
            {
                "role": "assistant",
                "content": answer
            }
        )
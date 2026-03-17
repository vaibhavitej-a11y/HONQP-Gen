import streamlit as st
from generator import generate_questions

def _render_card(item: dict, index: int) -> None:
    q = item.get("question", "")
    a = item.get("answer", "")

    st.markdown(
        f"""
        <div style="
            background-color: white;
            padding: 24px;
            border-radius: 16px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            margin-bottom: 20px;
            border: 1px solid #f0f0f0;
        ">
            <div style="color: #666; font-size: 0.9rem; margin-bottom: 8px; font-weight: 600;">Question {index + 1}</div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #1a1a1a; margin-bottom: 12px;">{q}</div>
            <div style="background-color: #f8f9fa; padding: 12px 16px; border-radius: 12px; border-left: 4px solid #3b82f6;">
                <span style="font-weight: 700; color: #4b5563; font-size: 0.9rem; display: block; margin-bottom: 4px;">Answer</span>
                <span style="color: #1a1a1a;">{a}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def main() -> None:
    st.set_page_config(page_title="HONQPGen", page_icon="🤖", layout="centered")

    # Hide default menu
    hide_menu = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Overall Style */
    .stApp {
        background-color: #fcfcfc;
        color: #1a1a1a;
    }

    /* Headers and Labels Contrast */
    h1, h2, h3, h4, h5, p, span, label {
        color: #1e293b !important;
    }
    
    /* Slider Labels specific fix */
    .stSlider label, .stSlider div[data-testid="stMarkdownContainer"] p {
        color: #1e293b !important;
        font-weight: 700 !important;
    }

    /* Help icons */
    .stSlider button[aria-label="Selected value"] {
        color: #3b82f6 !important;
    }
    
    /* Rounded corners and padding */
    .stTextArea textarea {
        background-color: white !important;
        color: #1a1a1a !important;
        border-radius: 12px !important;
        border: 1px solid #e2e8f0 !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 1px #3b82f6 !important;
    }
    
    /* Custom button styling */
    div.stButton > button {
        background-color: #ff6b6b !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        font-weight: 700 !important;
        transition: all 0.3s ease !important;
        white-space: nowrap !important;
    }
    div.stButton > button:hover {
        background-color: #ff5252 !important;
        box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Spacing */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 4rem !important;
    }

    /* Slider styling */
    .stSlider > div [data-baseweb="slider"] {
        margin-top: 10px;
    }
    </style>
    """
    st.markdown(hide_menu, unsafe_allow_html=True)

    # Top Bar
    t1, t2 = st.columns([3, 1])
    with t1:
        st.markdown("<h3 style='margin-top: 0; color: #1e293b; font-weight: 800;'>HONQPGen 🤖</h3>", unsafe_allow_html=True)
    with t2:
        col1, col2 = st.columns(2)
        with col1:
             if st.button("📤 Share", use_container_width=True):
                 st.toast("Link copied!")
        with col2:
             if st.button("❓ Help", use_container_width=True):
                 st.info("Paste an educational paragraph, set the parameters, and click Generate!")

    st.markdown("<hr style='margin: 10px 0 30px 0; opacity: 0.1;'>", unsafe_allow_html=True)

    # Section 1: Hero
    st.markdown(
        """
        <div style='text-align: center; margin-bottom: 40px;'>
            <h1 style='font-size: 3.5rem; font-weight: 900; color: #1e293b; margin-bottom: 10px;'>HONQPGen 🤖</h1>
            <p style='font-size: 1.25rem; color: #64748b; margin-bottom: 30px;'>
                <b style='color: #334155;'>Hands-On AI-Based Question Generation System</b><br>
                Instant, high-quality question generation from your educational content
            </p>
            <div style='display: flex; justify-content: center; gap: 20px; font-weight: 700; color: #3b82f6; font-size: 1.1rem;'>
                <span>📝 Paste Text</span> <span style='color: #cbd5e1;'>➔</span> <span>🧠 AI Reads It</span> <span style='color: #cbd5e1;'>➔</span> <span>❓ Get Questions</span>
            </div>
        </div>
        <hr style='margin: 30px 0; opacity: 0.1;'>
        """,
        unsafe_allow_html=True
    )

    # Section 2: Input Area
    st.markdown("#### **Your Paragraph**")
    text = st.text_area(
        label="none",
        label_visibility="collapsed",
        height=200,
        placeholder="Example: The solar system consists of the Sun and the objects that orbit it...",
    )

    st.write("")
    st.markdown("##### **Generation Parameters**")
    c1, c2 = st.columns(2)
    with c1:
        max_questions = st.slider("**Total Questions**", 1, 30, 10, help="Specify the maximum number of questions to generate.")
    with c2:
        max_keywords = st.slider("**Keywords Analysis**", 1, 50, 12, help="Set the depth of keyword extraction from your text.")

    st.write("")
    generate = st.button("🚀 Generate Questions", use_container_width=True)

    # Section 3: Output Area
    if generate:
        if not text.strip():
            st.warning("Please paste a paragraph first.")
            return

        with st.spinner("Generating questions... (this may take a few seconds)"):
            try:
                items = generate_questions(text, max_questions=int(max_questions), max_keywords=int(max_keywords))
            except Exception as e:
                st.error(f"Error: {str(e)}")
                return

        if not items:
            st.info("No questions generated. Try a longer paragraph.")
            return

        st.success(f"Generated {len(items)} questions!")
        st.write("")
        
        for i, item in enumerate(items):
            _render_card(item, i)

if __name__ == "__main__":
    main()


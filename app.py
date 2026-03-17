import streamlit as st

from generator import generate_questions


def _render_card(item: dict, index: int) -> None:
    q = item.get("question", "")
    a = item.get("answer", "")
    qtype = item.get("type", "Descriptive")
    options = item.get("options", [])
    fib = item.get("fill_in_blank", None)

    st.markdown(
        f"""
        <div style="
            border: 1px solid rgba(0,0,0,0.08);
            border-radius: 14px;
            padding: 16px 16px 14px 16px;
            margin: 12px 0;
            background: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        ">
            <div style="display:flex; justify-content:space-between; align-items:center; gap:12px;">
                <div style="font-size:14px; font-weight:700;">Q{index + 1}</div>
                <div style="
                    font-size:12px;
                    font-weight:700;
                    padding: 4px 10px;
                    border-radius: 999px;
                    background: rgba(99, 102, 241, 0.10);
                    color: rgb(67, 56, 202);
                    border: 1px solid rgba(99, 102, 241, 0.25);
                ">{qtype}</div>
            </div>
            <div style="margin-top:10px; font-size:16px; line-height:1.45;"><b>{q}</b></div>
            <div style="margin-top:10px; font-size:14px;">
                <span style="font-weight:700;">Answer:</span>
                <span>{a}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if qtype == "MCQ" and isinstance(options, list) and options:
        st.write("**Options:**")
        for opt in options:
            st.write(f"- {opt}")

    if fib:
        with st.expander("Fill in the blank version"):
            st.write(fib)


def main() -> None:
    st.set_page_config(page_title="HONQPGen", page_icon="❓", layout="centered")

    st.markdown(
        """
        <div style="margin-bottom: 10px;">
            <div style="font-size: 30px; font-weight: 800;">HONQPGen</div>
            <div style="color: rgba(0,0,0,0.62); margin-top: 2px;">
                AI-based question generation (SpaCy keywords + T5 QG-HL).
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    text = st.text_area(
        "Paste a paragraph",
        height=180,
        placeholder="Example: Albert Einstein was a theoretical physicist who developed the theory of relativity...",
    )

    cols = st.columns([1, 1, 2])
    with cols[0]:
        max_questions = st.number_input("Max questions", min_value=1, max_value=30, value=10, step=1)
    with cols[1]:
        max_keywords = st.number_input("Max keywords", min_value=1, max_value=50, value=12, step=1)
    with cols[2]:
        st.write("")
        st.write("")
        generate = st.button("Generate Questions", type="primary", use_container_width=True)

    if generate:
        if not text.strip():
            st.warning("Please paste a paragraph first.")
            return

        with st.spinner("Generating questions... (first run may download models)"):
            try:
                items = generate_questions(text, max_questions=int(max_questions), max_keywords=int(max_keywords))
            except Exception as e:
                st.error(str(e))
                st.info(
                    "If this is a fresh environment, install dependencies and the SpaCy model:\n\n"
                    "- `pip install -r requirements.txt`\n"
                    "- `python -m spacy download en_core_web_sm`"
                )
                return

        if not items:
            st.info("No questions generated. Try a longer paragraph.")
            return

        st.markdown("### Results")
        for i, item in enumerate(items):
            _render_card(item, i)


if __name__ == "__main__":
    main()


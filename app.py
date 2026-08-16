"""Answer Feedback Tutor.

A single-page Streamlit app that:
1. Takes a student's typed answer to a preset question.
2. Grades it against a rubric using a local LLM (Ollama).
3. Turns the missed points into an image prompt and generates a study
   diagram using a local Stable Diffusion instance (AUTOMATIC1111 API).
4. Displays the text feedback and the generated image together.

Run with: streamlit run app.py
"""

import streamlit as st

from src.grading import grade_answer
from src.image_gen import build_image_prompt, generate_image
from src.utils import load_rubrics

st.set_page_config(page_title="Answer Feedback Tutor", page_icon="📝", layout="centered")

st.title("📝 Answer Feedback Tutor")
st.caption(
    "Local LLM grading + local image generation, running fully on your machine "
    "(no cloud APIs)."
)

rubrics = load_rubrics()
questions_by_id = {r["id"]: r for r in rubrics}

question_choice = st.selectbox(
    "Choose a question",
    options=list(questions_by_id.keys()),
    format_func=lambda qid: questions_by_id[qid]["question"],
)

selected = questions_by_id[question_choice]
st.markdown(f"**Question:** {selected['question']}")

student_answer = st.text_area("Type your answer here", height=200)

if st.button("Grade my answer", type="primary"):
    if not student_answer.strip():
        st.error("Please type an answer before submitting.")
    else:
        with st.spinner("Grading with local LLM..."):
            try:
                result = grade_answer(
                    question=selected["question"],
                    key_points=selected["key_points"],
                    student_answer=student_answer,
                )
            except (RuntimeError, ValueError) as exc:
                st.error(str(exc))
                st.stop()

        st.subheader(f"Score: {result['score']}/100")
        st.write(result["summary"])

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("✅ **Covered points**")
            for point in result["covered_points"]:
                st.markdown(f"- {point}")
        with col2:
            st.markdown("❌ **Missed points**")
            for point in result["missed_points"]:
                st.markdown(f"- {point}")

        if result["missed_points"]:
            with st.spinner("Generating a study diagram for what you missed..."):
                prompt = build_image_prompt(result["missed_points"], topic=selected["question"])
                try:
                    image_path = generate_image(prompt, filename_prefix=selected["id"])
                except RuntimeError as exc:
                    st.warning(str(exc))
                    image_path = None

            if image_path:
                st.subheader("Study diagram for what you missed")
                st.image(str(image_path))
        else:
            st.success("You covered every key point — no gaps to illustrate!")

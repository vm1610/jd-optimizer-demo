import streamlit as st
import anthropic
import json

st.set_page_config(page_title="JD Optimizer", page_icon="⚡", layout="wide")

st.markdown("""
<style>
  .block-container { padding-top: 2rem; }
  .tag { display:inline-block; background:#e8f0fe; color:#1a56db; border-radius:4px;
         padding:2px 10px; margin:3px; font-size:0.82rem; font-weight:600; }
  .bias-tag { background:#fde8e8; color:#c81e1e; }
  .section-label { font-size:0.75rem; font-weight:700; letter-spacing:1.5px;
                   text-transform:uppercase; color:#6b7280; margin-bottom:0.4rem; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ JD Optimizer")
st.caption("Paste a job description — get a rewrite, skill breakdown, and bias report instantly.")

try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except Exception:
    import os
    api_key = os.getenv("ANTHROPIC_API_KEY", "")

if not api_key:
    st.error("ANTHROPIC_API_KEY not set. Add it to Streamlit secrets.")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

SAMPLE_JD = """Software Engineer – Full Stack

We are looking for a rockstar ninja developer who can hit the ground running.
The ideal candidate is a young, energetic self-starter with 10+ years of experience in React and Node.js.

Responsibilities:
- Build and maintain web applications
- Work with the team to deliver features
- Write clean code

Requirements:
- BS/MS in Computer Science preferred
- Strong communication skills
- Experience with AWS
- Must be available nights and weekends when needed
"""

with st.sidebar:
    st.markdown("### Settings")
    tone = st.selectbox("Target tone", ["Professional", "Inclusive & Modern", "Startup", "Corporate"])
    show_sample = st.button("Load sample JD")

jd_input = st.text_area(
    "Paste your Job Description here",
    value=SAMPLE_JD if "load_sample" in st.session_state and st.session_state.load_sample else "",
    height=280,
    placeholder="Paste any job description..."
)

if show_sample:
    st.session_state.load_sample = True
    st.rerun()

run = st.button("⚡ Optimize", type="primary", disabled=not jd_input.strip())

if run and jd_input.strip():
    prompt = f"""You are an expert HR consultant and technical recruiter. Analyze this job description and return a JSON object with exactly these keys:

1. "rewritten_jd": A rewritten version of the JD that is clear, inclusive, and realistic. Fix vague language, remove bias, make requirements reasonable. Tone: {tone}.
2. "technical_skills": Array of specific technical skills/tools mentioned or implied (strings).
3. "soft_skills": Array of soft skills mentioned or implied (strings).
4. "bias_flags": Array of objects with "phrase" (the problematic text) and "reason" (why it's problematic).
5. "summary": 2-sentence summary of what was improved.

Job Description:
{jd_input}

Return only valid JSON, no markdown, no extra text."""

    with st.spinner("Analyzing and rewriting..."):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        st.error("Couldn't parse response. Try again.")
        st.stop()

    st.success(data.get("summary", ""))
    st.divider()

    tab1, tab2, tab3 = st.tabs(["✍️ Rewritten JD", "🛠 Skills", "⚠️ Bias Report"])

    with tab1:
        st.markdown('<div class="section-label">Optimized Job Description</div>', unsafe_allow_html=True)
        st.text_area("", value=data.get("rewritten_jd", ""), height=400, label_visibility="collapsed")
        st.download_button("Download rewritten JD", data.get("rewritten_jd", ""), "optimized_jd.txt")

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="section-label">Technical Skills</div>', unsafe_allow_html=True)
            tags = "".join(f'<span class="tag">{s}</span>' for s in data.get("technical_skills", []))
            st.markdown(tags, unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="section-label">Soft Skills</div>', unsafe_allow_html=True)
            tags = "".join(f'<span class="tag">{s}</span>' for s in data.get("soft_skills", []))
            st.markdown(tags, unsafe_allow_html=True)

    with tab3:
        flags = data.get("bias_flags", [])
        if not flags:
            st.success("No bias detected in this JD.")
        else:
            st.markdown(f'<div class="section-label">{len(flags)} issue{"s" if len(flags) != 1 else ""} found</div>', unsafe_allow_html=True)
            for f in flags:
                with st.expander(f"❌ \"{f.get('phrase', '')}\""):
                    st.write(f.get("reason", ""))

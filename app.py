import streamlit as st
import json
import os
import uuid
from datetime import datetime

from rag_pipeline import answer_query

# ----------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Nutrify — AI Nutrition & Recipe Assistant",
    page_icon="🥗",
    layout="wide",
)

# ----------------------------------------------------------------------
# PERSISTENT CHAT HISTORY (stored on disk as JSON)
# ----------------------------------------------------------------------
HISTORY_FILE = "data/chat_sessions.json"


def load_sessions():
    if not os.path.exists(HISTORY_FILE):
        return {"sessions": []}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"sessions": []}


def save_sessions(data):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def upsert_session(session_id, title, messages):
    data = load_sessions()
    sessions = data["sessions"]
    existing = next((s for s in sessions if s["id"] == session_id), None)
    if existing:
        existing["title"] = title
        existing["messages"] = messages
    else:
        sessions.insert(
            0,
            {
                "id": session_id,
                "title": title,
                "created": datetime.now().isoformat(),
                "messages": messages,
            },
        )
    save_sessions(data)


def get_current_session(session_id):
    data = load_sessions()
    return next((s for s in data["sessions"] if s["id"] == session_id), None)


# ----------------------------------------------------------------------
# SESSION STATE INIT
# ----------------------------------------------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

# ----------------------------------------------------------------------
# QUESTION CLASSIFICATION (for category badges + follow-ups)
# ----------------------------------------------------------------------
DISEASE_KEYWORDS = [
    "diabet", "pcos", "thyroid", "anemia", "anaemia", "liver", "heart disease",
    "hypertension", "blood pressure", "cholesterol", "kidney", "obesity",
]
RECIPE_KEYWORDS = [
    "recipe", "how to make", "how do i make", "cook", "dish", "meal idea",
    "ingredients for",
]
GUIDELINE_KEYWORDS = [
    "guideline", "how much", "daily intake", "recommended", "should i eat",
    "is it healthy", "benefits of", "good for", "healthy diet",
]


def classify_question(q):
    ql = q.lower()
    if any(k in ql for k in DISEASE_KEYWORDS):
        return "disease", "Health Condition", "cat-disease"
    if any(k in ql for k in RECIPE_KEYWORDS):
        return "recipe", "Recipe", "cat-recipe"
    if any(k in ql for k in GUIDELINE_KEYWORDS):
        return "guideline", "Nutrition Guidance", "cat-guideline"
    return "general", "General", "cat-general"


FOLLOWUPS = {
    "disease": [
        "What foods should I avoid?",
        "Any recipe suggestions for this condition?",
        "How much of this nutrient do I need daily?",
    ],
    "recipe": [
        "Is this recipe good for weight loss?",
        "What are the health benefits of the main ingredient?",
        "Suggest a similar recipe with less oil",
    ],
    "guideline": [
        "Give me a recipe that fits this guideline",
        "What foods are highest in this nutrient?",
        "Is this different for people with diabetes?",
    ],
    "general": [
        "Can you suggest a recipe using this?",
        "What are the nutritional benefits?",
        "Is this suitable for a diabetic diet?",
    ],
}

SAMPLE_QUESTIONS = {
    "🍳 Recipes": [
        "Give me a high-protein Indian breakfast recipe",
        "Ragi recipe for dinner",
        "Quick North Indian dal recipe",
        "Low-oil paneer recipe",
    ],
    "🥦 Nutrition": [
        "Is avocado good for weight loss?",
        "Benefits of coconut water",
        "What are alkaline foods?",
        "Foods high in iron",
    ],
    "❤️ Health Guidelines": [
        "What should I eat if I have high blood pressure?",
        "Diet tips for PCOS",
        "Foods good for thyroid health",
        "How to manage diabetes through diet?",
    ],
}

# ----------------------------------------------------------------------
# CSS — modern hero with rotating health-image background
# ----------------------------------------------------------------------
HERO_IMAGES = [
    "https://images.unsplash.com/photo-1490645935967-10de6ba17061?auto=format&fit=crop&w=1600&q=80",
    "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=1600&q=80",
    "https://images.unsplash.com/photo-1498837167922-ddd27525d352?auto=format&fit=crop&w=1600&q=80",
    "https://images.unsplash.com/photo-1490818387583-1baba5e638af?auto=format&fit=crop&w=1600&q=80",
]

hero_slides_css = ""
hero_slides_html = ""
n = len(HERO_IMAGES)
slide_duration = 24  # seconds for a full cycle
each = slide_duration / n
for i, url in enumerate(HERO_IMAGES):
    delay = i * each
    hero_slides_css += f"""
    .bg-slide-{i} {{
        background-image: linear-gradient(180deg, rgba(15,15,15,0.35) 0%, rgba(15,15,15,0.35) 45%, rgba(15,15,15,0.8) 100%), url('{url}');
        animation-delay: {delay}s;
    }}
    """
    hero_slides_html += f'<div class="bg-slide bg-slide-{i}"></div>'

keyframe_steps = ""
fade_frac = 0.06  # fraction of cycle spent fading in/out
hold_frac = (1.0 / n) - fade_frac
pct_in = round(fade_frac * 100 / (1), 2)
# Build a simple 4-step keyframe (works well for n=4): fade in, hold, fade out, hidden
keyframes = f"""
@keyframes heroCycle {{
  0% {{ opacity: 0; transform: scale(1.06); }}
  4% {{ opacity: 1; transform: scale(1.06); }}
  {round(100/n - 4,2)}% {{ opacity: 1; transform: scale(1.12); }}
  {round(100/n,2)}% {{ opacity: 0; transform: scale(1.12); }}
  100% {{ opacity: 0; }}
}}
"""

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&family=Work+Sans:wght@400;500;600;700&display=swap');

:root {{
    --pink: #D6336C;
    --pink-deep: #8C1F52;
    --green-deep: #1F4D3A;
    --green-bright: #4CA771;
    --mustard: #F2B705;
    --chili: #E8482C;
    --cream: #FFF7EA;
    --ink: #241A15;
}}

html, body, [class*="css"] {{
    font-family: 'Work Sans', sans-serif;
}}

.stApp {{
    background: var(--cream);
}}

/* ---------------- HERO ---------------- */
.hero-wrap {{
    position: relative;
    width: 100%;
    min-height: 300px;
    border-radius: 26px;
    overflow: hidden;
    margin-bottom: 1.4rem;
    box-shadow: 0 10px 30px rgba(36,26,21,0.25);
}}

.bg-slide {{
    position: absolute;
    inset: 0;
    background-size: cover;
    background-position: center;
    opacity: 0;
    animation: heroCycle {slide_duration}s infinite;
}}

{keyframes}
{hero_slides_css}

.hero-content {{
    position: relative;
    z-index: 2;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    min-height: 300px;
    padding: 2.2rem 2.4rem 1.8rem 2.4rem;
}}

.hero-eyebrow {{
    display: inline-block;
    background: var(--mustard);
    color: var(--ink);
    font-family: 'Fredoka', sans-serif;
    font-weight: 600;
    font-size: 0.8rem;
    padding: 0.25rem 0.9rem;
    border-radius: 999px;
    transform: rotate(-2deg);
    width: fit-content;
    margin-bottom: 0.7rem;
    box-shadow: 3px 3px 0 rgba(0,0,0,0.25);
}}

.hero-content h1.hero-title {{
    font-family: 'Fredoka', sans-serif !important;
    font-weight: 700 !important;
    font-size: 2.5rem !important;
    color: #FFFFFF !important;
    text-shadow: 0 2px 4px rgba(0,0,0,0.85), 0 4px 20px rgba(0,0,0,0.6) !important;
    line-height: 1.1 !important;
    margin: 0 0 0.4rem 0 !important;
}}

.hero-content p.hero-sub {{
    font-family: 'Work Sans', sans-serif !important;
    font-size: 1.02rem !important;
    color: #FFFFFF !important;
    text-shadow: 0 1px 3px rgba(0,0,0,0.8), 0 2px 10px rgba(0,0,0,0.5) !important;
    max-width: 640px;
    margin: 0 !important;
}}

/* ---------------- SIDEBAR ---------------- */
[data-testid="stSidebar"] {{
    background: var(--green-deep);
}}
[data-testid="stSidebar"] * {{
    color: var(--cream) !important;
}}
[data-testid="stSidebar"] .element-container {{
    margin-bottom: 0.25rem !important;
}}
div[data-testid="stVerticalBlock"] {{
    gap: 0.35rem !important;
}}
[data-testid="stSidebar"] button {{
    background: rgba(255,247,234,0.08) !important;
    border: 1px solid rgba(255,247,234,0.18) !important;
    border-radius: 10px !important;
    text-align: left !important;
}}
[data-testid="stSidebar"] button:hover {{
    background: rgba(255,247,234,0.18) !important;
    border-color: var(--mustard) !important;
}}

/* ---------------- CHAT BUBBLES ---------------- */
[data-testid="stChatMessage"] {{
    background: #FFFFFF;
    border-radius: 16px;
    border: 1px solid rgba(36,26,21,0.08);
    box-shadow: 0 2px 10px rgba(36,26,21,0.06);
}}

/* ---------------- BADGES ---------------- */
.cat-badge {{
    display: inline-block;
    font-family: 'Fredoka', sans-serif;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 0.15rem 0.6rem;
    border-radius: 999px;
    margin-bottom: 0.5rem;
}}
.cat-recipe {{ background: #FDE6C8; color: #8C4A0F; }}
.cat-guideline {{ background: #DDEFE0; color: var(--green-deep); }}
.cat-disease {{ background: #FBE0E6; color: var(--pink-deep); }}
.cat-general {{ background: #EAE6F5; color: #4A2E8C; }}

/* ---------------- ONBOARDING CARDS ---------------- */
.onboard-card {{
    background: #FFFFFF;
    border-radius: 16px;
    padding: 1.1rem 1.2rem;
    border: 1px solid rgba(36,26,21,0.08);
    box-shadow: 4px 4px 0 rgba(232,72,44,0.12);
    height: 100%;
}}
.onboard-emoji {{ font-size: 1.6rem; }}
.onboard-title {{
    font-family: 'Fredoka', sans-serif;
    font-weight: 600;
    color: var(--ink);
    margin: 0.3rem 0 0.2rem 0;
}}
.onboard-text {{
    font-size: 0.88rem;
    color: #5B4A3F;
    margin: 0;
}}

/* ---------------- FOLLOW-UP CHIPS ---------------- */
.stButton>button {{
    border-radius: 999px !important;
}}

/* ---------------- CHAT INPUT ---------------- */
[data-testid="stChatInput"] {{
    background: #FFFFFF !important;
    border: 1px solid rgba(36,26,21,0.15) !important;
    border-radius: 14px !important;
}}
[data-testid="stChatInput"] textarea {{
    color: var(--ink) !important;
    background: #FFFFFF !important;
}}
[data-testid="stChatInput"] textarea::placeholder {{
    color: #8A7A6D !important;
    opacity: 1 !important;
}}
[data-testid="stChatInput"] button {{
    background: var(--chili) !important;
}}
[data-testid="stChatInput"] button svg {{
    fill: #FFFFFF !important;
}}
</style>
""",
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🥗 Nutrify")

    if st.button("➕ New chat", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("**Past conversations**")

    data = load_sessions()
    sessions = data.get("sessions", [])
    if not sessions:
        st.caption("No conversations yet")
    else:
        for s in sessions[:20]:
            label = s["title"][:34] + ("…" if len(s["title"]) > 34 else "")
            if st.button(label, key=f"hist_{s['id']}", use_container_width=True):
                st.session_state.session_id = s["id"]
                st.session_state.messages = s["messages"]
                st.rerun()

    st.markdown("---")
    st.markdown("**Try asking**")
    tabs = st.tabs(list(SAMPLE_QUESTIONS.keys()))
    for tab, (cat, questions) in zip(tabs, SAMPLE_QUESTIONS.items()):
        with tab:
            for q in questions:
                if st.button(q, key=f"sample_{q}", use_container_width=True):
                    st.session_state.pending_question = q

    st.markdown("---")
    with st.expander("About this project"):
        st.markdown(
            "Nutrify is a retrieval-augmented assistant that answers "
            "questions about recipes, everyday nutrition, and general "
            "health guidelines. It retrieves relevant information before "
            "generating an answer, and always encourages checking with a "
            "healthcare professional for personal medical advice."
        )

    if st.session_state.messages:
        if st.button("🗑️ Clear conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

# ----------------------------------------------------------------------
# HERO
# ----------------------------------------------------------------------
st.markdown(
    f"""
<div class="hero-wrap">
    {hero_slides_html}
    <div class="hero-content">
        <span class="hero-eyebrow">AI Nutrition & Recipe Assistant</span>
        <h1 class="hero-title">Nutrify</h1>
        <p class="hero-sub">Ask about recipes, nutrition, or general health guidelines — grounded in retrieved sources, not a substitute for medical advice.</p>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------
# ONBOARDING (only when no messages yet)
# ----------------------------------------------------------------------
if not st.session_state.messages:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """<div class="onboard-card">
            <div class="onboard-emoji">🍳</div>
            <p class="onboard-title">Recipes</p>
            <p class="onboard-text">Ask for a dish by name, ingredient, or cuisine — Indian and international recipes included.</p>
            </div>""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """<div class="onboard-card">
            <div class="onboard-emoji">🥦</div>
            <p class="onboard-title">Nutrition</p>
            <p class="onboard-text">Ask what a food is good for, how much of something you need, or general healthy-eating questions.</p>
            </div>""",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """<div class="onboard-card">
            <div class="onboard-emoji">❤️</div>
            <p class="onboard-title">Health Guidelines</p>
            <p class="onboard-text">Ask about eating well with diabetes, PCOS, thyroid issues, anemia, heart health, and more.</p>
            </div>""",
            unsafe_allow_html=True,
        )
    st.markdown("")

# ----------------------------------------------------------------------
# CHAT HISTORY DISPLAY
# ----------------------------------------------------------------------
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🌿"):
        if msg["role"] == "assistant" and "badge_label" in msg:
            st.markdown(
                f'<span class="cat-badge {msg["badge_class"]}">{msg["badge_label"]}</span>',
                unsafe_allow_html=True,
            )
        st.markdown(msg["content"])

        # Follow-up chips only after the most recent assistant message
        if (
            msg["role"] == "assistant"
            and i == len(st.session_state.messages) - 1
            and "cat_key" in msg
        ):
            st.markdown("**You might also ask:**")
            cols = st.columns(len(FOLLOWUPS[msg["cat_key"]]))
            for col, fq in zip(cols, FOLLOWUPS[msg["cat_key"]]):
                with col:
                    if st.button(fq, key=f"followup_{i}_{fq}"):
                        st.session_state.pending_question = fq

# ----------------------------------------------------------------------
# HANDLE INPUT (either typed or a clicked sample/follow-up question)
# ----------------------------------------------------------------------
typed = st.chat_input("Ask about a recipe, nutrient, or health guideline...")
question = st.session_state.pending_question or typed
st.session_state.pending_question = None

if question:
    cat_key, badge_label, badge_class = classify_question(question)

    st.session_state.messages.append({"role": "user", "content": question})

    with st.spinner("Thinking..."):
        answer = answer_query(question)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "cat_key": cat_key,
            "badge_label": badge_label,
            "badge_class": badge_class,
        }
    )

    title = st.session_state.messages[0]["content"]
    upsert_session(st.session_state.session_id, title, st.session_state.messages)

    st.rerun()

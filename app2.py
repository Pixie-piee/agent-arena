import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import json
import os
from dotenv import load_dotenv
load_dotenv()

st.write("API Key Loaded:", os.getenv("GEMINI_API_KEY"))

# ---- CONFIG ----
st.set_page_config(
    page_title="Agent Arena",
    page_icon="robot",
    layout="wide"
)

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ---- FAKE DATA ----
agents = [
    {"name": "Agent A (Claude)", "task": "Fix bug in Python repo", "status": "Pass", "steps": 12, "failure_type": "None", "time_taken": "45s"},
    {"name": "Agent B (GPT)", "task": "Fix bug in Python repo", "status": "Fail", "steps": 24, "failure_type": "Looping", "time_taken": "120s"},
    {"name": "Agent C (Baseline)", "task": "Fix bug in Python repo", "status": "Fail", "steps": 8, "failure_type": "Early Exit", "time_taken": "20s"},
]

df = pd.DataFrame(agents)

traces = {
    "Agent A (Claude)": [
        "ls -la",
        "cat main.py",
        "python test.py",
        "nano main.py",
        "python test.py",
        "[PASS] Tests passed - task complete"
    ],
    "Agent B (GPT)": [
        "ls",
        "grep error main.py",
        "grep error main.py",
        "grep error main.py",
        "grep error main.py",
        "grep error main.py",
        "grep error main.py",
        "grep error main.py",
        "[FAIL] Exit without completing"
    ],
    "Agent C (Baseline)": [
        "ls",
        "cat main.py",
        "[FAIL] Exit without completing"
    ]
}

# ---- SIDEBAR ----
st.sidebar.title("Agent Arena")
st.sidebar.markdown("**Harbor Buildathon 2026**")
st.sidebar.divider()
st.sidebar.markdown("### About")
st.sidebar.info("Runs multiple AI agents on the same task and analyzes why they succeed or fail using Gemini AI.")
st.sidebar.divider()
total = len(df)
passed = len(df[df["status"] == "Pass"])
failed = len(df[df["status"] == "Fail"])
st.sidebar.metric("Total Agents", total)
st.sidebar.metric("Passed", passed)
st.sidebar.metric("Failed", failed)

# ---- MAIN PAGE ----
st.title("Agent Arena")
st.markdown("### AI Agent Comparison + Failure Analysis Dashboard")
st.markdown("*Powered by Harbor SDK + Gemini AI*")
st.divider()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Leaderboard", "Trajectory Viewer", "AI Analysis", "Upload Trajectory"])

# ---- TAB 1: LEADERBOARD ----
with tab1:
    st.markdown("### Agent Leaderboard")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Agents Tested", total)
    col2.metric("Tasks Run", 1)
    col3.metric("Pass Rate", f"{int((passed/total)*100)}%")
    col4.metric("Failures", failed)

    st.divider()
    st.dataframe(df, use_container_width=True)

    st.divider()
    st.markdown("### Failure Breakdown")
    failures = df[df["failure_type"] != "None"]
    fig = px.bar(
        failures,
        x="name",
        y="steps",
        color="failure_type",
        title="Failed Agents - Steps Taken vs Failure Type",
        color_discrete_sequence=["#FF4B4B", "#FFA500"]
    )
    st.plotly_chart(fig, use_container_width=True)

# ---- TAB 2: TRAJECTORY VIEWER ----
with tab2:
    st.markdown("### Trajectory Viewer")
    st.markdown("Select an agent to inspect every step it took.")

    selected_agent = st.selectbox("Select an agent:", list(traces.keys()))

    agent_data = df[df["name"] == selected_agent].iloc[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("Status", agent_data["status"])
    col2.metric("Total Steps", agent_data["steps"])
    col3.metric("Time Taken", agent_data["time_taken"])

    st.divider()
    st.markdown(f"**Steps taken by {selected_agent}:**")

    for i, step in enumerate(traces[selected_agent]):
        if "[FAIL]" in step:
            st.error(f"Step {i+1}: {step}")
        elif "[PASS]" in step:
            st.success(f"Step {i+1}: {step}")
        else:
            st.code(f"Step {i+1}: {step}")

# ---- HELPER FUNCTIONS ----
def run_gemini_analysis(trajectory_steps, agent_name="the agent"):
    """Run Gemini analysis and return parsed JSON result."""
    trajectory_text = "\n".join(trajectory_steps)

    prompt = f"""
You are an AI agent evaluator. Analyze this agent trajectory and diagnose the failure.

Trajectory:
{trajectory_text}

Respond ONLY with a valid JSON object. No extra text, no markdown, no code fences.
Use exactly these keys:
{{
  "failure_type": "one of: Looping, Early Exit, Wrong Approach, Hallucination, Permission Error, Timeout",
  "confidence": "a percentage like 92%",
  "root_cause": "one clear sentence explaining the core problem",
  "evidence": "one sentence pointing to specific steps that show the failure",
  "suggestion": "one sentence on what the agent should have done differently",
  "severity": "one of: Low, Medium, High, Critical"
}}
"""
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)

    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


def display_analysis_cards(result, agent_name):
    """Display parsed Gemini result as cards."""
    st.error("Failure Detected")
    st.divider()

    col1, col2, col3 = st.columns(3)
    col1.metric("Failure Type", result.get("failure_type", "Unknown"))
    col2.metric("Confidence", result.get("confidence", "N/A"))
    col3.metric("Severity", result.get("severity", "N/A"))

    st.divider()

    st.markdown("#### Root Cause")
    st.info(result.get("root_cause", "N/A"))

    st.markdown("#### Evidence")
    st.warning(result.get("evidence", "N/A"))

    st.markdown("#### Suggestion")
    st.success(result.get("suggestion", "N/A"))


# ---- TAB 3: AI ANALYSIS ----
with tab3:
    st.markdown("### AI Failure Analysis")
    st.markdown("Select a failed agent and click Analyze to get a diagnosis from Gemini.")

    failed_agents = df[df["status"] == "Fail"]["name"].tolist()
    selected_failed = st.selectbox("Select a failed agent:", failed_agents)

    if st.button(f"Analyze {selected_failed}"):
        with st.spinner("Gemini is analyzing the trajectory..."):
            try:
                result = run_gemini_analysis(traces[selected_failed], selected_failed)
                display_analysis_cards(result, selected_failed)
            except json.JSONDecodeError:
                st.error("Gemini returned an unexpected format. Try again.")
            except Exception as e:
                st.error(f"Something went wrong: {e}")

# ---- TAB 4: UPLOAD TRAJECTORY ----
with tab4:
    st.markdown("### Upload Your Own Trajectory")
    st.markdown("Paste a JSON trajectory or upload a `.json` file to analyze any agent run.")

    st.markdown("**Expected JSON format:**")
    st.code('''[
  "ls -la",
  "cat main.py",
  "python test.py",
  "grep error main.py",
  "grep error main.py",
  "[FAIL] Exit without completing"
]''', language="json")

    st.divider()

    input_method = st.radio("Input method:", ["Paste JSON", "Upload file"], horizontal=True)

    trajectory_input = None

    if input_method == "Paste JSON":
        raw_text = st.text_area("Paste your trajectory JSON here:", height=200, placeholder='["step 1", "step 2", "[FAIL] Exit without completing"]')
        if raw_text.strip():
            try:
                trajectory_input = json.loads(raw_text)
                if not isinstance(trajectory_input, list):
                    st.error("JSON must be a list of steps (strings).")
                    trajectory_input = None
                else:
                    st.success(f"Loaded {len(trajectory_input)} steps.")
            except json.JSONDecodeError:
                st.error("Invalid JSON. Check your formatting.")

    else:
        uploaded_file = st.file_uploader("Upload a JSON file:", type=["json"])
        if uploaded_file:
            try:
                trajectory_input = json.load(uploaded_file)
                if not isinstance(trajectory_input, list):
                    st.error("JSON must be a list of steps (strings).")
                    trajectory_input = None
                else:
                    st.success(f"Loaded {len(trajectory_input)} steps from file.")
            except Exception as e:
                st.error(f"Could not read file: {e}")

    if trajectory_input:
        st.divider()
        st.markdown("**Preview - steps in your trajectory:**")
        for i, step in enumerate(trajectory_input):
            if "[FAIL]" in str(step):
                st.error(f"Step {i+1}: {step}")
            elif "[PASS]" in str(step):
                st.success(f"Step {i+1}: {step}")
            else:
                st.code(f"Step {i+1}: {step}")

        st.divider()
        if st.button("Analyze This Trajectory"):
            with st.spinner("Gemini is analyzing..."):
                try:
                    result = run_gemini_analysis([str(s) for s in trajectory_input])
                    display_analysis_cards(result, "Uploaded Agent")
                except json.JSONDecodeError:
                    st.error("Gemini returned an unexpected format. Try again.")
                except Exception as e:
                    st.error(f"Something went wrong: {e}")
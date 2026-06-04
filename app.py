import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# ---- CONFIG ----
st.set_page_config(
    page_title="Agent Arena",
    page_icon="🤖",
    layout="wide"
)

import os
from dotenv import load_dotenv
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ---- FAKE DATA ----
agents = [
    {"name": "Agent A (Claude)", "task": "Fix bug in Python repo", "status": "✅ Pass", "steps": 12, "failure_type": "None", "time_taken": "45s"},
    {"name": "Agent B (GPT)", "task": "Fix bug in Python repo", "status": "❌ Fail", "steps": 24, "failure_type": "Looping", "time_taken": "120s"},
    {"name": "Agent C (Baseline)", "task": "Fix bug in Python repo", "status": "❌ Fail", "steps": 8, "failure_type": "Early Exit", "time_taken": "20s"},
]

df = pd.DataFrame(agents)

traces = {
    "Agent A (Claude)": [
        "ls -la",
        "cat main.py",
        "python test.py",
        "nano main.py",
        "python test.py",
        "✅ Tests passed - task complete"
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
        "❌ Exit without completing"
    ],
    "Agent C (Baseline)": [
        "ls",
        "cat main.py",
        "❌ Exit without completing"
    ]
}

# ---- SIDEBAR ----
st.sidebar.title("🤖 Agent Arena")
st.sidebar.markdown("**Harbor Buildathon 2026**")
st.sidebar.divider()
st.sidebar.markdown("### About")
st.sidebar.info("Runs multiple AI agents on the same task and analyzes why they succeed or fail using AI-powered trajectory analysis.")
st.sidebar.divider()
total = len(df)
passed = len(df[df["status"] == "✅ Pass"])
failed = len(df[df["status"] == "❌ Fail"])
st.sidebar.metric("Total Agents", total)
st.sidebar.metric("Passed", passed)
st.sidebar.metric("Failed", failed)

# ---- MAIN PAGE ----
st.title("🤖 Agent Arena")
st.markdown("### AI Agent Comparison + Failure Analysis Dashboard")
st.markdown("*Powered by Harbor SDK + Gemini AI*")
st.divider()

# Tabs
tab1, tab2, tab3 = st.tabs(["🏆 Leaderboard", "🔍 Trajectory Viewer", "🧠 AI Analysis"])

# ---- TAB 1: LEADERBOARD ----
with tab1:
    st.markdown("### Agent Leaderboard")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Agents Tested", total)
    col2.metric("Tasks Run", 1)
    col3.metric("Pass Rate", f"{int((passed/total)*100)}%")
    col4.metric("Failures", failed)
    
    st.divider()
    st.dataframe(df, width='stretch')
    
    st.divider()
    st.markdown("### Failure Breakdown")
    failures = df[df["failure_type"] != "None"]
    fig = px.bar(
        failures, 
        x="name", 
        y="steps", 
        color="failure_type",
        title="Failed Agents — Steps Taken vs Failure Type",
        color_discrete_sequence=["#FF4B4B", "#FFA500"]
    )
    st.plotly_chart(fig, width='stretch')

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
        if "❌" in step:
            st.error(f"Step {i+1}: {step}")
        elif "✅" in step:
            st.success(f"Step {i+1}: {step}")
        else:
            st.code(f"Step {i+1}: {step}")

# ---- TAB 3: AI ANALYSIS ----
with tab3:
    st.markdown("### AI Failure Analysis")
    st.markdown("Select a failed agent and click Analyze to get an AI diagnosis.")
    
    failed_agents = df[df["status"] == "❌ Fail"]["name"].tolist()
    selected_failed = st.selectbox("Select a failed agent:", failed_agents)
    
    if st.button(f"🔍 Analyze {selected_failed}"):
        with st.spinner("Gemini is analyzing the trajectory..."):
            trajectory_text = "\n".join(traces[selected_failed])
            
            prompt = f"""
You are an AI agent evaluator. Analyze this agent trajectory and diagnose the failure.

Trajectory:
{trajectory_text}

Respond in this exact format:
Failure Type: [one of: Looping, Early Exit, Wrong Approach]
Confidence: [a percentage]
Root Cause: [one sentence]
Evidence: [one sentence pointing to specific steps]
Suggestion: [one sentence on what the agent should have done]
"""
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            
            st.error("❌ Failure Detected")
            st.markdown(response.text)
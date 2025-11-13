import streamlit as st
import google.generativeai as genai
import pandas as pd
import json

# ✅ App Configuration
st.set_page_config(page_title="Howden Insurance: Query Fan-Out Simulator for AI Engines", layout="wide")
st.title("🔍 Howden Insurance: Query Fan-Out Simulator for AI Engines")

# ✅ Sidebar: API Key and Query Input
st.sidebar.header("Configuration")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password")
user_query = st.sidebar.text_area("Enter your query", "Who's the best local insurance broker in my area?", height=120)
mode = st.sidebar.radio("Search Mode", ["AI Overview (simple)", "AI Mode (complex)"])

# ✅ Configure Gemini API
if gemini_key:
    try:
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel("gemini-1.5-flash-latest")  # Flexible model selection
    except Exception as e:
        st.error(f"Failed to configure Gemini: {e}")
        st.stop()
else:
    st.error("Please enter your Gemini API Key to proceed.")
    st.stop()

# ✅ Prompt Builder Function
def QUERY_FANOUT_PROMPT(q, mode):
    min_queries_simple = 10
    min_queries_complex = 20

    if mode == "AI Overview (simple)":
        num_queries_instruction = (
            f"Analyze the user's query: \"{q}\". Based on '{mode}', decide an optimal number of queries (≥{min_queries_simple}). "
            f"For simple queries, {min_queries_simple}-{min_queries_simple+5} queries may suffice. Provide reasoning for your choice."
        )
    else:
        num_queries_instruction = (
            f"Analyze the user's query: \"{q}\". Based on '{mode}', decide an optimal number of queries (≥{min_queries_complex}). "
            f"For complex queries, {min_queries_complex+5}-{min_queries_complex+10} queries or more may be needed. Provide reasoning."
        )

    return (
        f"You are simulating Google's AI Mode query fan-out process.\n"
        f"Original query: \"{q}\". Mode: \"{mode}\".\n\n"
        f"{num_queries_instruction}\n\n"
        "Generate exactly that many unique queries in JSON format:\n"
        "{\n"
        "  \"generation_details\": {\n"
        "    \"target_query_count\": <number>,\n"
        "    \"reasoning_for_count\": \"<reasoning>\"\n"
        "  },\n"
        "  \"expanded_queries\": [\n"
        "    {\"query\": \"...\", \"type\": \"...\", \"user_intent\": \"...\", \"reasoning\": \"...\"}\n"
        "  ]\n"
        "}"
    )

# ✅ Fan-Out Generation Function
def generate_fanout(query, mode):
    prompt = QUERY_FANOUT_PROMPT(query, mode)
    try:
        response = model.generate_content(prompt)
        json_text = response.text.strip()

        # Remove markdown fences if present
        if json_text.startswith("```json"):
            json_text = json_text[7:]
        if json_text.endswith("```"):
            json_text = json_text[:-3]
        json_text = json_text.strip()

        # Validate and parse JSON
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError:
            st.error("Failed to parse Gemini response as JSON.")
            st.text("Raw response:")
            st.text(json_text)
            return None

        generation_details = data.get("generation_details", {})
        expanded_queries = data.get("expanded_queries", [])
        st.session_state.generation_details = generation_details
        return expanded_queries

    except Exception as e:
        st.error(f"Unexpected error during generation: {e}")
        return None

# ✅ Initialize session state
if 'generation_details' not in st.session_state:
    st.session_state.generation_details = None

# ✅ Run Fan-Out
if st.sidebar.button("Run Fan-Out 🚀"):
    st.session_state.generation_details = None

    if not user_query.strip():
        st.warning("Please enter a query.")
    else:
        with st.spinner("Generating query fan-out using Gemini..."):
            results = generate_fanout(user_query, mode)

        if results:
            st.success("Query fan-out complete!")

            # Display generation details
            details = st.session_state.generation_details or {}
            generated_count = len(results)
            target_count = details.get('target_query_count', 'N/A')
            reasoning = details.get('reasoning_for_count', 'Not provided.')

            st.markdown("---")
            st.subheader("Model's Query Generation Plan")
            st.markdown(f"**Target Queries:** `{target_count}`")
            st.markdown(f"**Reasoning:** _{reasoning}_")
            st.markdown(f"**Actual Generated:** `{generated_count}`")
            st.markdown("---")

            if isinstance(target_count, int) and target_count != generated_count:
                st.warning(f"Model aimed for {target_count} queries but generated {generated_count}.")

            # Display DataFrame
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True, height=(min(len(df), 20)+1)*35+3)

            # Download CSV
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", data=csv, file_name="query_fan_out.csv", mime="text/csv")
        else:
            st.warning("No queries generated or an error occurred.")

import streamlit as st
import logging
from agent import run_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="TRF Agent", page_icon="🚜", layout="wide")
st.title("🚜 TRF Groq AI Agent")

st.markdown("""
Query tractor test reports (TRF) using natural language. Specify what you want:

**Data Format**: CSV, JSON, markdown, summary, statistics, count, or table (default)
**Features**: steering, braking, suspension, engine, hydraulics, etc.
**Time**: specific months, years, sprints

**Examples:**
- "Get braking test data from February 2025 sprint 2 as CSV"
- "Give me a summary of all steering tests"
- "Show stats for March 2024 Sprint 1"
- "Count how many tests passed in February 2025"
""")

prompt = st.text_input(
    "Enter your query",
    "Get braking test data from February 2025 sprint 2 as CSV",
    help="Include feature, time period, and desired format"
)

if st.button("Run Query", type="primary"):
    if not prompt.strip():
        st.error("Please enter a query")
    else:
        try:
            with st.spinner("Processing your query..."):
                result = run_agent(prompt)
            
            if isinstance(result, list):
                # Table format (list of dicts)
                st.success(f"✅ Found {len(result)} matching records")
                st.dataframe(result, use_container_width=True)
                
                # Provide download options
                col1, col2 = st.columns(2)
                with col1:
                    import json
                    csv_rows = [[r['feature'], r['status'], r['value'], r['remarks'], r['file']] for r in result]
                    csv_header = "feature,status,value,remarks,file\n"
                    csv_data = csv_header + "\n".join([",".join(row) for row in csv_rows])
                    st.download_button("📥 Download as CSV", csv_data, "results.csv", "text/csv")
                with col2:
                    json_data = json.dumps(result, indent=2)
                    st.download_button("📥 Download as JSON", json_data, "results.json", "application/json")
                    
            elif isinstance(result, dict):
                st.json(result)
            else:
                # String output 
                result_str = str(result)
                
                if result_str.startswith("Found ") and result_str.endswith("record(s)"):
                    st.success(result_str)
                elif "Statistics" in result_str or "By Status" in result_str:
                    st.success("📊 Statistics:")
                    st.markdown(result_str)
                elif result_str.startswith("|") and "|" in result_str[5:]:
                    # Markdown table
                    st.success("📋 Table Results:")
                    st.markdown(result_str)
                    st.download_button("📥 Download as Text", result_str, "results.txt", "text/plain")
                elif "feature,status,value" in result_str:
                    # CSV format
                    st.success("📊 CSV Results:")
                    st.code(result_str, language="csv")
                    st.download_button("📥 Download CSV", result_str, "results.csv", "text/csv")
                elif "Error" in result_str or "error" in result_str.lower() or "failed" in result_str.lower():
                    st.warning(f"⚠️ {result_str}")
                else:
                    # Summary or other text
                    st.success("📝 Result:")
                    st.write(result_str)
                    
        except Exception as e:
            logger.error(f"Application error: {e}")
            st.error(f"❌ An unexpected error occurred: {str(e)}")

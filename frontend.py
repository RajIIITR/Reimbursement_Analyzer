import streamlit as st
import requests
import json

# Page config
st.set_page_config(page_title="Invoice Analysis", page_icon="📄")

# Backend URL
API_URL = "http://localhost:8000"

st.title("📄 Invoice Reimbursement Analysis")
st.markdown("---")

# Check if backend is running
def check_backend():
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

if not check_backend():
    st.error("❌ Backend not running! Please start FastAPI first: `python app.py`")
    st.stop()
else:
    st.success("✅ Backend connected")

# Initialize session state
if 'processed' not in st.session_state:
    st.session_state.processed = False
if 'employees' not in st.session_state:
    st.session_state.employees = []

# Step 1: Upload Files
st.header("Step 1: Upload Files")
col1, col2 = st.columns(2)

with col1:
    hr_policy = st.file_uploader("HR Policy PDF", type=['pdf'])
    
with col2:
    invoices_zip = st.file_uploader("Invoices ZIP", type=['zip'])

if st.button("🔍 Process Files"):
    if hr_policy and invoices_zip:
        with st.spinner("Processing... Please wait"):
            try:
                files = {
                    'hr_policy': (hr_policy.name, hr_policy.getvalue(), 'application/pdf'),
                    'invoices_zip': (invoices_zip.name, invoices_zip.getvalue(), 'application/zip')
                }
                
                response = requests.post(f"{API_URL}/analyze_invoices", files=files)
                
                if response.status_code == 200:
                    result = response.json()
                    st.session_state.processed = True
                    st.session_state.employees = list(result.get('analysis_summary', {}).keys())
                    st.success("✅ Files processed successfully!")
                    
                    # Show results
                    st.subheader("Results:")
                    st.write(f"**Total Employees:** {result.get('total_employees', 0)}")
                    st.write(f"**Employees:** {', '.join(st.session_state.employees)}")
                    
                else:
                    st.error(f"❌ Error: {response.text}")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    else:
        st.warning("Please upload both files")

# Step 2: Query Employee (only show if processed)
if st.session_state.processed:
    st.markdown("---")
    st.header("Step 2: Query Employee")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        employee_name = st.selectbox("Select Employee:", st.session_state.employees)
    
    with col2:
        query = st.text_input("Ask a question:", placeholder="What are my expenses?")
    
    if st.button("💬 Ask Question"):
        if employee_name and query:
            try:
                payload = {"employee_name": employee_name, "query": query}
                response = requests.post(f"{API_URL}/query_employee", json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    st.subheader("Answer:")
                    st.write(result.get('answer', 'No answer'))
                else:
                    st.error(f"❌ Error: {response.text}")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("Please select employee and enter question")

# Show current employees
if st.session_state.employees:
    st.markdown("---")
    st.subheader("Available Employees:")
    for emp in st.session_state.employees:
        st.write(f"• {emp}")
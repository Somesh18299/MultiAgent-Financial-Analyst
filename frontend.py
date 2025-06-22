import streamlit as st
import requests
from typing import Dict, Optional
import time

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="Financial Analysis AI",
    page_icon="📈",
    layout="centered"
)

def call_analysis_api(query: str) -> Optional[Dict]:
    """Call the analysis API with the user's query"""
    try:
        payload = {
            "query": query,
            "target_score": 5,  # Fixed value
            "max_retries": 5,   # Fixed value
            "purpose": "financial analysis"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/analyze",
            json=payload,
            timeout=300  # 5 minutes timeout
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        st.error("Request timed out. The analysis is taking longer than expected.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to the analysis service. Please make sure the backend is running.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return None

def check_api_health() -> bool:
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    # Header
    st.title("📈 Financial Analysis AI")
    st.markdown("Ask any financial question and get AI-powered analysis with web search and intelligent retry mechanisms.")
    
    # API Health Check
    with st.sidebar:
        st.header("ℹ️ About")
        
        # API Status
        api_status = check_api_health()
        if api_status:
            st.success("🟢 API Status: Online")
        else:
            st.error("🔴 API Status: Offline")
            st.warning("Make sure to run the backend server first!")
        
        st.markdown("---")
        st.markdown("**How it works:**")
        st.markdown("1. 🧠 AI breaks down your question")
        st.markdown("2. 🔍 Searches web for relevant data")
        st.markdown("3. 📊 Analyzes and summarizes findings")
        st.markdown("4. ✅ Quality check & retry if needed")
        st.markdown("5. 📈 Delivers comprehensive analysis")

    # Main content area
    # Query input
    query = st.text_area(
        "Enter your financial question:",
        height=100,
        placeholder="e.g., How is Apple performing in Q4 2024? What are the key financial metrics for Tesla this quarter? Analyze Microsoft's recent earnings report.",
        help="Ask about stock performance, earnings, financial metrics, market trends, company analysis, etc."
    )
    
    # Analyze button
    col1, col2 = st.columns([3, 1])
    
    with col1:
        analyze_button = st.button(
            "🚀 Analyze", 
            type="primary", 
            use_container_width=True,
            disabled=not api_status
        )
    
    with col2:
        if st.button("Clear", use_container_width=True):
            st.rerun()
    
    # Analysis execution
    if analyze_button:
        if not query.strip():
            st.warning("⚠️ Please enter a question to analyze.")
            return
        
        if not api_status:
            st.error("❌ Cannot analyze: API is offline. Please start the backend server.")
            return
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Start analysis
        with st.spinner("🔄 Analyzing your query... This may take a few minutes."):
            start_time = time.time()
            
            # Update progress
            status_text.text("🧠 Planning analysis strategy...")
            progress_bar.progress(10)
            
            # Call API
            result = call_analysis_api(query)
            
            if result:
                # Update progress
                progress_bar.progress(100)
                end_time = time.time()
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                # Display results
                st.markdown("## 📊 Analysis Results")
                st.markdown("---")
                
                # Analysis content
                st.markdown(result.get("final_answer", "No analysis available"))
                
                # Analysis metadata
                st.markdown("---")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    total_time = end_time - start_time
                    st.metric("Total Time", f"{total_time:.1f}s")
                
                with col2:
                    max_retries_reached = result.get("max_retries_reached", False)
                    error_occurred = result.get("error", False)
                    
                    if error_occurred:
                        status = "❌ Error"
                    elif max_retries_reached:
                        status = "⚠️ Partial"
                    else:
                        status = "✅ Complete"
                    
                    st.metric("Status", status)
                
                # Processing time breakdown
                processing_times = result.get("processing_time", {})
                if processing_times:
                    with st.expander("⏱️ Processing Time Breakdown"):
                        for stage, duration in processing_times.items():
                            st.write(f"**{stage.capitalize()}**: {duration:.2f}s")
                
                # Status messages
                if result.get("error", False):
                    st.error("❌ An error occurred during analysis. Results may be incomplete.")
                elif max_retries_reached:
                    st.warning("⚠️ Analysis completed with partial results. Some information may be limited.")
                else:
                    st.success("✅ Analysis completed successfully!")
                
            else:
                progress_bar.empty()
                status_text.empty()
                st.error("❌ Failed to get analysis. Please try again.")

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
        <p>🤖 Powered by AI agents with web search capabilities</p>
        <p>Built with FastAPI, LangGraph, Groq, and Streamlit</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, END
import os
import asyncio
import time
import logging
from typing import Dict, List, Any
import re

from dotenv import load_dotenv
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup API Keys for Groq and Tavily
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

if not GROQ_API_KEY or not TAVILY_API_KEY:
    raise ValueError("Please set GROQ_API_KEY and TAVILY_API_KEY environment variables")

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)
search_tool = TavilySearch(max_results=3)

def plan_subquestions(state: Dict) -> Dict:
    """Break down the main question into focused sub-questions"""
    start = time.time()
    user_input = state["user_input"]
    purpose = state.get("purpose", "financial analysis")
    
    prompt = f"""
    You are an expert financial analyst specializing in {purpose}.
    Break the following question into exactly 3 focused, specific sub-questions that can be answered via web search.
    Each sub-question should target different aspects of the analysis.

    Main Question: "{user_input}"

    Requirements:
    - Make each sub-question specific and searchable
    - Focus on quantitative data where possible
    - Ensure questions are complementary, not overlapping
    - Format as a numbered list (1., 2., 3.)

    Sub-questions:
    """
    
    try:
        output = llm.invoke(prompt).content
        sub_questions = []
        for line in output.strip().split("\n"):
            line = line.strip()
            if line and (line.startswith(("1.", "2.", "3.")) or line[0].isdigit()):
                question = line.split(".", 1)[-1].strip()
                if question:
                    sub_questions.append(question)
        
        # Ensure we have exactly 3 questions
        if len(sub_questions) < 3:
            sub_questions.extend([user_input] * (3 - len(sub_questions)))
        elif len(sub_questions) > 3:
            sub_questions = sub_questions[:3]
            
        processing_time = time.time() - start
        logger.info(f"Planning completed in {processing_time:.2f} seconds")
        logger.info(f"Sub-questions: {sub_questions}")
        
        return {
            **state, 
            "sub_questions": sub_questions,
            "processing_time": {**state.get("processing_time", {}), "planning": processing_time}
        }
    except Exception as e:
        logger.error(f"Error in plan_subquestions: {e}")
        return {**state, "sub_questions": [user_input]}

async def retrieve_each(state: Dict) -> Dict:
    """Retrieve information for each sub-question concurrently"""
    start = time.time()
    queries = state["sub_questions"]

    async def fetch_with_retry(query: str, max_retries: int = 2) -> Dict:
        """Fetch search results with retry logic"""
        for attempt in range(max_retries + 1):
            try:
                result = await search_tool.ainvoke({"query": query})
                logger.info(f"Search successful for: '{query}'")
                return {"question": query, "result": result, "attempt": attempt + 1}
            except Exception as e:
                logger.warning(f"Search attempt {attempt + 1} failed for '{query}': {e}")
                if attempt == max_retries:
                    return {"question": query, "result": None, "error": str(e)}
                await asyncio.sleep(1)

    try:
        results = await asyncio.gather(*[fetch_with_retry(q) for q in queries])
        
        processing_time = time.time() - start
        logger.info(f"Retrieval completed in {processing_time:.2f} seconds")
        
        return {
            **state, 
            "search_results": results,
            "processing_time": {**state.get("processing_time", {}), "retrieval": processing_time}
        }
    except Exception as e:
        logger.error(f"Error in retrieve_each: {e}")
        return {**state, "search_results": []}

def extract_content_from_search_result(result: Any) -> str:
    """Extract readable content from various search result formats"""
    if result is None:
        return ""
    
    # If it's already a string, return it
    if isinstance(result, str):
        return result[:1000]
    
    # If it's a list, try to extract from each item
    if isinstance(result, list):
        content_parts = []
        for item in result[:3]:  # Take first 3 items
            if isinstance(item, dict):
                # Try common content keys
                for key in ['content', 'text', 'snippet', 'description', 'summary']:
                    if key in item and item[key]:
                        content_parts.append(str(item[key])[:500])
                        break
            elif isinstance(item, str):
                content_parts.append(item[:500])
        return "\n---\n".join(content_parts)
    
    # If it's a dict, try to extract content
    if isinstance(result, dict):
        # Try common content keys
        for key in ['content', 'text', 'snippet', 'description', 'summary', 'results']:
            if key in result:
                if key == 'results' and isinstance(result[key], list):
                    # Recursively extract from results list
                    return extract_content_from_search_result(result[key])
                elif result[key]:
                    return str(result[key])[:1000]
    
    # Fallback: convert to string
    return str(result)[:1000]

def summarize_chunks(state: Dict) -> Dict:
    """Summarize search results for each sub-question"""
    start = time.time()
    summaries = []
    
    for chunk in state["search_results"]:
        if "error" in chunk:
            summaries.append(f"Unable to retrieve information for: {chunk['question']} (Error: {chunk['error']})")
            continue
            
        # Extract content using our robust extraction function
        content = extract_content_from_search_result(chunk["result"])
        
        if not content or len(content.strip()) < 10:
            summaries.append(f"No relevant information found for: {chunk['question']}")
            continue
        
        prompt = f"""
        You are a professional financial analyst. Analyze the following information to answer the specific question.
        Focus on quantitative data, key metrics, and factual insights.

        Question: {chunk['question']}
        
        Source Information:
        {content}

        Instructions:
        - Extract specific numbers, percentages, dates, and metrics
        - Identify key trends or changes
        - Note any significant events or developments
        - Keep the summary concise but comprehensive
        - If information is insufficient, state what's missing

        Analysis:
        """
        
        try:
            summary = llm.invoke(prompt).content
            summaries.append(f"Q: {chunk['question']}\nA: {summary}")
        except Exception as e:
            logger.error(f"Error summarizing chunk: {e}")
            summaries.append(f"Error processing: {chunk['question']}")
    
    processing_time = time.time() - start
    logger.info(f"Summarization completed in {processing_time:.2f} seconds")
    
    return {
        **state, 
        "summarized_chunks": summaries,
        "processing_time": {**state.get("processing_time", {}), "summarization": processing_time}
    }

def critic_node(state: Dict) -> Dict:
    """Evaluate the quality of summaries"""
    start = time.time()
    summaries = "\n\n".join(state["summarized_chunks"])
    
    prompt = f"""
    You are a senior financial analyst reviewing research summaries. Evaluate the quality and completeness of the analysis.

    Original Question: {state['user_input']}
    
    Analysis Summaries:
    {summaries}

    Evaluation Criteria:
    1. Completeness: Does the analysis address all aspects of the original question?
    2. Data Quality: Are specific metrics, numbers, and dates provided?
    3. Relevance: Is the information directly relevant to the question?
    4. Clarity: Is the analysis clear and well-structured?

    Provide a score from 1-10 where:
    - 8-10: Excellent, comprehensive analysis
    - 6-7: Good analysis with minor gaps
    - 4-5: Adequate but missing key information
    - 1-3: Poor, significant issues

    Format:
    Score: <number>
    Strengths: <what works well>
    Weaknesses: <what needs improvement>
    """
    
    try:
        result = llm.invoke(prompt).content
        
        # Extract score more robustly
        score = 6  # Default score
        for line in result.split('\n'):
            if line.strip().lower().startswith('score:'):
                score_part = line.split(':', 1)[1].strip()
                # Extract first number found
                numbers = re.findall(r'\d+', score_part)
                if numbers:
                    score = min(int(numbers[0]), 10)  # Cap at 10
                break
        
        processing_time = time.time() - start
        logger.info(f"Critic evaluation completed in {processing_time:.2f} seconds - Score: {score}")
        
        return {
            **state, 
            "critic_score": score, 
            "critic_feedback": result.strip(),
            "processing_time": {**state.get("processing_time", {}), "critic": processing_time}
        }
    except Exception as e:
        logger.error(f"Error in critic_node: {e}")
        return {**state, "critic_score": 6, "critic_feedback": "Error in evaluation"}

def score_based_decision(state: Dict) -> str:
    """Decide whether to proceed or retry based on critic score"""
    score = state.get("critic_score", 0)
    retry_count = state.get("retry_count", 0)
    sufficient_score = state.get("target_score", 6)  # Default target score
    max_retries = state.get("max_retries", 5)  # Default max retries
    
    logger.info(f"Decision - Score: {score}/{sufficient_score}, Retries: {retry_count}/{max_retries}")
    
    if score >= sufficient_score or retry_count >= max_retries:
        return "good_summary"
    else:
        return "poor_summary"

def synthesize_final(state: Dict) -> Dict:
    """Create comprehensive final analysis"""
    start = time.time()
    
    prompt = f"""
    You are a senior financial analyst preparing a comprehensive report. Based on the research summaries, 
    provide a detailed analysis that directly answers the original question.

    Original Question: {state['user_input']}

    Research Findings:
    {chr(10).join(state['summarized_chunks'])}

    Instructions:
    - Structure your response with clear sections
    - Lead with key findings and conclusions
    - Include specific metrics, percentages, and data points
    - Provide context and implications
    - End with a clear summary statement
    - Use professional financial analysis language

    Comprehensive Analysis:
    """
    
    try:
        final_answer = llm.invoke(prompt).content
        
        processing_time = time.time() - start
        total_time = sum(state.get("processing_time", {}).values()) + processing_time
        
        logger.info(f"Final synthesis completed in {processing_time:.2f} seconds")
        logger.info(f"Total processing time: {total_time:.2f} seconds")
        
        return {
            **state, 
            "final_answer": final_answer,
            "processing_time": {**state.get("processing_time", {}), "synthesis": processing_time}
        }
    except Exception as e:
        logger.error(f"Error in synthesize_final: {e}")
        return {**state, "final_answer": "Error generating final analysis"}

def retry_retrieval(state: Dict) -> Dict:
    """Retry with enhanced prompting and different search strategies"""
    start = time.time()
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 5)
    
    if retry_count >= max_retries:
        logger.info(f"Maximum retries ({max_retries}) reached. Proceeding with available information.")
        return {
            **state, 
            "final_answer": f"Maximum retries ({max_retries}) reached. Analysis based on available information.",
            "max_retries_reached": True
        }
    
    logger.info(f"Retrying analysis (attempt {retry_count + 1}/{max_retries})...")
    
    # Enhanced retry strategies based on retry count
    new_state = {**state, "retry_count": retry_count + 1}
    
    # Different strategies for different retry attempts
    if retry_count < 3:
        # First few retries: Try more specific sub-questions
        logger.info("Strategy: Refining sub-questions for more specific searches")
        new_state = plan_subquestions_refined(new_state)
    elif retry_count < 6:
        # Mid-range retries: Try different search terms
        logger.info("Strategy: Using alternative search terms")
        new_state = modify_search_terms(new_state)
    else:
        # Later retries: Focus on broader searches
        logger.info("Strategy: Broadening search scope")
        new_state = broaden_search_scope(new_state)
    
    processing_time = time.time() - start
    logger.info(f"Retry preparation completed in {processing_time:.2f} seconds")
    
    return {
        **new_state,
        "processing_time": {**new_state.get("processing_time", {}), f"retry_{retry_count + 1}": processing_time}
    }

def plan_subquestions_refined(state: Dict) -> Dict:
    """Create more refined and specific sub-questions"""
    user_input = state["user_input"]
    previous_feedback = state.get("critic_feedback", "")
    
    prompt = f"""
    You are an expert financial analyst. The previous analysis attempt received this feedback:
    {previous_feedback}
    
    Create 3 NEW, more specific and targeted sub-questions for this main question:
    "{user_input}"
    
    Make these questions:
    - More specific with exact metrics and timeframes
    - Focus on different data sources (earnings reports, market data, analyst reports)
    - Include specific financial terms and ratios
    - Target recent and reliable information sources
    
    Format as numbered list:
    """
    
    try:
        output = llm.invoke(prompt).content
        sub_questions = []
        for line in output.strip().split("\n"):
            line = line.strip()
            if line and (line.startswith(("1.", "2.", "3.")) or line[0].isdigit()):
                question = line.split(".", 1)[-1].strip()
                if question:
                    sub_questions.append(question)
        
        if len(sub_questions) < 3:
            sub_questions.extend([user_input] * (3 - len(sub_questions)))
        elif len(sub_questions) > 3:
            sub_questions = sub_questions[:3]
            
        logger.info(f"Refined sub-questions: {sub_questions}")
        return {**state, "sub_questions": sub_questions}
    except Exception as e:
        logger.error(f"Error in plan_subquestions_refined: {e}")
        return state

def modify_search_terms(state: Dict) -> Dict:
    """Modify search terms for better results"""
    original_questions = state["sub_questions"]
    modified_questions = []
    
    # Add more specific financial terms and synonyms
    enhancements = [
        " financial results earnings revenue",
        " stock performance market cap valuation", 
        " quarterly report Q1 Q2 Q3 Q4 annual"
    ]
    
    for i, question in enumerate(original_questions):
        if i < len(enhancements):
            modified_question = question + enhancements[i]
        else:
            modified_question = question + " latest news update"
        modified_questions.append(modified_question)
    
    logger.info(f"Modified search terms: {modified_questions}")
    return {**state, "sub_questions": modified_questions}

def broaden_search_scope(state: Dict) -> Dict:
    """Broaden the search scope for more general information"""
    user_input = state["user_input"]
    
    # Create broader, more general questions
    broad_questions = [
        f"{user_input} news recent developments",
        f"{user_input} financial performance overview",
        f"{user_input} market analysis investor sentiment"
    ]
    
    logger.info(f"Broadened search scope: {broad_questions}")
    return {**state, "sub_questions": broad_questions}

def create_financial_analysis_graph():
    """Create and configure the financial analysis workflow"""
    workflow = StateGraph(dict)
    
    # Set entry point
    workflow.set_entry_point("planner")
    
    # Add nodes
    workflow.add_node("planner", plan_subquestions)
    workflow.add_node("retriever", retrieve_each)
    workflow.add_node("summarizer", summarize_chunks)
    workflow.add_node("critic", critic_node)
    workflow.add_node("synthesizer", synthesize_final)
    workflow.add_node("retry", retry_retrieval)
    
    # Add edges
    workflow.add_edge("planner", "retriever")
    workflow.add_edge("retriever", "summarizer")
    workflow.add_edge("summarizer", "critic")
    
    # Conditional edges based on critic evaluation
    workflow.add_conditional_edges(
        "critic",
        score_based_decision,
        {
            "good_summary": "synthesizer",
            "poor_summary": "retry"
        }
    )
    
    workflow.add_edge("retry", "retriever")  # Go back to retrieval with new strategy
    workflow.add_edge("synthesizer", END)
    
    return workflow.compile()

async def analyze_stock_question(question: str, purpose: str = "financial analysis", 
                                target_score: int = 6, max_retries: int = 5) -> Dict:
    """Main function to analyze stock-related questions with configurable retry parameters"""
    graph = create_financial_analysis_graph()
    
    initial_state = {
        "user_input": question,
        "purpose": purpose,
        "retry_count": 0,
        "target_score": target_score,  # Minimum acceptable critic score
        "max_retries": max_retries,    # Maximum number of retries
        "processing_time": {}
    }
    
    try:
        result = await graph.ainvoke(initial_state)
        return result
    except Exception as e:
        logger.error(f"Error in analysis: {e}")
        return {"final_answer": f"Analysis failed: {str(e)}", "error": True}
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
import logging
from graph import analyze_stock_question

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Financial Analysis API",
    description="AI-powered financial analysis service",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalysisRequest(BaseModel):
    query: str
    target_score: int = 5  # Fixed default value
    max_retries: int = 5   # Fixed default value
    purpose: str = "financial analysis"

class AnalysisResponse(BaseModel):
    final_answer: str
    critic_score: Optional[int] = None
    retry_count: int = 0
    processing_time: Dict = {}
    max_retries_reached: bool = False
    error: bool = False
    critic_feedback: Optional[str] = None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Financial Analysis API is running"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "Financial Analysis API",
        "version": "1.0.0"
    }

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_financial_query(request: AnalysisRequest):
    """
    Analyze a financial query using the AI agent
    
    Args:
        request: AnalysisRequest containing the query and parameters
        
    Returns:
        AnalysisResponse with the analysis results
    """
    try:
        logger.info(f"Received analysis request: {request.query}")
        
        # Validate input
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Force fixed values regardless of what's sent in request
        target_score = 5
        max_retries = 5
        
        logger.info(f"Using fixed parameters - Target Score: {target_score}, Max Retries: {max_retries}")
        
        # Run the analysis
        result = await analyze_stock_question(
            question=request.query,
            purpose=request.purpose,
            target_score=target_score,
            max_retries=max_retries
        )
        
        # Prepare response
        response = AnalysisResponse(
            final_answer=result.get("final_answer", "No analysis available"),
            critic_score=result.get("critic_score"),
            retry_count=result.get("retry_count", 0),
            processing_time=result.get("processing_time", {}),
            max_retries_reached=result.get("max_retries_reached", False),
            error=result.get("error", False),
            critic_feedback=result.get("critic_feedback")
        )
        
        logger.info(f"Analysis completed successfully. Score: {response.critic_score}, Retries: {response.retry_count}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing analysis request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/analyze/status/{task_id}")
async def get_analysis_status(task_id: str):
    """
    Get the status of a long-running analysis task
    Note: This is a placeholder for future implementation of async task tracking
    """
    return {"message": "Task status endpoint - not implemented yet", "task_id": task_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
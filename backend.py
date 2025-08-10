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
    target_score: int = 6  # Fixed default value
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

# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from typing import Dict, Optional
# import logging
# import asyncio
# import time
# import threading
# from graph import analyze_stock_question

# # Setup detailed logging
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
# )
# logger = logging.getLogger(__name__)

# # Create a separate logger for request tracking
# request_logger = logging.getLogger("REQUEST_TRACKER")
# request_logger.setLevel(logging.INFO)

# app = FastAPI(
#     title="Financial Analysis API",
#     description="AI-powered financial analysis service",
#     version="1.0.0"
# )

# # Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # In production, specify exact origins
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Track active requests
# active_requests = {}
# request_counter = 0

# class AnalysisRequest(BaseModel):
#     query: str
#     target_score: int = 6  # Fixed default value
#     max_retries: int = 5   # Fixed default value
#     purpose: str = "financial analysis"

# class AnalysisResponse(BaseModel):
#     final_answer: str
#     critic_score: Optional[int] = None
#     retry_count: int = 0
#     processing_time: Dict = {}
#     max_retries_reached: bool = False
#     error: bool = False
#     critic_feedback: Optional[str] = None

# @app.middleware("http")
# async def log_requests(request, call_next):
#     """Middleware to log all requests and responses"""
#     global request_counter
#     request_counter += 1
#     request_id = f"REQ_{request_counter}_{int(time.time())}"
    
#     start_time = time.time()
    
#     request_logger.info(f"🔵 [{request_id}] INCOMING REQUEST: {request.method} {request.url}")
#     request_logger.info(f"🔵 [{request_id}] Thread ID: {threading.current_thread().ident}")
#     request_logger.info(f"🔵 [{request_id}] Active requests before: {len(active_requests)}")
    
#     # Track this request
#     active_requests[request_id] = {
#         "start_time": start_time,
#         "method": request.method,
#         "url": str(request.url),
#         "thread_id": threading.current_thread().ident
#     }
    
#     try:
#         response = await call_next(request)
        
#         end_time = time.time()
#         duration = end_time - start_time
        
#         request_logger.info(f"🟢 [{request_id}] COMPLETED: {response.status_code} in {duration:.2f}s")
        
#         return response
        
#     except Exception as e:
#         end_time = time.time()
#         duration = end_time - start_time
        
#         request_logger.error(f"🔴 [{request_id}] FAILED: {str(e)} after {duration:.2f}s")
#         raise
        
#     finally:
#         # Remove from active requests
#         if request_id in active_requests:
#             del active_requests[request_id]
#         request_logger.info(f"🔵 [{request_id}] Active requests after: {len(active_requests)}")

# @app.get("/")
# async def root():
#     """Health check endpoint"""
#     logger.info("🏠 Root endpoint called")
#     return {"message": "Financial Analysis API is running"}

# @app.get("/health")
# async def health_check():
#     """Detailed health check"""
#     logger.info("🏥 Health check endpoint called")
    
#     # Get system info
#     thread_count = threading.active_count()
#     current_thread = threading.current_thread().ident
    
#     health_info = {
#         "status": "healthy",
#         "service": "Financial Analysis API",
#         "version": "1.0.0",
#         "active_requests": len(active_requests),
#         "thread_count": thread_count,
#         "current_thread": current_thread,
#         "timestamp": time.time()
#     }
    
#     logger.info(f"🏥 Health info: {health_info}")
#     return health_info

# @app.get("/debug/status")
# async def debug_status():
#     """Debug endpoint to show system status"""
#     logger.info("🔧 Debug status endpoint called")
    
#     debug_info = {
#         "active_requests": active_requests,
#         "thread_count": threading.active_count(),
#         "current_thread": threading.current_thread().ident,
#         "request_counter": request_counter
#     }
    
#     logger.info(f"🔧 Debug info: {debug_info}")
#     return debug_info

# @app.post("/analyze", response_model=AnalysisResponse)
# async def analyze_financial_query(request: AnalysisRequest):
#     """
#     Analyze a financial query using the AI agent
    
#     Args:
#         request: AnalysisRequest containing the query and parameters
        
#     Returns:
#         AnalysisResponse with the analysis results
#     """
#     analysis_start_time = time.time()
#     current_thread = threading.current_thread().ident
    
#     logger.info(f"🚀 ANALYSIS STARTED - Thread: {current_thread}")
#     logger.info(f"🚀 Query: {request.query}")
#     logger.info(f"🚀 Active requests at start: {len(active_requests)}")
    
#     try:
#         # Validate input
#         logger.debug("🔍 Validating input...")
#         if not request.query.strip():
#             logger.warning("❌ Empty query received")
#             raise HTTPException(status_code=400, detail="Query cannot be empty")
        
#         # Force fixed values regardless of what's sent in request
#         target_score = 5
#         max_retries = 5
        
#         logger.info(f"⚙️ Using fixed parameters - Target Score: {target_score}, Max Retries: {max_retries}")
        
#         # Log before calling the analysis function
#         logger.info("📊 About to call analyze_stock_question...")
#         analysis_call_start = time.time()
        
#         # Run the analysis
#         try:
#             logger.info("🔄 Calling analyze_stock_question with asyncio...")
#             result = await analyze_stock_question(
#                 question=request.query,
#                 purpose=request.purpose,
#                 target_score=target_score,
#                 max_retries=max_retries
#             )
            
#             analysis_call_end = time.time()
#             logger.info(f"✅ analyze_stock_question completed in {analysis_call_end - analysis_call_start:.2f}s")
            
#         except asyncio.TimeoutError as e:
#             logger.error(f"⏰ Timeout in analyze_stock_question: {str(e)}")
#             raise HTTPException(status_code=504, detail="Analysis timed out")
#         except asyncio.CancelledError as e:
#             logger.error(f"🚫 Analysis cancelled: {str(e)}")
#             raise HTTPException(status_code=499, detail="Analysis cancelled")
#         except Exception as e:
#             logger.error(f"💥 Error in analyze_stock_question: {str(e)}")
#             logger.error(f"💥 Error type: {type(e)}")
#             raise
        
#         logger.info("📊 Analysis function returned, processing results...")
        
#         # Prepare response
#         logger.debug("📦 Preparing response...")
#         response = AnalysisResponse(
#             final_answer=result.get("final_answer", "No analysis available"),
#             critic_score=result.get("critic_score"),
#             retry_count=result.get("retry_count", 0),
#             processing_time=result.get("processing_time", {}),
#             max_retries_reached=result.get("max_retries_reached", False),
#             error=result.get("error", False),
#             critic_feedback=result.get("critic_feedback")
#         )
        
#         analysis_end_time = time.time()
#         total_analysis_time = analysis_end_time - analysis_start_time
        
#         logger.info(f"✅ ANALYSIS COMPLETED successfully in {total_analysis_time:.2f}s")
#         logger.info(f"✅ Score: {response.critic_score}, Retries: {response.retry_count}")
#         logger.info(f"✅ Thread: {current_thread}")
        
#         return response
        
#     except HTTPException as he:
#         analysis_end_time = time.time()
#         total_analysis_time = analysis_end_time - analysis_start_time
        
#         logger.error(f"🔴 HTTP Exception after {total_analysis_time:.2f}s: {he.detail}")
#         logger.error(f"🔴 Thread: {current_thread}")
#         raise
        
#     except Exception as e:
#         analysis_end_time = time.time()
#         total_analysis_time = analysis_end_time - analysis_start_time
        
#         logger.error(f"💥 UNEXPECTED ERROR after {total_analysis_time:.2f}s: {str(e)}")
#         logger.error(f"💥 Error type: {type(e)}")
#         logger.error(f"💥 Thread: {current_thread}")
#         logger.exception("Full traceback:")
        
#         raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
#     finally:
#         final_time = time.time()
#         total_time = final_time - analysis_start_time
#         logger.info(f"🏁 ANALYSIS ENDPOINT FINISHED after {total_time:.2f}s - Thread: {current_thread}")

# @app.get("/analyze/status/{task_id}")
# async def get_analysis_status(task_id: str):
#     """
#     Get the status of a long-running analysis task
#     Note: This is a placeholder for future implementation of async task tracking
#     """
#     logger.info(f"📋 Task status requested for: {task_id}")
#     return {"message": "Task status endpoint - not implemented yet", "task_id": task_id}

# # Add a startup event to log server startup
# @app.on_event("startup")
# async def startup_event():
#     logger.info("🚀 FastAPI server starting up...")
#     logger.info(f"🚀 Main thread ID: {threading.current_thread().ident}")
#     logger.info(f"🚀 Thread count at startup: {threading.active_count()}")

# # Add a shutdown event to log server shutdown
# @app.on_event("shutdown")
# async def shutdown_event():
#     logger.info("🛑 FastAPI server shutting down...")
#     logger.info(f"🛑 Active requests at shutdown: {len(active_requests)}")
#     logger.info(f"🛑 Thread count at shutdown: {threading.active_count()}")

# if __name__ == "__main__":
#     import uvicorn
    
#     logger.info("🏁 Starting server with uvicorn...")
#     uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
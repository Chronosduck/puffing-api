# ============================================
# FILE 3: app.py
# Main FastAPI application
# ============================================
"""
FastAPI Backend for Puffing Language IDE
A modern, async REST API for executing Puffing Language code
Compatible with FastAPI 0.128.0+ and Pydantic 2.12.5+
"""
import os
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from models import (
    CodeRequest, ExecutionResponse,
    ValidationRequest, ValidationResponse,
    HealthResponse
)
from services import PuffingExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Puffing Language API",
    description="REST API for executing Puffing Language code",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================
# CORS Configuration for Render
# ============================================

ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

allowed_origins = [
    "https://puffingmanual.web.app",
    "https://puffingmanual.firebaseapp.com",
]

# Add localhost for development
if ENVIRONMENT == "development":
    allowed_origins.extend([
        "http://localhost:5173",
        "http://localhost:5000",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # ← NOW SPECIFIC ORIGINS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Initialize executor
executor = PuffingExecutor()


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Puffing Language API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="ok",
        version="0.1.0",
        language="Puffing"
    )


@app.post("/execute", response_model=ExecutionResponse, tags=["Execution"])
async def execute_code(request: CodeRequest):
    """
    Execute Puffing Language code
    
    - **code**: Puffing Language source code
    - **timeout**: Maximum execution time (1-30 seconds)
    
    Returns execution results including output, errors, and execution time
    """
    try:
        logger.info(f"Executing code (length: {len(request.code)} chars)")
        
        if not request.code.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Code cannot be empty"
            )
        
# Execute code
        result = executor.execute(
            request.code, 
            request.timeout,
            request.input_values or []
        )
        
        logger.info(f"Execution completed: success={result['success']}, "
                   f"time={result['execution_time']}s")
        
        return ExecutionResponse(**result)
        
    except Exception as e:
        logger.error(f"Unexpected error in execute endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(e)}"
        )


@app.post("/validate", response_model=ValidationResponse, tags=["Validation"])
async def validate_syntax(request: ValidationRequest):
    """
    Validate Puffing Language syntax without execution
    
    - **code**: Code to validate
    
    Returns validation results and token list if valid
    """
    try:
        logger.info(f"Validating code (length: {len(request.code)} chars)")
        
        if not request.code.strip():
            return ValidationResponse(
                valid=False,
                error="Code cannot be empty",
                tokens=None
            )
        
        # Validate syntax
        is_valid, error_msg, tokens = executor.validate_syntax(request.code)
        
        logger.info(f"Validation completed: valid={is_valid}")
        
        return ValidationResponse(
            valid=is_valid,
            error=error_msg,
            tokens=tokens if is_valid else None
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in validate endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )




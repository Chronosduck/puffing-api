# ============================================
# FILE 1: models.py
# Pydantic models for API validation
# ============================================
"""
Pydantic models for API request/response validation
Compatible with Pydantic 2.12.5+ and FastAPI 0.128.0+
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class CodeRequest(BaseModel):
    """Request model for code execution"""
    code: str = Field(..., description="Puffing Language source code to execute")
    timeout: Optional[int] = Field(5, description="Execution timeout in seconds", ge=1, le=30)
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "code": 'print("Hello, Puffing!");',
                "timeout": 5
            }]
        }
    }


class ExecutionResponse(BaseModel):
    """Response model for code execution"""
    success: bool = Field(..., description="Whether execution was successful")
    output: Optional[str] = Field(None, description="Program output")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    error_type: Optional[str] = Field(None, description="Type of error")
    traceback: Optional[str] = Field(None, description="Full error traceback")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "success": True,
                "output": "Hello, Puffing!\n",
                "error": None,
                "error_type": None,
                "traceback": None,
                "execution_time": 0.023
            }]
        }
    }


class ValidationRequest(BaseModel):
    """Request model for syntax validation"""
    code: str = Field(..., description="Code to validate")


class ValidationResponse(BaseModel):
    """Response model for syntax validation"""
    valid: bool = Field(..., description="Whether code is syntactically valid")
    error: Optional[str] = Field(None, description="Validation error message")
    tokens: Optional[List[Dict[str, Any]]] = Field(None, description="Token list if valid")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    language: str

# ============================================
# FILE 2: services.py
# Core execution services
# ============================================
"""
Core services for executing Puffing Language code
"""
import sys
import time
import traceback
from io import StringIO
from typing import Tuple, Optional
import signal
from contextlib import contextmanager

# Import Puffing Language components
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.lexer import Lexer
from src.parser import Parser
from src.interpreter import Interpreter
from src.errors import PuffingError


class TimeoutException(Exception):
    """Raised when code execution times out"""
    pass


def timeout_handler(signum, frame):
    """Signal handler for execution timeout"""
    raise TimeoutException("Code execution timed out")


@contextmanager
def time_limit(seconds: int):
    """Context manager to limit execution time"""
    if sys.platform != 'win32':
        # Unix-based systems
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
    else:
        # Windows doesn't support SIGALRM, just yield without timeout
        # In production, consider using threading.Timer or multiprocessing
        yield


class PuffingExecutor:
    """Service for executing Puffing Language code"""
    
    @staticmethod
    def validate_syntax(code: str) -> Tuple[bool, Optional[str], Optional[list]]:
        """
        Validate Puffing Language syntax without execution
        
        Returns:
            (is_valid, error_message, tokens)
        """
        try:
            # Tokenize
            lexer = Lexer(code)
            tokens = lexer.tokenize()
            
            # Parse
            parser = Parser(tokens)
            parser.parse()
            
            # Convert tokens to serializable format
            token_list = [
                {"type": str(token.type), "value": token.value}
                for token in tokens
            ]
            
            return True, None, token_list
            
        except PuffingError as e:
            return False, str(e), None
        except Exception as e:
            return False, f"Unexpected error: {str(e)}", None
    
    @staticmethod
    def execute(code: str, timeout: int = 5) -> dict:
        """
        Execute Puffing Language code and capture output
        
        Args:
            code: Source code to execute
            timeout: Maximum execution time in seconds
            
        Returns:
            Dictionary with execution results
        """
        start_time = time.time()
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            with time_limit(timeout):
                # Tokenize
                lexer = Lexer(code)
                tokens = lexer.tokenize()
                
                # Parse
                parser = Parser(tokens)
                ast = parser.parse()
                
                # Interpret
                interpreter = Interpreter()
                interpreter.run(ast)
                
                # Get output
                output = captured_output.getvalue()
                execution_time = time.time() - start_time
                
                return {
                    "success": True,
                    "output": output or "Program executed successfully!",
                    "error": None,
                    "error_type": None,
                    "traceback": None,
                    "execution_time": round(execution_time, 4)
                }
                
        except TimeoutException:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "output": None,
                "error": f"Execution timed out after {timeout} seconds",
                "error_type": "TimeoutError",
                "traceback": None,
                "execution_time": round(execution_time, 4)
            }
            
        except PuffingError as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "output": None,
                "error": str(e),
                "error_type": e.__class__.__name__,
                "traceback": traceback.format_exc(),
                "execution_time": round(execution_time, 4)
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "output": None,
                "error": f"Unexpected error: {str(e)}",
                "error_type": e.__class__.__name__,
                "traceback": traceback.format_exc(),
                "execution_time": round(execution_time, 4)
            }
            
        finally:
            # Restore stdout
            sys.stdout = old_stdout



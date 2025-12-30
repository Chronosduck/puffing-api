"""
Enhanced Error Handling System for Puffing Language
Provides detailed, user-friendly error messages with context and ASCII emoticons! :D
"""


class PuffingError(Exception):
    """Base exception for Puffing Language"""
    def __init__(self, message, line=None, column=None):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(self.format_error())
    
    def format_error(self):
        """Format error message with location info"""
        if self.line and self.column:
            return f"Line {self.line}, col {self.column}: {self.message}"
        elif self.line:
            return f"Line {self.line}: {self.message}"
        return self.message


# ==================== LEXER ERRORS ====================

class LexerError(PuffingError):
    """Raised when lexical analysis fails"""
    pass


class UnterminatedStringError(LexerError):
    """Raised when string literal is not closed"""
    def __init__(self, line, column):
        super().__init__(
            "Unterminated string literal - missing closing quote! Don't leave your strings hanging! (>_<)",
            line, column
        )


class UnterminatedCommentError(LexerError):
    """Raised when block comment is not closed"""
    def __init__(self, line, column):
        super().__init__(
            "Unterminated block comment - missing closing '-?' Your comment is going on forever! (-_-;)",
            line, column
        )


class InvalidCharacterError(LexerError):
    """Raised when encountering invalid character"""
    def __init__(self, char, line, column):
        super().__init__(
            f"Invalid character '{char}' - not recognized by Puffing! This character is sus... (o_O)",
            line, column
        )


class InvalidNumberError(LexerError):
    """Raised when number format is invalid"""
    def __init__(self, number_str, line, column):
        super().__init__(
            f"Invalid number format '{number_str}' - That's not how math works! (╯°□°)╯",
            line, column
        )


# ==================== PARSER ERRORS ====================

class ParserError(PuffingError):
    """Raised when parsing fails"""
    pass


class UnexpectedTokenError(ParserError):
    """Raised when unexpected token is encountered"""
    def __init__(self, expected, got, value=None):
        msg = f"Expected {expected}, but got {got}"
        if value is not None:
            msg += f" ('{value}')"
        msg += " - Plot twist we didn't see coming! (O_o)"
        super().__init__(msg)


class UnexpectedEOFError(ParserError):
    """Raised when file ends unexpectedly"""
    def __init__(self, expected):
        super().__init__(
            f"Unexpected end of file - expected {expected}. Your code just... stopped! (T_T)"
        )


class InvalidSyntaxError(ParserError):
    """Raised for general syntax errors"""
    def __init__(self, message, line=None):
        super().__init__(f"Syntax Error: {message} - Let's review the grammar rules! (^_^;)", line)


class MissingBraceError(ParserError):
    """Raised when brace is missing"""
    def __init__(self, brace_type="'}'"):
        super().__init__(f"Missing {brace_type} - Did you forget to close something? :P")


class InvalidDestructuringError(ParserError):
    """Raised when destructuring pattern is invalid"""
    def __init__(self, message):
        super().__init__(f"Invalid destructuring pattern: {message} - Unpacking went wrong! (@_@)")


class InvalidFunctionDefinitionError(ParserError):
    """Raised when function definition is malformed"""
    def __init__(self, message):
        super().__init__(f"Invalid function definition: {message} - Function looks funky! (¬‿¬)")


class InvalidLambdaError(ParserError):
    """Raised when lambda syntax is invalid"""
    def __init__(self, message):
        super().__init__(f"Invalid lambda expression: {message} - Lambda's not feeling right! (._. )")


# ==================== RUNTIME ERRORS ====================

class RuntimeError(PuffingError):
    """Raised when runtime execution fails"""
    pass


class VariableNotDefinedError(RuntimeError):
    """Raised when accessing undefined variable"""
    def __init__(self, var_name):
        super().__init__(
            f"Variable '{var_name}' is not defined. "
            f"Did you forget to declare it with 'let' or 'lock'? (o_o)?"
        )


class ConstantReassignmentError(RuntimeError):
    """Raised when trying to modify a constant"""
    def __init__(self, const_name):
        super().__init__(
            f"Cannot reassign constant '{const_name}'. "
            f"Constants declared with 'lock' are immutable. Nice try though! (¬_¬)"
        )


class TypeMismatchError(RuntimeError):
    """Raised when type operation is invalid"""
    def __init__(self, operation, type1, type2=None):
        if type2:
            msg = f"Cannot perform {operation} on {type1} and {type2} - These types don't play well together! (X_X)"
        else:
            msg = f"Cannot perform {operation} on {type1} - Wrong type buddy! (>_<)"
        super().__init__(msg)


class DivisionByZeroError(RuntimeError):
    """Raised when dividing by zero"""
    def __init__(self):
        super().__init__(
            "Division by zero is not allowed - Math police says NO! ಠ_ಠ"
        )


class IndexError(RuntimeError):
    """Raised when array/string index is out of bounds"""
    def __init__(self, index, length, container_type="array"):
        if index < 0:
            super().__init__(
                f"Negative index {index} out of range for {container_type} "
                f"of length {length} - Going too far back! (◉_◉)"
            )
        else:
            super().__init__(
                f"Index {index} out of range for {container_type} of length {length}. "
                f"Remember: Puffing uses 1-based indexing (valid range: 1-{length}) - Stay in bounds! :/"
            )


class InvalidIndexTypeError(RuntimeError):
    """Raised when index is not an integer"""
    def __init__(self, index_type):
        super().__init__(
            f"Array/string indices must be integers, not {index_type} - Numbers only please! (¬_¬)"
        )


class KeyNotFoundError(RuntimeError):
    """Raised when dictionary key doesn't exist"""
    def __init__(self, key):
        super().__init__(
            f"Key '{key}' not found in dictionary. "
            f"Use has_key() to check if key exists, or get() with a default value. Key's MIA! (·_·)"
        )


class InvalidKeyTypeError(RuntimeError):
    """Raised when dictionary key type is invalid"""
    def __init__(self, key_type):
        super().__init__(
            f"Dictionary keys must be strings, numbers, or bools, not {key_type} - Pick a valid key type! (>_<)>"
        )


class NotIterableError(RuntimeError):
    """Raised when trying to iterate non-iterable"""
    def __init__(self, type_name):
        super().__init__(
            f"Cannot iterate over {type_name}. "
            f"Only arrays, strings, and ranges are iterable. Can't loop through that! (._. )"
        )


class NotIndexableError(RuntimeError):
    """Raised when trying to index non-indexable type"""
    def __init__(self, type_name):
        super().__init__(
            f"Cannot index {type_name}. "
            f"Only arrays, strings, and dictionaries support indexing. No square brackets for you! (¬‿¬)"
        )


class EmptyArrayError(RuntimeError):
    """Raised when operation requires non-empty array"""
    def __init__(self, operation):
        super().__init__(
            f"Cannot perform {operation} on empty array - Nothing to work with! (._. )"
        )


class DestructuringError(RuntimeError):
    """Raised when destructuring fails"""
    def __init__(self, expected, got):
        super().__init__(
            f"Cannot destructure: expected {expected} values, but got {got} - Size mismatch! (@_@)"
        )


class InvalidDestructuringTypeError(RuntimeError):
    """Raised when destructuring non-iterable"""
    def __init__(self, type_name):
        super().__init__(
            f"Cannot destructure {type_name}. "
            f"Destructuring requires an array or iterable. Can't unpack that! (>_<)"
        )


class FunctionNotFoundError(RuntimeError):
    """Raised when function doesn't exist"""
    def __init__(self, func_name):
        super().__init__(
            f"Function '{func_name}' is not defined - Did you spell it right? (o_O)"
        )


class NotCallableError(RuntimeError):
    """Raised when trying to call non-function"""
    def __init__(self, name, type_name):
        super().__init__(
            f"'{name}' is not a function (it's a {type_name}). "
            f"Cannot call non-function values. That's not callable! (¬_¬)"
        )


class ArgumentCountError(RuntimeError):
    """Raised when function argument count doesn't match"""
    def __init__(self, func_name, expected, got):
        super().__init__(
            f"Function '{func_name}' expects {expected} argument(s), "
            f"but {got} were provided - Wrong number of args! (>_<)"
        )


class InvalidCastError(RuntimeError):
    """Raised when type casting fails"""
    def __init__(self, value, target_type, reason=None):
        msg = f"Cannot cast '{value}' to {target_type}"
        if reason:
            msg += f": {reason}"
        msg += " - Type conversion failed! (X_X)"
        super().__init__(msg)


class LibraryNotFoundError(RuntimeError):
    """Raised when library import fails"""
    def __init__(self, lib_name):
        super().__init__(
            f"Library '{lib_name}' not found. "
            f"Available libraries: math.main, string.main - Check the spelling! (·_·)"
        )


class BreakOutsideLoopError(RuntimeError):
    """Raised when break used outside loop"""
    def __init__(self):
        super().__init__(
            "'break' statement can only be used inside loops - You're not in a loop! (O_o)"
        )


class ContinueOutsideLoopError(RuntimeError):
    """Raised when continue used outside loop"""
    def __init__(self):
        super().__init__(
            "'continue' statement can only be used inside loops - No loop to continue! (o_O)"
        )


class ReturnOutsideFunctionError(RuntimeError):
    """Raised when return used outside function"""
    def __init__(self):
        super().__init__(
            "'return' statement can only be used inside functions - Nothing to return from! (-_-;)"
        )


class InvalidFormatError(RuntimeError):
    """Raised when format operation fails"""
    def __init__(self, value, type_name):
        super().__init__(
            f"Cannot format {type_name} value '{value}'. "
            f"Formatting only works with numbers. Format fail! (>_<)"
        )


class InvalidInputError(RuntimeError):
    """Raised when input conversion fails"""
    def __init__(self, input_str, target_type, reason=None):
        msg = f"Cannot convert input '{input_str}' to {target_type}"
        if reason:
            msg += f": {reason}"
        msg += " - Bad input conversion! (@_@)"
        super().__init__(msg)


class InvalidSortError(RuntimeError):
    """Raised when array cannot be sorted"""
    def __init__(self, reason):
        super().__init__(
            f"Cannot sort array: {reason}. "
            f"All elements must be comparable (same type). Sorting chaos! (╯°□°)╯"
        )


class InvalidRangeError(RuntimeError):
    """Raised when range arguments are invalid"""
    def __init__(self, message):
        super().__init__(f"Invalid range: {message} - Range doesn't make sense! (·_·)")


class StackOverflowError(RuntimeError):
    """Raised when recursion depth exceeds limit"""
    def __init__(self, func_name=None):
        if func_name:
            super().__init__(
                f"Maximum recursion depth exceeded in function '{func_name}'. "
                f"Check for infinite recursion. Too much recursion! (X_X)"
            )
        else:
            super().__init__(
                "Maximum recursion depth exceeded. Check for infinite recursion. Stack overflow! (╯°□°)╯"
            )


class InvalidCompoundAssignError(RuntimeError):
    """Raised when compound assignment has type issues"""
    def __init__(self, operator, var_type, value_type):
        super().__init__(
            f"Cannot apply compound operator '{operator}' to {var_type} and {value_type} - Types don't match! (>_<)"
        )


class InvalidIncrementError(RuntimeError):
    """Raised when increment/decrement applied to non-numeric"""
    def __init__(self, var_name, var_type):
        super().__init__(
            f"Cannot increment/decrement '{var_name}' of type {var_type}. "
            f"Only numeric types support ++/-- operators. Can't count that! (¬_¬)"
        )


class InvalidUnaryOperatorError(RuntimeError):
    """Raised when unary operator applied to wrong type"""
    def __init__(self, operator, operand_type):
        super().__init__(
            f"Cannot apply unary operator '{operator}' to {operand_type} - Wrong type for this operator! (._. )"
        )


class InvalidBinaryOperatorError(RuntimeError):
    """Raised when binary operator applied to incompatible types"""
    def __init__(self, operator, left_type, right_type):
        super().__init__(
            f"Cannot apply operator '{operator}' between {left_type} and {right_type} - Incompatible types! (X_X)"
        )


class ModuloByZeroError(RuntimeError):
    """Raised when modulo by zero"""
    def __init__(self):
        super().__init__(
            "Modulo by zero is not allowed - Can't divide remainders by zero! ಠ_ಠ"
        )


class NegativeExponentError(RuntimeError):
    """Raised when negative number raised to fractional power"""
    def __init__(self, base, exponent):
        super().__init__(
            f"Cannot raise negative number {base} to fractional power {exponent} - Math says nope! (>_<)"
        )


class StringIndexAssignmentError(RuntimeError):
    """Raised when trying to assign to string index"""
    def __init__(self):
        super().__init__(
            "Cannot assign to string index. Strings are immutable in Puffing. No string mutations! (¬_¬)"
        )


class InvalidSliceError(RuntimeError):
    """Raised when slice arguments are invalid"""
    def __init__(self, message):
        super().__init__(f"Invalid slice: {message} - Slicing went wrong! (@_@)")


class ArrayMethodError(RuntimeError):
    """Raised when array method fails"""
    def __init__(self, method_name, message):
        super().__init__(f"Array method '{method_name}' failed: {message} - Method mishap! (X_X)")


class DictMethodError(RuntimeError):
    """Raised when dictionary method fails"""
    def __init__(self, method_name, message):
        super().__init__(f"Dictionary method '{method_name}' failed: {message} - Dict disaster! (>_<)")


class StringMethodError(RuntimeError):
    """Raised when string method fails"""
    def __init__(self, method_name, message):
        super().__init__(f"String method '{method_name}' failed: {message} - String struggle! (@_@)")


class InvalidComparisonError(RuntimeError):
    """Raised when comparing incomparable types"""
    def __init__(self, left_type, right_type):
        super().__init__(
            f"Cannot compare {left_type} and {right_type}. "
            f"Comparison requires compatible types. Apples and oranges! (¬‿¬)"
        )


class CircularReferenceError(RuntimeError):
    """Raised when circular reference detected in nested structures"""
    def __init__(self):
        super().__init__(
            "Circular reference detected in nested data structure - Inception! (O_o)"
        )


class ImmutableModificationError(RuntimeError):
    """Raised when trying to modify immutable value"""
    def __init__(self, operation, type_name):
        super().__init__(
            f"Cannot perform {operation} on immutable {type_name} - No modifications allowed! (¬_¬)"
        )


class InvalidLengthError(RuntimeError):
    """Raised when len() applied to non-sized type"""
    def __init__(self, type_name):
        super().__init__(
            f"Object of type {type_name} has no length. "
            f"len() only works with arrays, strings, and dictionaries. Can't measure that! (·_·)"
        )


class MathDomainError(RuntimeError):
    """Raised when math operation outside valid domain"""
    def __init__(self, operation, value, reason):
        super().__init__(
            f"Math error in {operation}({value}): {reason} - Math domain violation! (X_X)"
        )


class InvalidParameterError(RuntimeError):
    """Raised when function parameter is invalid"""
    def __init__(self, func_name, param_name, expected, got):
        super().__init__(
            f"Invalid parameter '{param_name}' for {func_name}: "
            f"expected {expected}, got {got} - Wrong parameter type! (@_@)"
        )


class DuplicateParameterError(ParserError):
    """Raised when function has duplicate parameter names"""
    def __init__(self, param_name):
        super().__init__(
            f"Duplicate parameter name '{param_name}' in function definition - No duplicates allowed! (¬_¬)"
        )


class DuplicateKeyError(RuntimeError):
    """Raised when dictionary literal has duplicate keys"""
    def __init__(self, key):
        super().__init__(
            f"Duplicate key '{key}' in dictionary literal - Keys must be unique! (>_<)"
        )


class InvalidEscapeSequenceError(LexerError):
    """Raised when invalid escape sequence in string"""
    def __init__(self, sequence, line, column):
        super().__init__(
            f"Invalid escape sequence '\\{sequence}' in string - Unknown escape! (O_o)",
            line, column
        )


class NestedFunctionError(ParserError):
    """Raised when function defined inside another function"""
    def __init__(self):
        super().__init__(
            "Nested function definitions are not supported. "
            "Define functions at the top level only. No function inception! (¬‿¬)"
        )


class InvalidBreakLevelError(RuntimeError):
    """Raised when break/continue used incorrectly"""
    def __init__(self, statement):
        super().__init__(
            f"'{statement}' can only be used directly inside loop body - Wrong context! (._. )"
        )


class TooManyArgumentsError(RuntimeError):
    """Raised when too many arguments passed"""
    def __init__(self, func_name, max_args, got):
        super().__init__(
            f"Function '{func_name}' accepts at most {max_args} argument(s), "
            f"but {got} were provided - Too many args! (O_o)"
        )


class TooFewArgumentsError(RuntimeError):
    """Raised when too few arguments passed"""
    def __init__(self, func_name, min_args, got):
        super().__init__(
            f"Function '{func_name}' requires at least {min_args} argument(s), "
            f"but only {got} were provided - Not enough args! (>_<)"
        )


# ==================== HELPER FUNCTIONS ====================

def get_type_name(value):
    """Get user-friendly type name for error messages"""
    if isinstance(value, bool):
        return "bool"
    elif isinstance(value, int):
        return "int"
    elif isinstance(value, float):
        return "float"
    elif isinstance(value, str):
        return "string"
    elif isinstance(value, list):
        return "array"
    elif isinstance(value, dict):
        return "dictionary"
    elif isinstance(value, set):
        return "set"
    elif callable(value):
        return "function"
    else:
        return type(value).__name__


def format_value(value, max_length=50):
    """Format value for error messages"""
    if isinstance(value, str):
        if len(value) > max_length:
            return f'"{value[:max_length]}..."'
        return f'"{value}"'
    elif isinstance(value, list):
        if len(str(value)) > max_length:
            return f"[array with {len(value)} elements]"
        return str(value)
    elif isinstance(value, dict):
        if len(str(value)) > max_length:
            return f"{{dictionary with {len(value)} keys}}"
        return str(value)
    elif isinstance(value, set):
        if len(str(value)) > max_length:
            return f"{{set with {len(value)} elements}}"
        return str(value)
    else:
        return str(value)
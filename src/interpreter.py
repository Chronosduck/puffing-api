"""
Interpreter for Puffing Language
Executes the Abstract Syntax Tree (AST)
UPDATED: Full N-dimensional array + N-dimensional dictionary + Set support
"""

import math
import sys
from src.lexer import TokenType
from src.ast_nodes import (
    NumberNode, StringNode, BoolNode, ArrayNode, SetNode, IndexAccessNode, IndexAssignNode,
    VarAssignNode, VarAccessNode, VarReassignNode, CompoundAssignNode,
    PrintNode, IfNode, BlockNode,
    BinaryOpNode, UnaryOpNode, TypeCastNode,
    InputNode, LibImportNode, FormatNode, FunctionCallNode,
    ForLoopNode, RangeNode, WhileLoopNode, DoWhileLoopNode, BreakNode, ContinueNode,
    IncrementNode, FunctionDefNode, LambdaNode, ReturnNode, DestructureAssignNode, DictNode
)
from src.errors import VariableNotDefinedError, RuntimeError as PuffingRuntimeError


class BreakException(Exception):
    """Exception to handle break statements"""
    pass


class ContinueException(Exception):
    """Exception to handle continue statements"""
    pass


class ReturnException(Exception):
    """Exception to handle return statements"""
    def __init__(self, value):
        self.value = value


class PuffingFunction:
    """Runtime representation of a user-defined function"""
    def __init__(self, name, params, body, interpreter):
        self.name = name
        self.params = params
        self.body = body
        self.interpreter = interpreter
    
    def call(self, args):
        """Execute the function with given arguments"""
        if len(args) != len(self.params):
            raise PuffingRuntimeError(
                f"Function '{self.name}' expects {len(self.params)} arguments, "
                f"got {len(args)}"
            )
        
        # Save current variable state
        saved_vars = self.interpreter.variables.copy()
        
        try:
            # Bind parameters to arguments
            for param, arg in zip(self.params, args):
                self.interpreter.variables[param] = arg
            
            # Execute function body
            result = self.interpreter.eval(self.body)
            return result
        
        except ReturnException as e:
            return e.value
        
        finally:
            # Restore previous variable state
            self.interpreter.variables = saved_vars
    
    def __repr__(self):
        return f"<function {self.name}>"
    
    def __call__(self, *args):
        """Allow calling like a Python function"""
        return self.call(list(args))


class PuffingLambda:
    """Runtime representation of a lambda function"""
    def __init__(self, params, body, is_expression, interpreter):
        self.params = params
        self.body = body
        self.is_expression = is_expression
        self.interpreter = interpreter
    
    def call(self, args):
        """Execute the lambda with given arguments"""
        if len(args) != len(self.params):
            raise PuffingRuntimeError(
                f"Lambda expects {len(self.params)} arguments, got {len(args)}"
            )
        
        # Save current variable state
        saved_vars = self.interpreter.variables.copy()
        
        try:
            # Bind parameters to arguments
            for param, arg in zip(self.params, args):
                self.interpreter.variables[param] = arg
            
            # Execute lambda body
            if self.is_expression:
                # Single expression - return its value
                result = self.interpreter.eval(self.body)
                return result
            else:
                # Block - execute normally
                result = self.interpreter.eval(self.body)
                return result
        
        except ReturnException as e:
            return e.value
        
        finally:
            # Restore previous variable state
            self.interpreter.variables = saved_vars
    
    def __repr__(self):
        return f"<lambda ({len(self.params)} params)>"
    
    def __call__(self, *args):
        """Allow calling like a Python function"""
        return self.call(list(args))


class Interpreter:
    def __init__(self):
        self.variables = {}
        self.constants = set()  # Track constant variables
        self.libraries = {}  # Track imported libraries

    def run(self, node):
        """Execute the AST"""
        return self.eval(node)

    def eval(self, node):
        """Evaluate a node"""
        
        # Function definition
        if isinstance(node, FunctionDefNode):
            func = PuffingFunction(node.name, node.params, node.body, self)
            self.variables[node.name] = func
            return func
        
        # Lambda function
        if isinstance(node, LambdaNode):
            return PuffingLambda(node.params, node.body, node.is_expression, self)
        
        # Return statement
        if isinstance(node, ReturnNode):
            value = self.eval(node.value_node) if node.value_node else None
            raise ReturnException(value)
        
        # Literal values
        if isinstance(node, NumberNode):
            return node.value

        if isinstance(node, StringNode):
            return node.value

        if isinstance(node, BoolNode):
            return node.value

        # Array literal
        if isinstance(node, ArrayNode):
            return [self.eval(elem) for elem in node.elements]

        # Set literal
        if isinstance(node, SetNode):
            elements = [self.eval(elem) for elem in node.elements]
            # Ensure all elements are hashable
            hashable_elements = []
            for elem in elements:
                if not isinstance(elem, (str, int, float, bool, type(None))):
                    raise PuffingRuntimeError(
                        f"Set elements must be immutable (strings, numbers, bools), "
                        f"got {type(elem).__name__}"
                    )
                hashable_elements.append(elem)
            return set(hashable_elements)

        # Dictionary literal
        if isinstance(node, DictNode):
            result = {}
            for key_node, value_node in node.pairs:
                key = self.eval(key_node)
                value = self.eval(value_node)
                
                # Keys must be hashable (strings, numbers, bools)
                if not isinstance(key, (str, int, float, bool)):
                    raise PuffingRuntimeError(
                        f"Dictionary keys must be strings, numbers, or bools, "
                        f"got {type(key).__name__}"
                    )
                
                result[key] = value
            return result

        # Index/Key access - FIXED for negative indexing and dictionary access
        if isinstance(node, IndexAccessNode):
            container_value = self.eval(node.container_node)
            key = self.eval(node.key_node)
    
            # Handle arrays and strings (1-based indexing with negative support)
            if isinstance(container_value, (list, str)):
                if not isinstance(key, int):
                    raise PuffingRuntimeError(
                        f"Array/string index must be an integer, got {type(key).__name__}"
                    )
                
                # Handle negative indexing (Python-style: -1 is last, -2 is second to last)
                if key < 0:
                    try:
                        return container_value[key]
                    except IndexError:
                        raise PuffingRuntimeError(
                            f"Index {key} out of range for {type(container_value).__name__} "
                            f"of length {len(container_value)}"
                        )
                else:
                    # Positive index: convert 1-based to 0-based
                    zero_based_index = key - 1
                
                    if zero_based_index < 0:
                        raise PuffingRuntimeError(f"Index {key} is invalid (indices start at 1)")
                
                    try:
                        return container_value[zero_based_index]
                    except IndexError:
                        raise PuffingRuntimeError(
                            f"Index {key} out of range for {type(container_value).__name__} "
                            f"of length {len(container_value)}"
                        )
            
            # Handle dictionaries
            elif isinstance(container_value, dict):
                if key not in container_value:
                    raise PuffingRuntimeError(f"Key '{key}' not found in dictionary")
                return container_value[key]
            
            else:
                raise PuffingRuntimeError(
                    f"Cannot index {type(container_value).__name__} "
                    f"(only arrays, strings, and dictionaries are indexable)"
                )

        # Index/Key assignment: variable[index] as value OR dict[key] as value (N-dimensional)
        if isinstance(node, IndexAssignNode):
            # Handle N-dimensional index/key assignment
            left_expr = node.container_node
            new_value = self.eval(node.value_node)
            
            # Build the access path by traversing IndexAccessNode chain
            path = []
            current = left_expr
            
            while isinstance(current, IndexAccessNode):
                path.insert(0, self.eval(current.key_node))
                current = current.container_node
            
            # Current should be a VarAccessNode now
            if not isinstance(current, VarAccessNode):
                raise PuffingRuntimeError("Can only assign to variable indices/keys")
            
            var_name = current.name
            
            if var_name not in self.variables:
                raise VariableNotDefinedError(var_name)
            
            if var_name in self.constants:
                raise PuffingRuntimeError(f"Cannot modify constant '{var_name}'")
            
            # Navigate to the target container
            target = self.variables[var_name]
            
            # If only one key/index, handle simple case
            if len(path) == 1:
                key = path[0]
                
                # Array assignment (1-based or negative)
                if isinstance(target, list):
                    if not isinstance(key, int):
                        raise PuffingRuntimeError(
                            f"Array index must be an integer, got {type(key).__name__}"
                        )
                    
                    # Handle negative indexing
                    if key < 0:
                        try:
                            target[key] = new_value
                            return new_value
                        except IndexError:
                            raise PuffingRuntimeError(
                                f"Index {key} out of range for array of length {len(target)}"
                            )
                    else:
                        # Positive index: convert 1-based to 0-based
                        zero_based_idx = key - 1
                        
                        if zero_based_idx < 0:
                            raise PuffingRuntimeError(f"Index {key} is invalid (indices start at 1)")
                        
                        try:
                            target[zero_based_idx] = new_value
                            return new_value
                        except IndexError:
                            raise PuffingRuntimeError(
                                f"Index {key} out of range for array of length {len(target)}"
                            )
                
                # Dictionary assignment
                elif isinstance(target, dict):
                    if not isinstance(key, (str, int, float, bool)):
                        raise PuffingRuntimeError(
                            f"Dictionary keys must be strings, numbers, or bools, "
                            f"got {type(key).__name__}"
                        )
                    target[key] = new_value
                    return new_value
                
                else:
                    raise PuffingRuntimeError(
                        f"Cannot assign to index/key of {type(target).__name__} "
                        f"(only arrays and dictionaries support assignment)"
                    )
            
            # Navigate through all but the last key/index
            for key in path[:-1]:
                # Array navigation
                if isinstance(target, list):
                    if not isinstance(key, int):
                        raise PuffingRuntimeError(
                            f"Array index must be an integer, got {type(key).__name__}"
                        )
                    
                    # Handle negative indexing
                    if key < 0:
                        try:
                            target = target[key]
                        except IndexError:
                            raise PuffingRuntimeError(
                                f"Index {key} out of range for array of length {len(target)}"
                            )
                    else:
                        # Positive index: convert 1-based to 0-based
                        zero_based_idx = key - 1
                        
                        if zero_based_idx < 0:
                            raise PuffingRuntimeError(f"Index {key} is invalid (indices start at 1)")
                        
                        try:
                            target = target[zero_based_idx]
                        except IndexError:
                            raise PuffingRuntimeError(
                                f"Index {key} out of range for array of length {len(target)}"
                            )
                
                # Dictionary navigation
                elif isinstance(target, dict):
                    if key not in target:
                        raise PuffingRuntimeError(f"Key '{key}' not found in dictionary")
                    target = target[key]
                
                else:
                    raise PuffingRuntimeError(
                        f"Cannot index {type(target).__name__} "
                        f"(expected array or dictionary for nested indexing)"
                    )
            
            # Assign to the last key/index
            final_key = path[-1]
            
            # Array assignment
            if isinstance(target, list):
                if not isinstance(final_key, int):
                    raise PuffingRuntimeError(
                        f"Array index must be an integer, got {type(final_key).__name__}"
                    )
                
                # Handle negative indexing for final assignment
                if final_key < 0:
                    try:
                        target[final_key] = new_value
                        return new_value
                    except IndexError:
                        raise PuffingRuntimeError(
                            f"Index {final_key} out of range for array of length {len(target)}"
                        )
                else:
                    # Positive index: convert 1-based to 0-based
                    zero_based_final = final_key - 1
                    
                    if zero_based_final < 0:
                        raise PuffingRuntimeError(f"Index {final_key} is invalid (indices start at 1)")
                    
                    try:
                        target[zero_based_final] = new_value
                        return new_value
                    except IndexError:
                        raise PuffingRuntimeError(
                            f"Index {final_key} out of range for array of length {len(target)}"
                        )
            
            # Dictionary assignment
            elif isinstance(target, dict):
                if not isinstance(final_key, (str, int, float, bool)):
                    raise PuffingRuntimeError(
                        f"Dictionary keys must be strings, numbers, or bools, "
                        f"got {type(final_key).__name__}"
                    )
                target[final_key] = new_value
                return new_value
            
            else:
                raise PuffingRuntimeError(
                    f"Cannot assign to index/key of {type(target).__name__} "
                    f"(only arrays and dictionaries support assignment)"
                )

        # Library import
        if isinstance(node, LibImportNode):
            self.import_library(node.module_path)
            return None

        # Variable assignment
        if isinstance(node, VarAssignNode):
            value = self.eval(node.value_node)
            self.variables[node.name] = value
            if node.constant:
                self.constants.add(node.name)
            return value

        # Destructuring assignment
        if isinstance(node, DestructureAssignNode):
            value = self.eval(node.value_node)
            
            # Value must be iterable (array, string, etc.)
            if not hasattr(value, '__iter__') or isinstance(value, dict):
                raise PuffingRuntimeError(
                    f"Cannot destructure {type(value).__name__} "
                    f"(expected array or iterable)"
                )
            
            # Convert to list if needed
            if isinstance(value, str):
                value_list = list(value)
            else:
                value_list = list(value)
            
            # Check if we have enough values
            if len(value_list) < len(node.var_names):
                raise PuffingRuntimeError(
                    f"Not enough values to unpack: expected {len(node.var_names)}, "
                    f"got {len(value_list)}"
                )
            
            # Assign each variable
            for i, var_name in enumerate(node.var_names):
                self.variables[var_name] = value_list[i]
                if node.constant:
                    self.constants.add(var_name)
            
            return value_list

        # Variable reassignment
        if isinstance(node, VarReassignNode):
            if node.name not in self.variables:
                raise VariableNotDefinedError(node.name)
            if node.name in self.constants:
                raise PuffingRuntimeError(f"Cannot reassign constant '{node.name}'")
            value = self.eval(node.value_node)
            self.variables[node.name] = value
            return value

        # Compound assignment (+5x, -3x, *2x, etc.)
        if isinstance(node, CompoundAssignNode):
            if node.name not in self.variables:
                raise VariableNotDefinedError(node.name)
            if node.name in self.constants:
                raise PuffingRuntimeError(f"Cannot reassign constant '{node.name}'")
            
            current_value = self.variables[node.name]
            compound_value = self.eval(node.value_node)
            
            if node.operator == TokenType.PLUS:
                self.variables[node.name] = current_value + compound_value
            elif node.operator == TokenType.MINUS:
                self.variables[node.name] = current_value - compound_value
            elif node.operator == TokenType.MULTIPLY:
                self.variables[node.name] = current_value * compound_value
            elif node.operator == TokenType.DIVIDE:
                if compound_value == 0:
                    raise PuffingRuntimeError("Division by zero")
                self.variables[node.name] = current_value / compound_value
            elif node.operator == TokenType.MODULO:
                self.variables[node.name] = current_value % compound_value
            elif node.operator == TokenType.POWER:
                self.variables[node.name] = current_value ** compound_value
            else:
                raise PuffingRuntimeError(f"Unknown compound operator: {node.operator}")
            
            return self.variables[node.name]

        # Increment/Decrement (i++, ++i, i--, --i)
        if isinstance(node, IncrementNode):
            if node.name not in self.variables:
                raise VariableNotDefinedError(node.name)
            if node.name in self.constants:
                raise PuffingRuntimeError(f"Cannot modify constant '{node.name}'")
            
            current_value = self.variables[node.name]
            
            if node.operator == TokenType.INCREMENT:
                new_value = current_value + 1
            elif node.operator == TokenType.DECREMENT:
                new_value = current_value - 1
            else:
                raise PuffingRuntimeError(f"Unknown increment operator: {node.operator}")
            
            self.variables[node.name] = new_value
            
            # Return old value for postfix, new value for prefix
            return new_value if node.prefix else current_value

        # Variable access
        if isinstance(node, VarAccessNode):
            if node.name not in self.variables:
                raise VariableNotDefinedError(node.name)
            return self.variables[node.name]

        # Range function
        if isinstance(node, RangeNode):
            start = self.eval(node.start_node)
            stop = self.eval(node.stop_node) if node.stop_node else None
            step = self.eval(node.step_node) if node.step_node else 1
            
            # Handle single argument case: range(n) means 1 to n (1-based)
            if stop is None:
                stop = start
                start = 1
            
            return list(range(int(start), int(stop) + 1, int(step)))

        # Function call
        if isinstance(node, FunctionCallNode):
            return self.eval_function_call(node)

        # Binary operations
        if isinstance(node, BinaryOpNode):
            return self.eval_binary_op(node)

        # Unary operations
        if isinstance(node, UnaryOpNode):
            return self.eval_unary_op(node)

        # Type casting
        if isinstance(node, TypeCastNode):
            return self.eval_type_cast(node)

        # Number formatting
        if isinstance(node, FormatNode):
            return self.eval_format(node)

        # Input statement
        if isinstance(node, InputNode):
            return self.eval_input(node)

        # Print statement
        if isinstance(node, PrintNode):
            values = []
            for value_node in node.value_nodes:
                val = self.eval(value_node)
                # Format arrays, sets, and dictionaries nicely
                if isinstance(val, list):
                    formatted_elements = []
                    for elem in val:
                        if isinstance(elem, str):
                            formatted_elements.append(f'"{elem}"')
                        else:
                            formatted_elements.append(str(elem))
                    values.append('[' + ', '.join(formatted_elements) + ']')
                elif isinstance(val, set):
                    formatted_elements = []
                    for elem in sorted(val, key=lambda x: (type(x).__name__, x)):
                        if isinstance(elem, str):
                            formatted_elements.append(f'"{elem}"')
                        else:
                            formatted_elements.append(str(elem))
                    values.append('#{' + ', '.join(formatted_elements) + '}')
                elif isinstance(val, dict):
                    formatted_pairs = []
                    for k, v in val.items():
                        key_str = f'"{k}"' if isinstance(k, str) else str(k)
                        val_str = f'"{v}"' if isinstance(v, str) else str(v)
                        formatted_pairs.append(f'{key_str}: {val_str}')
                    values.append('{' + ', '.join(formatted_pairs) + '}')
                else:
                    values.append(str(val))
            
            output = ''.join(values)
            sys.stdout.write(output)
            sys.stdout.flush()
            return None

        # If statement
        if isinstance(node, IfNode):
            condition = self.eval(node.condition_node)

            # Truthy evaluation
            if self.is_truthy(condition):
                return self.eval(node.true_block)
            
            # Check elif blocks
            for elif_condition, elif_block in node.elif_blocks:
                if self.is_truthy(self.eval(elif_condition)):
                    return self.eval(elif_block)
            
            # Else block
            if node.false_block:
                return self.eval(node.false_block)
            return None

        # For loop (Python-style)
        if isinstance(node, ForLoopNode):
            # Evaluate the iterable
            iterable = self.eval(node.iterable_node)
            
            if not hasattr(iterable, '__iter__'):
                raise PuffingRuntimeError("For loop requires an iterable")

            result = None

            # Save previous loop variable value if it exists
            had_var = node.var_name in self.variables
            old_var = self.variables.get(node.var_name)

            try:
                for value in iterable:
                    try:
                        # Set loop variable to current value
                        self.variables[node.var_name] = value
                        result = self.eval(node.body)
                    except ContinueException:
                        continue
            except BreakException:
                pass
            finally:
                # Restore previous loop variable value or remove it
                if had_var:
                    self.variables[node.var_name] = old_var
                else:
                    self.variables.pop(node.var_name, None)

            return result

        # While loop
        if isinstance(node, WhileLoopNode):
            result = None
            
            try:
                while self.is_truthy(self.eval(node.condition_node)):
                    try:
                        result = self.eval(node.body)
                    except ContinueException:
                        continue
            except BreakException:
                pass

            return result

        # Do-while loop
        if isinstance(node, DoWhileLoopNode):
            result = None
            
            try:
                while True:
                    try:
                        result = self.eval(node.body)
                    except ContinueException:
                        pass
                    
                    if not self.is_truthy(self.eval(node.condition_node)):
                        break
            except BreakException:
                pass

            return result

        # Break statement
        if isinstance(node, BreakNode):
            raise BreakException()

        # Continue statement
        if isinstance(node, ContinueNode):
            raise ContinueException()

        # Block of statements
        if isinstance(node, BlockNode):
            result = None
            for stmt in node.statements:
                result = self.eval(stmt)
            return result

        raise PuffingRuntimeError(f"Unknown AST node: {node}")

    def eval_binary_op(self, node):
        """Evaluate binary operation"""
        left = self.eval(node.left)
        right = self.eval(node.right)
        op = node.op

        # Arithmetic operations
        if op == TokenType.PLUS:
            # Support string concatenation and array concatenation
            if isinstance(left, str) or isinstance(right, str):
                return str(left) + str(right)
            if isinstance(left, list) and isinstance(right, list):
                return left + right
            return left + right
        elif op == TokenType.MINUS:
            return left - right
        elif op == TokenType.MULTIPLY:
            return left * right
        elif op == TokenType.DIVIDE:
            if right == 0:
                raise PuffingRuntimeError("Division by zero")
            return left / right
        elif op == TokenType.MODULO:
            return left % right
        elif op == TokenType.POWER:
            return left ** right

        # Comparison operations
        elif op == TokenType.EQUAL:
            return left == right
        elif op == TokenType.NOT_EQUAL:
            return left != right
        elif op == TokenType.LESS:
            return left < right
        elif op == TokenType.GREATER:
            return left > right
        elif op == TokenType.LESS_EQUAL:
            return left <= right
        elif op == TokenType.GREATER_EQUAL:
            return left >= right

        # Logical operations
        elif op == TokenType.AND:
            return self.is_truthy(left) and self.is_truthy(right)
        elif op == TokenType.OR:
            return self.is_truthy(left) or self.is_truthy(right)

        raise PuffingRuntimeError(f"Unknown binary operator: {op}")

    def eval_unary_op(self, node):
        """Evaluate unary operation"""
        operand = self.eval(node.operand)
        op = node.op

        if op == TokenType.MINUS:
            return -operand
        elif op == TokenType.NOT:
            return not self.is_truthy(operand)

        raise PuffingRuntimeError(f"Unknown unary operator: {op}")

    def eval_type_cast(self, node):
        """Evaluate type casting"""
        value = self.eval(node.node)
        target_type = node.target_type

        try:
            if target_type == TokenType.INT:
                return int(value)
            elif target_type == TokenType.FLOAT:
                return float(value)
            elif target_type == TokenType.STR:
                return str(value)
            elif target_type == TokenType.BOOL:
                return self.is_truthy(value)
        except (ValueError, TypeError) as e:
            raise PuffingRuntimeError(f"Cannot cast {value} to {target_type}: {e}")

        raise PuffingRuntimeError(f"Unknown type: {target_type}")

    def eval_format(self, node):
        """Evaluate number formatting"""
        value = self.eval(node.node)
        precision = node.precision

        if not isinstance(value, (int, float)):
            raise PuffingRuntimeError(f"Cannot format non-numeric value: {value}")

        return f"{value:.{precision}f}"

    def eval_input(self, node):
        """Evaluate input statement"""
        user_input = input()

        # If no type specified, return as string
        if node.input_type is None:
            return user_input

        # Cast to specified type
        try:
            if node.input_type == TokenType.INT:
                return int(user_input)
            elif node.input_type == TokenType.FLOAT:
                return float(user_input)
            elif node.input_type == TokenType.STR:
                return str(user_input)
            elif node.input_type == TokenType.BOOL:
                return user_input.lower() in ('true', '1', 'yes', 'y')
        except ValueError as e:
            raise PuffingRuntimeError(f"Invalid input for type {node.input_type}: {e}")

        return user_input

    def import_library(self, module_path):
        """Import a library module"""
        if module_path == "math.main":
            # Import math library functions
            self.libraries['math'] = {
                'sqrt': math.sqrt,
                'sin': math.sin,
                'cos': math.cos,
                'tan': math.tan,
                'asin': math.asin,
                'acos': math.acos,
                'atan': math.atan,
                'log': math.log,
                'log10': math.log10,
                'log2': math.log2,
                'exp': math.exp,
                'ceil': math.ceil,
                'floor': math.floor,
                'abs': math.fabs,
                'round': round,
                'pow': math.pow,
                'pi': math.pi,
                'e': math.e,
                'tau': math.tau,
            }
            for name, func in self.libraries['math'].items():
                self.variables[name] = func
        
        elif module_path == "string.main":
            # Import string library functions
            self.libraries['string'] = {
                'upper': lambda s: str(s).upper(),
                'lower': lambda s: str(s).lower(),
                'capitalize': lambda s: str(s).capitalize(),
                'title': lambda s: str(s).title(),
                'strip': lambda s: str(s).strip(),
                'lstrip': lambda s: str(s).lstrip(),
                'rstrip': lambda s: str(s).rstrip(),
                'split': lambda s, sep=' ': str(s).split(sep),
                'replace': lambda s, old, new: str(s).replace(old, new),
                'startswith': lambda s, prefix: str(s).startswith(prefix),
                'endswith': lambda s, suffix: str(s).endswith(suffix),
                'find': lambda s, sub: str(s).find(sub),
                'count': lambda s, sub: str(s).count(sub),
                'repeat': lambda s, n: str(s) * int(n),
                'reverse_str': lambda s: str(s)[::-1],
                'is_alpha': lambda s: str(s).isalpha(),
                'is_digit': lambda s: str(s).isdigit(),
                'is_alnum': lambda s: str(s).isalnum(),
                'is_lower': lambda s: str(s).islower(),
                'is_upper': lambda s: str(s).isupper(),
                'is_space': lambda s: str(s).isspace(),
                'substring': lambda s, start, end=None: str(s)[start:end],
                'char_at': lambda s, i: str(s)[i] if 0 <= i < len(str(s)) else "",
                'pad_left': lambda s, width, char=' ': str(s).rjust(width, char),
                'pad_right': lambda s, width, char=' ': str(s).ljust(width, char),
                'trim': lambda s, chars=None: str(s).strip(chars),
            }
            for name, func in self.libraries['string'].items():
                self.variables[name] = func
        
        else:
            raise PuffingRuntimeError(f"Unknown library: {module_path}")

    def is_truthy(self, value):
        """Determine if a value is truthy"""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        if isinstance(value, (list, dict, set)):
            return len(value) > 0
        return True

    def eval_function_call(self, node):
        """Evaluate function call"""
        func_name = node.name
        
        # Handle immediately invoked lambda: (lamb (x) => x + 1)(5)
        if isinstance(func_name, LambdaNode):
            lambda_func = PuffingLambda(
                func_name.params,
                func_name.body,
                func_name.is_expression,
                self
            )
            args = [self.eval(arg) for arg in node.args]
            try:
                return lambda_func.call(args)
            except ReturnException as e:
                return e.value
        
        # Check if it's a user-defined function or lambda variable
        if func_name in self.variables:
            func = self.variables[func_name]
            
            if isinstance(func, (PuffingFunction, PuffingLambda)):
                args = [self.eval(arg) for arg in node.args]
                try:
                    return func.call(args)
                except ReturnException as e:
                    return e.value
        
        # ==================== BUILT-IN FUNCTIONS ====================
        
        # len() - works for arrays, strings, dictionaries, and sets
        if func_name == "len":
            if len(node.args) != 1:
                raise PuffingRuntimeError("len() takes exactly 1 argument")
            value = self.eval(node.args[0])
            if not hasattr(value, '__len__'):
                raise PuffingRuntimeError(f"Object of type {type(value).__name__} has no len()")
            return len(value)
        
        # ==================== SET METHODS ====================
        
        if func_name == "set_add":
            if len(node.args) != 2:
                raise PuffingRuntimeError("set_add() takes exactly 2 arguments (set, value)")
            
            set_arg = node.args[0]
            if isinstance(set_arg, VarAccessNode):
                var_name = set_arg.name
                if var_name not in self.variables:
                    raise VariableNotDefinedError(f"Variable '{var_name}' not defined")
                if var_name in self.constants:
                    raise PuffingRuntimeError(f"Cannot modify constant '{var_name}'")
                set_val = self.variables[var_name]
            else:
                set_val = self.eval(set_arg)
            
            value = self.eval(node.args[1])
            
            if not isinstance(set_val, set):
                raise PuffingRuntimeError("set_add() requires a set")
            if not isinstance(value, (str, int, float, bool, type(None))):
                raise PuffingRuntimeError(
                    f"Set elements must be immutable (strings, numbers, bools), "
                    f"got {type(value).__name__}"
                )
            
            set_val.add(value)
            return set_val
        
        if func_name == "set_remove":
            if len(node.args) != 2:
                raise PuffingRuntimeError("set_remove() takes exactly 2 arguments (set, value)")
            
            set_arg = node.args[0]
            if isinstance(set_arg, VarAccessNode):
                var_name = set_arg.name
                if var_name not in self.variables:
                    raise VariableNotDefinedError(f"Variable '{var_name}' not defined")
                if var_name in self.constants:
                    raise PuffingRuntimeError(f"Cannot modify constant '{var_name}'")
                set_val = self.variables[var_name]
            else:
                set_val = self.eval(set_arg)
            
            value = self.eval(node.args[1])
            
            if not isinstance(set_val, set):
                raise PuffingRuntimeError("set_remove() requires a set")
            
            if value not in set_val:
                raise PuffingRuntimeError(f"Value '{value}' not found in set")
            
            set_val.remove(value)
            return set_val
        
        if func_name == "set_discard":
            """Like remove but doesn't error if element not found"""
            if len(node.args) != 2:
                raise PuffingRuntimeError("set_discard() takes exactly 2 arguments (set, value)")
            
            set_arg = node.args[0]
            if isinstance(set_arg, VarAccessNode):
                var_name = set_arg.name
                if var_name not in self.variables:
                    raise VariableNotDefinedError(f"Variable '{var_name}' not defined")
                if var_name in self.constants:
                    raise PuffingRuntimeError(f"Cannot modify constant '{var_name}'")
                set_val = self.variables[var_name]
            else:
                set_val = self.eval(set_arg)
            
            value = self.eval(node.args[1])
            
            if not isinstance(set_val, set):
                raise PuffingRuntimeError("set_discard() requires a set")
            
            set_val.discard(value)
            return set_val
        
        if func_name == "set_clear":
            if len(node.args) != 1:
                raise PuffingRuntimeError("set_clear() takes exactly 1 argument")
            
            set_arg = node.args[0]
            if isinstance(set_arg, VarAccessNode):
                var_name = set_arg.name
                if var_name not in self.variables:
                    raise VariableNotDefinedError(f"Variable '{var_name}' not defined")
                if var_name in self.constants:
                    raise PuffingRuntimeError(f"Cannot modify constant '{var_name}'")
                set_val = self.variables[var_name]
            else:
                set_val = self.eval(set_arg)
            
            if not isinstance(set_val, set):
                raise PuffingRuntimeError("set_clear() requires a set")
            
            set_val.clear()
            return set_val
        
        if func_name == "set_contains":
            if len(node.args) != 2:
                raise PuffingRuntimeError("set_contains() takes exactly 2 arguments (set, value)")
            
            set_val = self.eval(node.args[0])
            value = self.eval(node.args[1])
            
            if not isinstance(set_val, set):
                raise PuffingRuntimeError("set_contains() requires a set")
            
            return value in set_val
        
        if func_name == "set_union":
            """Merge multiple sets - returns new set"""
            if len(node.args) < 2:
                raise PuffingRuntimeError("set_union() takes at least 2 arguments")
            
            result = set()
            for arg in node.args:
                set_val = self.eval(arg)
                if not isinstance(set_val, set):
                    raise PuffingRuntimeError("set_union() requires all arguments to be sets")
                result = result.union(set_val)
            
            return result
        
        if func_name == "set_intersection":
            """Get common elements - returns new set"""
            if len(node.args) < 2:
                raise PuffingRuntimeError("set_intersection() takes at least 2 arguments")
            
            result = self.eval(node.args[0])
            if not isinstance(result, set):
                raise PuffingRuntimeError("set_intersection() requires all arguments to be sets")
            
            for i in range(1, len(node.args)):
                set_val = self.eval(node.args[i])
                if not isinstance(set_val, set):
                    raise PuffingRuntimeError("set_intersection() requires all arguments to be sets")
                result = result.intersection(set_val)
            
            return result
        
        if func_name == "set_difference":
            """Elements in first set but not in others - returns new set"""
            if len(node.args) < 2:
                raise PuffingRuntimeError("set_difference() takes at least 2 arguments")
            
            result = self.eval(node.args[0])
            if not isinstance(result, set):
                raise PuffingRuntimeError("set_difference() requires all arguments to be sets")
            
            for i in range(1, len(node.args)):
                set_val = self.eval(node.args[i])
                if not isinstance(set_val, set):
                    raise PuffingRuntimeError("set_difference() requires all arguments to be sets")
                result = result.difference(set_val)
            
            return result
        
        if func_name == "set_symmetric_difference":
            """Elements in either set but not both - returns new set"""
            if len(node.args) != 2:
                raise PuffingRuntimeError("set_symmetric_difference() takes exactly 2 arguments")
            
            set1 = self.eval(node.args[0])
            set2 = self.eval(node.args[1])
            
            if not isinstance(set1, set) or not isinstance(set2, set):
                raise PuffingRuntimeError("set_symmetric_difference() requires both arguments to be sets")
            
            return set1.symmetric_difference(set2)
        
        if func_name == "set_is_subset":
            """Check if first set is subset of second"""
            if len(node.args) != 2:
                raise PuffingRuntimeError("set_is_subset() takes exactly 2 arguments")
            
            set1 = self.eval(node.args[0])
            set2 = self.eval(node.args[1])
            
            if not isinstance(set1, set) or not isinstance(set2, set):
                raise PuffingRuntimeError("set_is_subset() requires both arguments to be sets")
            
            return set1.issubset(set2)
        
        if func_name == "set_is_superset":
            """Check if first set is superset of second"""
            if len(node.args) != 2:
                raise PuffingRuntimeError("set_is_superset() takes exactly 2 arguments")
            
            set1 = self.eval(node.args[0])
            set2 = self.eval(node.args[1])
            
            if not isinstance(set1, set) or not isinstance(set2, set):
                raise PuffingRuntimeError("set_is_superset() requires both arguments to be sets")
            
            return set1.issuperset(set2)
        
        if func_name == "set_is_disjoint":
            """Check if two sets have no elements in common"""
            if len(node.args) != 2:
                raise PuffingRuntimeError("set_is_disjoint() takes exactly 2 arguments")
            
            set1 = self.eval(node.args[0])
            set2 = self.eval(node.args[1])
            
            if not isinstance(set1, set) or not isinstance(set2, set):
                raise PuffingRuntimeError("set_is_disjoint() requires both arguments to be sets")
            
            return set1.isdisjoint(set2)
        
        if func_name == "set_copy":
            """Create a shallow copy of the set"""
            if len(node.args) != 1:
                raise PuffingRuntimeError("set_copy() takes exactly 1 argument")
            
            set_val = self.eval(node.args[0])
            
            if not isinstance(set_val, set):
                raise PuffingRuntimeError("set_copy() requires a set")
            
            return set_val.copy()
        
        if func_name == "set_to_array":
            """Convert set to array (list)"""
            if len(node.args) != 1:
                raise PuffingRuntimeError("set_to_array() takes exactly 1 argument")
            
            set_val = self.eval(node.args[0])
            
            if not isinstance(set_val, set):
                raise PuffingRuntimeError("set_to_array() requires a set")
            
            return list(set_val)
        
        if func_name == "array_to_set":
            """Convert array to set (removes duplicates)"""
            if len(node.args) != 1:
                raise PuffingRuntimeError("array_to_set() takes exactly 1 argument")
            
            array_val = self.eval(node.args[0])
            
            if not isinstance(array_val, list):
                raise PuffingRuntimeError("array_to_set() requires an array")
            
            # Check all elements are hashable
            for elem in array_val:
                if not isinstance(elem, (str, int, float, bool, type(None))):
                    raise PuffingRuntimeError(
                        f"Cannot convert array to set: elements must be immutable, "
                        f"got {type(elem).__name__}"
                    )
            
            return set(array_val)
        
        # ==================== DICTIONARY METHODS ====================
        
        if func_name == "keys":
            if len(node.args) != 1:
                raise PuffingRuntimeError("keys() takes exactly 1 argument")
            value = self.eval(node.args[0])
            if not isinstance(value, dict):
                raise PuffingRuntimeError("keys() requires a dictionary")
            return list(value.keys())
        
        if func_name == "values":
            if len(node.args) != 1:
                raise PuffingRuntimeError("values() takes exactly 1 argument")
            value = self.eval(node.args[0])
            if not isinstance(value, dict):
                raise PuffingRuntimeError("values() requires a dictionary")
            return list(value.values())
        
        if func_name == "items":
            if len(node.args) != 1:
                raise PuffingRuntimeError("items() takes exactly 1 argument")
            value = self.eval(node.args[0])
            if not isinstance(value, dict):
                raise PuffingRuntimeError("items() requires a dictionary")
            return [[k, v] for k, v in value.items()]
        
        if func_name == "has_key":
            if len(node.args) != 2:
                raise PuffingRuntimeError("has_key() takes exactly 2 arguments (dict, key)")
            dict_val = self.eval(node.args[0])
            key = self.eval(node.args[1])
            if not isinstance(dict_val, dict):
                raise PuffingRuntimeError("has_key() requires a dictionary")
            return key in dict_val
        
        if func_name == "set":
            if len(node.args) != 3:
                raise PuffingRuntimeError("set() takes exactly 3 arguments (dict, key, value)")
            
            dict_arg = node.args[0]
            if isinstance(dict_arg, VarAccessNode):
                var_name = dict_arg.name
                if var_name not in self.variables:
                    raise VariableNotDefinedError(f"Variable '{var_name}' not defined")
                if var_name in self.constants:
                    raise PuffingRuntimeError(f"Cannot modify constant '{var_name}'")
                dict_val = self.variables[var_name]
            else:
                dict_val = self.eval(dict_arg)
            
            key = self.eval(node.args[1])
            value = self.eval(node.args[2])
            
            if not isinstance(dict_val, dict):
                raise PuffingRuntimeError("set() requires a dictionary")
            if not isinstance(key, (str, int, float, bool)):
                raise PuffingRuntimeError(
                    f"Dictionary keys must be strings, numbers, or bools, got {type(key).__name__}"
                )
            
            dict_val[key] = value
            return dict_val
        
        if func_name == "get":
            if len(node.args) < 2 or len(node.args) > 3:
                raise PuffingRuntimeError("get() takes 2 or 3 arguments (dict, key, [default])")
            
            dict_val = self.eval(node.args[0])
            key = self.eval(node.args[1])
            default = self.eval(node.args[2]) if len(node.args) == 3 else None
            
            if not isinstance(dict_val, dict):
                raise PuffingRuntimeError("get() requires a dictionary")
            
            return dict_val.get(key, default)
        
        if func_name == "delete_key":
            if len(node.args) != 2:
                raise PuffingRuntimeError("delete_key() takes exactly 2 arguments (dict, key)")
            
            dict_arg = node.args[0]
            if isinstance(dict_arg, VarAccessNode):
                var_name = dict_arg.name
                if var_name not in self.variables:
                    raise VariableNotDefinedError(f"Variable '{var_name}' not defined")
                if var_name in self.constants:
                    raise PuffingRuntimeError(f"Cannot modify constant '{var_name}'")
                dict_val = self.variables[var_name]
            else:
                dict_val = self.eval(dict_arg)
            
            key = self.eval(node.args[1])
            if not isinstance(dict_val, dict):
                raise PuffingRuntimeError("delete_key() requires a dictionary")
            if key in dict_val:
                del dict_val[key]
            return dict_val
        
        if func_name == "clear_dict":
            if len(node.args) != 1:
                raise PuffingRuntimeError("clear_dict() takes exactly 1 argument")
            
            dict_arg = node.args[0]
            if isinstance(dict_arg, VarAccessNode):
                var_name = dict_arg.name
                if var_name not in self.variables:
                    raise VariableNotDefinedError(f"Variable '{var_name}' not defined")
                if var_name in self.constants:
                    raise PuffingRuntimeError(f"Cannot modify constant '{var_name}'")
                dict_val = self.variables[var_name]
            else:
                dict_val = self.eval(dict_arg)
            
            if not isinstance(dict_val, dict):
                raise PuffingRuntimeError("clear_dict() requires a dictionary")
            dict_val.clear()
            return dict_val
        
        if func_name == "update":
            if len(node.args) != 2:
                raise PuffingRuntimeError("update() takes exactly 2 arguments (dict, other_dict)")
            
            dict_arg = node.args[0]
            if isinstance(dict_arg, VarAccessNode):
                var_name = dict_arg.name
                if var_name not in self.variables:
                    raise VariableNotDefinedError(f"Variable '{var_name}' not defined")
                if var_name in self.constants:
                    raise PuffingRuntimeError(f"Cannot modify constant '{var_name}'")
                dict_val = self.variables[var_name]
            else:
                dict_val = self.eval(dict_arg)
            
            other_dict = self.eval(node.args[1])
            
            if not isinstance(dict_val, dict):
                raise PuffingRuntimeError("update() requires a dictionary")
            if not isinstance(other_dict, dict):
                raise PuffingRuntimeError("update() second argument must be a dictionary")
            
            dict_val.update(other_dict)
            return dict_val
        
        if func_name == "copy_dict":
            if len(node.args) != 1:
                raise PuffingRuntimeError("copy_dict() takes exactly 1 argument")
            
            dict_val = self.eval(node.args[0])
            if not isinstance(dict_val, dict):
                raise PuffingRuntimeError("copy_dict() requires a dictionary")
            
            return dict_val.copy()
        
        if func_name == "merge":
            if len(node.args) < 2:
                raise PuffingRuntimeError("merge() takes at least 2 arguments")
            
            result = {}
            for arg in node.args:
                dict_val = self.eval(arg)
                if not isinstance(dict_val, dict):
                    raise PuffingRuntimeError("merge() requires all arguments to be dictionaries")
                result.update(dict_val)
            
            return result
        
        # ==================== ARRAY METHODS ====================
        
        if func_name == "push":
            if len(node.args) != 2:
                raise PuffingRuntimeError("push() takes exactly 2 arguments (array, value)")
            
            array_arg = node.args[0]
            if isinstance(array_arg, VarAccessNode):
                var_name = array_arg.name
                if var_name not in self.variables:
                    raise VariableNotDefinedError(f"Variable '{var_name}' not defined")
                if var_name in self.constants:
                    raise PuffingRuntimeError(f"Cannot modify constant '{var_name}'")
                array = self.variables[var_name]
            else:
                array = self.eval(array_arg)
            
            value = self.eval(node.args[1])
            if not isinstance(array, list):
                raise PuffingRuntimeError("push() requires an array")
            array.append(value)
            return array
        
        if func_name == "pop":
            if len(node.args) != 1:
                raise PuffingRuntimeError("pop() takes exactly 1 argument")
            
            array_arg = node.args[0]
            if isinstance(array_arg, VarAccessNode):
                var_name = array_arg.name
                if var_name not in self.variables:
                    raise VariableNotDefinedError(f"Variable '{var_name}' not defined")
                if var_name in self.constants:
                    raise PuffingRuntimeError(f"Cannot modify constant '{var_name}'")
                array = self.variables[var_name]
            else:
                array = self.eval(array_arg)
            
            if not isinstance(array, list):
                raise PuffingRuntimeError("pop() requires an array")
            if len(array) == 0:
                raise PuffingRuntimeError("pop() from empty array")
            array.pop()
            return array
        
        if func_name == "shift":
            if len(node.args) != 1:
                raise PuffingRuntimeError("shift() takes exactly 1 argument")
            
            array_arg = node.args[0]
            if isinstance(array_arg, VarAccessNode):
                var_name = array_arg.name
                if var_name not in self.variables:
                    raise VariableNotDefinedError(f"Variable '{var_name}' not defined")
                if var_name in self.constants:
                    raise PuffingRuntimeError(f"Cannot modify constant '{var_name}'")
                array = self.variables[var_name]
            else:
                array = self.eval(array_arg)
            
            if not isinstance(array, list):
                raise PuffingRuntimeError("shift() requires an array")
            if len(array) == 0:
                raise PuffingRuntimeError("shift() from empty array")
            array.pop(0)
            return array
        
        # Remaining array functions
        if func_name in ["unshift", "insert", "remove", "clear", "reverse", "sort", 
                         "contains", "index_of", "slice", "join", "sum", "min", "max"]:
            return self._handle_array_functions(func_name, node.args)
        
        # ==================== LIBRARY FUNCTIONS ====================
        
        # Check if function exists in variables (from library imports)
        if func_name not in self.variables:
            raise PuffingRuntimeError(f"Function '{func_name}' not defined")
        
        func = self.variables[func_name]
        
        # Check if it's callable
        if not callable(func):
            raise PuffingRuntimeError(f"'{func_name}' is not a function")
        
        # Evaluate arguments
        args = [self.eval(arg) for arg in node.args]
        
        # Call function
        try:
            return func(*args)
        except Exception as e:
            raise PuffingRuntimeError(f"Error calling function '{func_name}': {e}")
        
    def _handle_array_functions(self, func_name, args):
    
        if func_name == "unshift":
            if len(args) != 2:
                raise PuffingRuntimeError("unshift() takes exactly 2 arguments (array, value)")
        
            array_arg = args[0]
            if isinstance(array_arg, VarAccessNode):
                var_name = array_arg.name
                if var_name not in self.variables:
                    raise VariableNotDefinedError(f"Variable '{var_name}' not defined")
                if var_name in self.constants:
                    raise PuffingRuntimeError(f"Cannot modify constant '{var_name}'")
                array = self.variables[var_name]
            else:
                array = self.eval(array_arg)
        
            value = self.eval(args[1])
            if not isinstance(array, list):
                raise PuffingRuntimeError("unshift() requires an array")
            array.insert(0, value)
            return array
    
        elif func_name == "insert":
            if len(args) != 3:
                raise PuffingRuntimeError("insert() takes exactly 3 arguments (array, index, value)")
        
            array_arg = args[0]
            if isinstance(array_arg, VarAccessNode):
                var_name = array_arg.name
                if var_name not in self.variables:
                    raise VariableNotDefinedError(f"Variable '{var_name}' not defined")
                if var_name in self.constants:
                    raise PuffingRuntimeError(f"Cannot modify constant '{var_name}'")
                array = self.variables[var_name]
            else:
                array = self.eval(array_arg)
        
            index = self.eval(args[1])
            value = self.eval(args[2])
            if not isinstance(array, list):
                raise PuffingRuntimeError("insert() requires an array")
            if not isinstance(index, int):
                raise PuffingRuntimeError("insert() index must be an integer")
        
            if index < 0:
                array.insert(index, value)
            else:
                zero_based_index = index - 1
                if zero_based_index < 0:
                    raise PuffingRuntimeError(f"Index {index} is invalid (indices start at 1)")
                array.insert(zero_based_index, value)
            return array
    
        elif func_name == "remove":
            if len(args) != 2:
                raise PuffingRuntimeError("remove() takes exactly 2 arguments (array, index)")
        
            array_arg = args[0]
            if isinstance(array_arg, VarAccessNode):
                var_name = array_arg.name
                if var_name not in self.variables:
                    raise VariableNotDefinedError(f"Variable '{var_name}' not defined")
                if var_name in self.constants:
                    raise PuffingRuntimeError(f"Cannot modify constant '{var_name}'")
                array = self.variables[var_name]
            else:
                array = self.eval(array_arg)
        
            index = self.eval(args[1])
            if not isinstance(array, list):
                raise PuffingRuntimeError("remove() requires an array")
            if not isinstance(index, int):
                raise PuffingRuntimeError("remove() index must be an integer")
        
            if index < 0:
                try:
                    array.pop(index)
                except IndexError:
                    raise PuffingRuntimeError(f"Index {index} out of range")
            else:
                zero_based_index = index - 1
                if zero_based_index < 0 or zero_based_index >= len(array):
                    raise PuffingRuntimeError(f"Index {index} out of range")
                array.pop(zero_based_index)
            return array
    
        elif func_name == "clear":
            if len(args) != 1:
                raise PuffingRuntimeError("clear() takes exactly 1 argument")
        
            array_arg = args[0]
            if isinstance(array_arg, VarAccessNode):
                var_name = array_arg.name
                if var_name not in self.variables:
                    raise VariableNotDefinedError(f"Variable '{var_name}' not defined")
                if var_name in self.constants:
                    raise PuffingRuntimeError(f"Cannot modify constant '{var_name}'")
                array = self.variables[var_name]
            else:
                array = self.eval(array_arg)
        
            if not isinstance(array, list):
                raise PuffingRuntimeError("clear() requires an array")
            array.clear()
            return array
    
        elif func_name == "reverse":
            if len(args) != 1:
                raise PuffingRuntimeError("reverse() takes exactly 1 argument")
        
            array_arg = args[0]
            if isinstance(array_arg, VarAccessNode):
                var_name = array_arg.name
                if var_name not in self.variables:
                    raise VariableNotDefinedError(f"Variable '{var_name}' not defined")
                if var_name in self.constants:
                    raise PuffingRuntimeError(f"Cannot modify constant '{var_name}'")
                array = self.variables[var_name]
            else:
                array = self.eval(array_arg)
        
            if not isinstance(array, list):
                raise PuffingRuntimeError("reverse() requires an array")
            array.reverse()
            return array
    
        elif func_name == "sort":
            if len(args) != 1:
                raise PuffingRuntimeError("sort() takes exactly 1 argument")
        
            array_arg = args[0]
            if isinstance(array_arg, VarAccessNode):
                var_name = array_arg.name
                if var_name not in self.variables:
                    raise VariableNotDefinedError(f"Variable '{var_name}' not defined")
                if var_name in self.constants:
                    raise PuffingRuntimeError(f"Cannot modify constant '{var_name}'")
                array = self.variables[var_name]
            else:
                array = self.eval(array_arg)
        
            if not isinstance(array, list):
                raise PuffingRuntimeError("sort() requires an array")
            try:
                array.sort()
            except TypeError as e:
                raise PuffingRuntimeError(f"Cannot sort array: {e}")
            return array
    
        elif func_name == "contains":
            if len(args) != 2:
                raise PuffingRuntimeError("contains() takes exactly 2 arguments (array, value)")
            array = self.eval(args[0])
            value = self.eval(args[1])
            if not isinstance(array, list):
                raise PuffingRuntimeError("contains() requires an array")
            return value in array
    
        elif func_name == "index_of":
            if len(args) != 2:
                raise PuffingRuntimeError("index_of() takes exactly 2 arguments (array, value)")
            array = self.eval(args[0])
            value = self.eval(args[1])
            if not isinstance(array, list):
                raise PuffingRuntimeError("index_of() requires an array")
            try:
                return array.index(value) + 1
            except ValueError:
                return -1
    
        elif func_name == "slice":
            if len(args) < 2 or len(args) > 3:
                raise PuffingRuntimeError("slice() takes 2 or 3 arguments (array, start, [end])")
            array = self.eval(args[0])
            start = self.eval(args[1])
            end = self.eval(args[2]) if len(args) == 3 else len(array) + 1
            if not isinstance(array, list):
                raise PuffingRuntimeError("slice() requires an array")
            if not isinstance(start, int) or not isinstance(end, int):
                raise PuffingRuntimeError("slice() indices must be integers")
            zero_start = start - 1
            zero_end = end - 1
            if zero_start < 0:
                zero_start = 0
            return array[zero_start:zero_end + 1]
    
        elif func_name == "join":
            if len(args) != 2:
                raise PuffingRuntimeError("join() takes exactly 2 arguments (array, separator)")
            array = self.eval(args[0])
            separator = self.eval(args[1])
            if not isinstance(array, list):
                raise PuffingRuntimeError("join() requires an array")
            if not isinstance(separator, str):
                raise PuffingRuntimeError("join() separator must be a string")
            return separator.join(str(item) for item in array)
    
        elif func_name == "sum":
            if len(args) != 1:
                raise PuffingRuntimeError("sum() takes exactly 1 argument")
            array = self.eval(args[0])
            if not isinstance(array, list):
                raise PuffingRuntimeError("sum() requires an array")
            try:
                return sum(array)
            except TypeError as e:
                raise PuffingRuntimeError(f"Cannot sum array: {e}")
    
        elif func_name == "min":
            if len(args) != 1:
                raise PuffingRuntimeError("min() takes exactly 1 argument")
            array = self.eval(args[0])
            if not isinstance(array, list):
                raise PuffingRuntimeError("min() requires an array")
            if len(array) == 0:
                raise PuffingRuntimeError("min() from empty array")
            try:
                return min(array)
            except TypeError as e:
                raise PuffingRuntimeError(f"Cannot find min: {e}")
    
        elif func_name == "max":
            if len(args) != 1:
                raise PuffingRuntimeError("max() takes exactly 1 argument")
            array = self.eval(args[0])
            if not isinstance(array, list):
                raise PuffingRuntimeError("max() requires an array")
            if len(array) == 0:
                raise PuffingRuntimeError("max() from empty array")
            try:
                return max(array)
            except TypeError as e:
                raise PuffingRuntimeError(f"Cannot find max: {e}")
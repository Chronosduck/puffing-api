"""
AST Node definitions for Puffing Language
Updated with Array, Index, N-dimensional Dictionary, and Set support
"""


class NumberNode:
    """Represents a numeric literal"""
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"NumberNode({self.value})"


class StringNode:
    """Represents a string literal"""
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"StringNode({self.value})"


class BoolNode:
    """Represents a boolean literal"""
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"BoolNode({self.value})"


class ArrayNode:
    """Represents an array literal: [1, 2, 3]"""
    def __init__(self, elements):
        self.elements = elements

    def __repr__(self):
        return f"ArrayNode({self.elements})"


class SetNode:
    """Represents a set literal: #{1, 2, 3}"""
    def __init__(self, elements):
        self.elements = elements

    def __repr__(self):
        return f"SetNode({self.elements})"


class DictNode:
    """Represents a dictionary literal: {key1: value1, key2: value2}"""
    def __init__(self, pairs):
        self.pairs = pairs  # List of (key_node, value_node) tuples

    def __repr__(self):
        return f"DictNode({self.pairs})"


class IndexAccessNode:
    """Represents index/key access: variable[index] or dict[key] - supports N-dimensions"""
    def __init__(self, container_node, key_node):
        self.container_node = container_node  # Can be array, dict, or another IndexAccessNode
        self.key_node = key_node

    def __repr__(self):
        return f"IndexAccessNode({self.container_node}, {self.key_node})"


class IndexAssignNode:
    """Represents index/key assignment: variable[index] as value or dict[key] as value - supports N-dimensions"""
    def __init__(self, container_node, key_node, value_node):
        self.container_node = container_node
        self.key_node = key_node
        self.value_node = value_node

    def __repr__(self):
        return f"IndexAssignNode({self.container_node}, {self.key_node}, {self.value_node})"


class VarAssignNode:
    """Represents variable assignment: let/lock x as value;"""
    def __init__(self, name, value_node, constant=False):
        self.name = name
        self.value_node = value_node
        self.constant = constant

    def __repr__(self):
        return f"VarAssignNode({self.name}, {self.value_node}, constant={self.constant})"


class VarReassignNode:
    """Represents variable reassignment: x as value;"""
    def __init__(self, name, value_node):
        self.name = name
        self.value_node = value_node

    def __repr__(self):
        return f"VarReassignNode({self.name}, {self.value_node})"


class CompoundAssignNode:
    """Represents compound assignment: +5x, -3x, *2x, /4y, etc."""
    def __init__(self, name, value_node, operator):
        self.name = name
        self.value_node = value_node
        self.operator = operator  # '+', '-', '*', '/', '%', '**'

    def __repr__(self):
        return f"CompoundAssignNode({self.name}, {self.value_node}, {self.operator})"


class IncrementNode:
    """Represents increment/decrement: i++, ++i, i--, --i"""
    def __init__(self, name, operator, prefix=False):
        self.name = name
        self.operator = operator  # '++' or '--'
        self.prefix = prefix  # True for ++i/--i, False for i++/i--

    def __repr__(self):
        return f"IncrementNode({self.name}, {self.operator}, prefix={self.prefix})"


class VarAccessNode:
    """Represents variable access: x"""
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"VarAccessNode({self.name})"


class BinaryOpNode:
    """Represents binary operation: left op right"""
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        return f"BinaryOpNode({self.left}, {self.op}, {self.right})"


class UnaryOpNode:
    """Represents unary operation: op operand"""
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand

    def __repr__(self):
        return f"UnaryOpNode({self.op}, {self.operand})"


class TypeCastNode:
    """Represents type casting: (type)variable"""
    def __init__(self, node, target_type):
        self.node = node
        self.target_type = target_type

    def __repr__(self):
        return f"TypeCastNode({self.node}, {self.target_type})"


class FormatNode:
    """Represents number formatting: variable.2f"""
    def __init__(self, node, precision):
        self.node = node
        self.precision = precision

    def __repr__(self):
        return f"FormatNode({self.node}, {self.precision})"


class PrintNode:
    """Represents print statement: print(value1, value2, ...);"""
    def __init__(self, value_nodes):
        # value_nodes can be a single node or a list of nodes
        self.value_nodes = value_nodes if isinstance(value_nodes, list) else [value_nodes]

    def __repr__(self):
        return f"PrintNode({self.value_nodes})"


class InputNode:
    """Represents input statement: input(type) or input()"""
    def __init__(self, input_type=None):
        self.input_type = input_type

    def __repr__(self):
        return f"InputNode({self.input_type})"


class IfNode:
    """Represents if-elif-else statement"""
    def __init__(self, condition_node, true_block, elif_blocks=None, false_block=None):
        self.condition_node = condition_node
        self.true_block = true_block
        self.elif_blocks = elif_blocks or []
        self.false_block = false_block

    def __repr__(self):
        return f"IfNode({self.condition_node}, {self.true_block}, elif={self.elif_blocks}, {self.false_block})"


class ForLoopNode:
    """Represents Python-style for loop: for var in range(start, stop, step) { ... }"""
    def __init__(self, var_name, iterable_node, body):
        self.var_name = var_name
        self.iterable_node = iterable_node
        self.body = body

    def __repr__(self):
        return f"ForLoopNode({self.var_name}, {self.iterable_node}, {self.body})"


class RangeNode:
    """Represents range function: range(start, stop, step)"""
    def __init__(self, start_node, stop_node=None, step_node=None):
        self.start_node = start_node
        self.stop_node = stop_node
        self.step_node = step_node

    def __repr__(self):
        return f"RangeNode({self.start_node}, {self.stop_node}, {self.step_node})"


class WhileLoopNode:
    """Represents while loop: while(condition) { ... }"""
    def __init__(self, condition_node, body):
        self.condition_node = condition_node
        self.body = body

    def __repr__(self):
        return f"WhileLoopNode({self.condition_node}, {self.body})"


class DoWhileLoopNode:
    """Represents do-while loop: do { ... } while(condition);"""
    def __init__(self, body, condition_node):
        self.body = body
        self.condition_node = condition_node

    def __repr__(self):
        return f"DoWhileLoopNode({self.body}, {self.condition_node})"


class BreakNode:
    """Represents break statement"""
    def __repr__(self):
        return "BreakNode()"


class ContinueNode:
    """Represents continue statement"""
    def __repr__(self):
        return "ContinueNode()"


class BlockNode:
    """Represents a block of statements"""
    def __init__(self, statements):
        self.statements = statements

    def __repr__(self):
        return f"BlockNode({self.statements})"


class LibImportNode:
    """Represents library import: lib $math.main;"""
    def __init__(self, module_path):
        self.module_path = module_path

    def __repr__(self):
        return f"LibImportNode({self.module_path})"
    

class FunctionCallNode:
    """Represents function call: func(arg1, arg2, ...)"""
    def __init__(self, name, args):
        self.name = name
        self.args = args

    def __repr__(self):
        return f"FunctionCallNode({self.name}, {self.args})"
    

class FunctionDefNode:
    """Represents function definition: fun name(params) { body }"""
    def __init__(self, name, params, body):
        self.name = name
        self.params = params  # List of parameter names
        self.body = body      # BlockNode

    def __repr__(self):
        return f"FunctionDefNode({self.name}, {self.params}, {self.body})"


class LambdaNode:
    """Represents lambda function: lamb (params) => expression or { body }"""
    def __init__(self, params, body, is_expression=True):
        self.params = params           # List of parameter names
        self.body = body               # Expression or BlockNode
        self.is_expression = is_expression  # True if single expression, False if block

    def __repr__(self):
        return f"LambdaNode({self.params}, {self.body}, expr={self.is_expression})"


class ReturnNode:
    """Represents return statement: return value;"""
    def __init__(self, value_node=None):
        self.value_node = value_node

    def __repr__(self):
        return f"ReturnNode({self.value_node})"


class DestructureAssignNode:
    """Represents destructuring assignment: let [a, b, c] as array;"""
    def __init__(self, var_names, value_node, constant=False):
        self.var_names = var_names  # List of variable names
        self.value_node = value_node
        self.constant = constant

    def __repr__(self):
        return f"DestructureAssignNode({self.var_names}, {self.value_node}, constant={self.constant})"
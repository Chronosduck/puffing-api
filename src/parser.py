"""
Parser for Puffing Language
Converts tokens into an Abstract Syntax Tree (AST)
COMPLETE VERSION - Fixed != operator + all original features
"""

from src.lexer import TokenType
from src.ast_nodes import (
    NumberNode, StringNode, BoolNode, ArrayNode, DictNode, IndexAccessNode, IndexAssignNode,
    VarAssignNode, VarAccessNode, VarReassignNode, CompoundAssignNode,
    PrintNode, IfNode, BlockNode,
    BinaryOpNode, UnaryOpNode, TypeCastNode,
    InputNode, LibImportNode, FormatNode, FunctionCallNode,
    ForLoopNode, RangeNode, WhileLoopNode, DoWhileLoopNode, BreakNode, ContinueNode,
    IncrementNode, FunctionDefNode, LambdaNode, ReturnNode, DestructureAssignNode, SetNode
)
from src.errors import ParserError


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = tokens[0] if tokens else None

    def advance(self):
        """Move to next token"""
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        return self.current_token

    def peek(self, offset=1):
        """Look ahead at token without advancing"""
        peek_pos = self.pos + offset
        if peek_pos < len(self.tokens):
            return self.tokens[peek_pos]
        return None

    def expect(self, token_type):
        """Expect a specific token type and advance"""
        if self.current_token.type != token_type:
            raise ParserError(
                f"Expected token {token_type}, got {self.current_token.type} "
                f"with value {self.current_token.value}"
            )
        self.advance()

    def parse(self):
        """Parse tokens into AST"""
        statements = []

        while self.current_token.type != TokenType.EOF:
            stmt = self.statement()
            statements.append(stmt)

        return BlockNode(statements)

    def statement(self):
        """Parse a single statement"""
        # Function definition
        if self.current_token.type == TokenType.FUN:
            return self.function_def()
        
        # Return statement
        if self.current_token.type == TokenType.RETURN:
            return self.return_statement()
        
        # Library import
        if self.current_token.type == TokenType.LIB:
            return self.lib_import()

        # Variable declaration
        if self.current_token.type == TokenType.LET:
            return self.var_assign(constant=False)
        
        # Constant declaration
        if self.current_token.type == TokenType.LOCK:
            return self.var_assign(constant=True)

        # Print statement
        if self.current_token.type == TokenType.PRINT:
            return self.print_statement()

        # If statement (doesn't need semicolon - has block)
        if self.current_token.type == TokenType.IF:
            return self.if_statement()

        # For loop (doesn't need semicolon - has block)
        if self.current_token.type == TokenType.FOR:
            return self.for_loop()

        # While loop (doesn't need semicolon - has block)
        if self.current_token.type == TokenType.WHILE:
            return self.while_loop()

        # Do-while loop (needs semicolon after while condition)
        if self.current_token.type == TokenType.DO:
            return self.do_while_loop()

        # Break statement
        if self.current_token.type == TokenType.BREAK:
            self.advance()
            self.expect(TokenType.SEMICOLON)
            return BreakNode()

        # Continue statement
        if self.current_token.type == TokenType.CONTINUE:
            self.advance()
            self.expect(TokenType.SEMICOLON)
            return ContinueNode()

        # Check for prefix increment/decrement (++i, --i)
        if self.current_token.type in (TokenType.INCREMENT, TokenType.DECREMENT):
            return self.prefix_increment()

        # Check for compound assignment (+5x, -3y, etc.)
        if self.current_token.type in (TokenType.PLUS, TokenType.MINUS, TokenType.MULTIPLY, 
                                       TokenType.DIVIDE, TokenType.MODULO, TokenType.POWER):
            return self.compound_assign()
   
        # Variable reassignment or postfix increment/decrement or index assignment
        if self.current_token.type == TokenType.IDENT:
            # Look ahead to determine what this is
            next_token = self.peek(1)
            
            if next_token:
                # Check for postfix increment/decrement (i++, i--)
                if next_token.type in (TokenType.INCREMENT, TokenType.DECREMENT):
                    return self.postfix_increment()
        
                # Check for index assignment (x[i] as value or x[i][j] as value)
                # We need to look further ahead to see if there's an 'as' after ALL the brackets
                if next_token.type == TokenType.LBRACKET:
                    # Scan ahead through ALL bracket pairs to find if there's an AS
                    temp_pos = self.pos + 1
                    
                    # Keep scanning while we find brackets
                    while temp_pos < len(self.tokens) and self.tokens[temp_pos].type == TokenType.LBRACKET:
                        # Skip this bracket pair
                        temp_pos += 1
                        bracket_count = 1
                        while temp_pos < len(self.tokens) and bracket_count > 0:
                            if self.tokens[temp_pos].type == TokenType.LBRACKET:
                                bracket_count += 1
                            elif self.tokens[temp_pos].type == TokenType.RBRACKET:
                                bracket_count -= 1
                            temp_pos += 1
                    
                    # Check if there's an AS after all the closing brackets
                    if temp_pos < len(self.tokens) and self.tokens[temp_pos].type == TokenType.AS:
                        return self.index_assign()
                    # Otherwise, it's just an expression (array/string access)
        
                # Check for reassignment (x as value)
                if next_token.type == TokenType.AS:
                    return self.var_reassign()

        # Expression statement (fallback)
        expr = self.expr()
        self.expect(TokenType.SEMICOLON)
        return expr

    def function_def(self):
        """Parse function definition: fun name(params) { body }"""
        self.expect(TokenType.FUN)
        
        if self.current_token.type != TokenType.IDENT:
            raise ParserError("Expected function name after 'fun'")
        
        func_name = self.current_token.value
        self.advance()
        
        self.expect(TokenType.LPAREN)
        
        # Parse parameters
        params = []
        if self.current_token.type != TokenType.RPAREN:
            if self.current_token.type != TokenType.IDENT:
                raise ParserError("Expected parameter name")
            params.append(self.current_token.value)
            self.advance()
            
            while self.current_token.type == TokenType.COMMA:
                self.advance()
                if self.current_token.type != TokenType.IDENT:
                    raise ParserError("Expected parameter name")
                params.append(self.current_token.value)
                self.advance()
        
        self.expect(TokenType.RPAREN)
        
        # Parse body
        body = self.block()
        
        return FunctionDefNode(func_name, params, body)

    def return_statement(self):
        """Parse return statement: return value; or return;"""
        self.expect(TokenType.RETURN)
        
        # Check if there's a return value
        if self.current_token.type == TokenType.SEMICOLON:
            self.advance()
            return ReturnNode(None)
        
        value = self.expr()
        self.expect(TokenType.SEMICOLON)
        return ReturnNode(value)

    def lambda_func(self):
        """Parse lambda function: lamb (params) => expr or lamb (params) => { body }"""
        self.expect(TokenType.LAMB)
        self.expect(TokenType.LPAREN)
        
        # Parse parameters
        params = []
        if self.current_token.type != TokenType.RPAREN:
            if self.current_token.type != TokenType.IDENT:
                raise ParserError("Expected parameter name in lambda")
            params.append(self.current_token.value)
            self.advance()
            
            while self.current_token.type == TokenType.COMMA:
                self.advance()
                if self.current_token.type != TokenType.IDENT:
                    raise ParserError("Expected parameter name in lambda")
                params.append(self.current_token.value)
                self.advance()
        
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.ARROW)
        
        # Check if it's a block or expression
        if self.current_token.type == TokenType.LBRACE:
            # Block lambda: lamb (x) => { return x * 2; }
            body = self.block()
            return LambdaNode(params, body, is_expression=False)
        else:
            # Expression lambda: lamb (x) => x * 2
            body = self.expr()
            return LambdaNode(params, body, is_expression=True)

    def index_assign(self):
        """Parse N-dimensional index assignment: x[i][j]...[n] as value;"""
        # Build the full index access chain first
        index_chain = self.postfix()
        
        # Verify it's an index access chain
        if not isinstance(index_chain, IndexAccessNode):
            raise ParserError("Expected index access before 'as'")
        
        self.expect(TokenType.AS)
        value_node = self.expr()
        self.expect(TokenType.SEMICOLON)
        
        # Create IndexAssignNode with the full chain
        # The interpreter will handle the nested structure
        return IndexAssignNode(index_chain, None, value_node)

    def prefix_increment(self):
        """Parse prefix increment/decrement: ++i, --i"""
        operator = self.current_token.type
        self.advance()
        
        if self.current_token.type != TokenType.IDENT:
            raise ParserError("Expected variable name after prefix increment/decrement")
        
        var_name = self.current_token.value
        self.advance()
        self.expect(TokenType.SEMICOLON)
        
        return IncrementNode(var_name, operator, prefix=True)

    def postfix_increment(self):
        """Parse postfix increment/decrement: i++, i--"""
        if self.current_token.type != TokenType.IDENT:
            raise ParserError("Expected variable name")
        
        var_name = self.current_token.value
        self.advance()
        
        operator = self.current_token.type
        self.advance()
        self.expect(TokenType.SEMICOLON)
        
        return IncrementNode(var_name, operator, prefix=False)

    def compound_assign(self):
        """Parse compound assignment: +5x, -3y, *2x, /4x, %3x, **2x"""
        operator = self.current_token.type
        self.advance()
        
        # Parse the value (number or expression)
        value_node = self.primary()
        
        # Expect variable name
        if self.current_token.type != TokenType.IDENT:
            raise ParserError("Expected variable name in compound assignment")
        
        var_name = self.current_token.value
        self.advance()
        self.expect(TokenType.SEMICOLON)
        
        return CompoundAssignNode(var_name, value_node, operator)

    def lib_import(self):
        """Parse library import: lib $math.main;"""
        self.expect(TokenType.LIB)
        self.expect(TokenType.DOLLAR)
        
        if self.current_token.type != TokenType.IDENT:
            raise ParserError("Expected library name after '$'")
        
        lib_name = self.current_token.value
        self.advance()
        
        # Handle module path (e.g., math.main)
        module_path = [lib_name]
        while self.current_token.type == TokenType.DOT:
            self.advance()
            if self.current_token.type != TokenType.IDENT:
                raise ParserError("Expected module name after '.'")
            module_path.append(self.current_token.value)
            self.advance()
        
        self.expect(TokenType.SEMICOLON)
        return LibImportNode('.'.join(module_path))

    def var_assign(self, constant=False):
        """Parse variable assignment: let/lock x as value; OR let/lock [a, b] as value;"""
        if constant:
            self.expect(TokenType.LOCK)
        else:
            self.expect(TokenType.LET)

        # Check for destructuring pattern: [a, b, c]
        if self.current_token.type == TokenType.LBRACKET:
            self.advance()  # Skip [
            
            var_names = []
            if self.current_token.type != TokenType.RBRACKET:
                if self.current_token.type != TokenType.IDENT:
                    raise ParserError("Expected variable name in destructuring pattern")
                var_names.append(self.current_token.value)
                self.advance()
                
                while self.current_token.type == TokenType.COMMA:
                    self.advance()  # Skip comma
                    if self.current_token.type != TokenType.IDENT:
                        raise ParserError("Expected variable name in destructuring pattern")
                    var_names.append(self.current_token.value)
                    self.advance()
            
            self.expect(TokenType.RBRACKET)
            self.expect(TokenType.AS)
            
            value_node = self.expr()
            self.expect(TokenType.SEMICOLON)
            
            return DestructureAssignNode(var_names, value_node, constant)

        # Standard single variable assignment
        if self.current_token.type != TokenType.IDENT:
            raise ParserError("Expected variable name after 'let'/'lock'")

        var_name = self.current_token.value
        self.advance()

        self.expect(TokenType.AS)

        value_node = self.expr()

        self.expect(TokenType.SEMICOLON)

        return VarAssignNode(var_name, value_node, constant)

    def var_reassign(self):
        """Parse variable reassignment: x as value;"""
        if self.current_token.type != TokenType.IDENT:
            raise ParserError("Expected variable name")

        var_name = self.current_token.value
        self.advance()

        self.expect(TokenType.AS)

        value_node = self.expr()

        self.expect(TokenType.SEMICOLON)

        return VarReassignNode(var_name, value_node)

    def for_loop(self):
        """Parse Python-style for loop: for var in range(...) { ... } or for var in iterable { ... }"""
        self.expect(TokenType.FOR)
        
        if self.current_token.type != TokenType.IDENT:
            raise ParserError("Expected variable name after 'for'")
        
        var_name = self.current_token.value
        self.advance()
        
        self.expect(TokenType.IN)
        
        # Parse the iterable (typically range(...))
        iterable = self.expr()
        
        body = self.block()
        
        return ForLoopNode(var_name, iterable, body)

    def while_loop(self):
        """Parse while loop: while condition { ... }"""
        self.expect(TokenType.WHILE)
        
        condition = self.expr()
        
        body = self.block()

        return WhileLoopNode(condition, body)

    def do_while_loop(self):
        """Parse do-while loop: do { ... } while condition;"""
        self.expect(TokenType.DO)

        body = self.block()

        self.expect(TokenType.WHILE)
        
        condition = self.expr()

        self.expect(TokenType.SEMICOLON)

        return DoWhileLoopNode(body, condition)
    
    def print_statement(self):
        """Parse print statement: print(value1, value2, ...);"""
        self.expect(TokenType.PRINT)
        self.expect(TokenType.LPAREN)

        # Parse multiple values separated by commas
        values = []
        if self.current_token.type != TokenType.RPAREN:
            values.append(self.expr())
            while self.current_token.type == TokenType.COMMA:
                self.advance()  # Skip comma
                values.append(self.expr())

        self.expect(TokenType.RPAREN)
        self.expect(TokenType.SEMICOLON)
        return PrintNode(values)

    def if_statement(self):
        """Parse if statement: if condition { ... } elif condition { ... } else { ... }"""
        self.expect(TokenType.IF)
        
        condition = self.expr()
        
        true_block = self.block()

        # Handle elif chains
        elif_blocks = []
        while self.current_token.type == TokenType.ELIF:
            self.expect(TokenType.ELIF)
            elif_condition = self.expr()
            elif_block = self.block()
            elif_blocks.append((elif_condition, elif_block))

        false_block = None
        if self.current_token.type == TokenType.ELSE:
            self.expect(TokenType.ELSE)
            false_block = self.block()

        return IfNode(condition, true_block, elif_blocks, false_block)

    def block(self):
        """Parse a block of statements: { ... }"""
        self.expect(TokenType.LBRACE)

        statements = []
        while self.current_token.type != TokenType.RBRACE:
            if self.current_token.type == TokenType.EOF:
                raise ParserError("Unexpected EOF, expected '}'")
            stmt = self.statement()
            statements.append(stmt)

        self.expect(TokenType.RBRACE)

        return BlockNode(statements)

    def expr(self):
        """Parse an expression (handles or)"""
        return self.or_expr()

    def or_expr(self):
        """Parse OR expression"""
        left = self.and_expr()

        while self.current_token.type == TokenType.OR:
            op = self.current_token.type
            self.advance()
            right = self.and_expr()
            left = BinaryOpNode(left, op, right)

        return left

    def and_expr(self):
        """Parse AND expression"""
        left = self.comparison()

        while self.current_token.type == TokenType.AND:
            op = self.current_token.type
            self.advance()
            right = self.comparison()
            left = BinaryOpNode(left, op, right)

        return left

    def comparison(self):
        """Parse comparison expression - FIXED: Added NOT_EQUAL support"""
        left = self.arith_expr()

        # Handle all comparison operators including !=
        while self.current_token.type in (
            TokenType.EQUAL, TokenType.NOT_EQUAL, 
            TokenType.LESS, TokenType.GREATER,
            TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL
        ):
            op = self.current_token.type
            self.advance()
            right = self.arith_expr()
            left = BinaryOpNode(left, op, right)

        return left

    def arith_expr(self):
        """Parse arithmetic expression (addition/subtraction)"""
        left = self.term()

        while self.current_token.type in (TokenType.PLUS, TokenType.MINUS):
            op = self.current_token.type
            self.advance()
            right = self.term()
            left = BinaryOpNode(left, op, right)

        return left

    def term(self):
        """Parse term (multiplication/division/modulo)"""
        left = self.power()

        while self.current_token.type in (TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO):
            op = self.current_token.type
            self.advance()
            right = self.power()
            left = BinaryOpNode(left, op, right)

        return left

    def power(self):
        """Parse power expression"""
        left = self.unary()

        if self.current_token.type == TokenType.POWER:
            op = self.current_token.type
            self.advance()
            right = self.power()  # Right associative
            return BinaryOpNode(left, op, right)

        return left

    def unary(self):
        """Parse unary expression"""
        if self.current_token.type in (TokenType.MINUS, TokenType.NOT):
            op = self.current_token.type
            self.advance()
            operand = self.unary()
            return UnaryOpNode(op, operand)

        return self.postfix()

    def postfix(self):
        """Parse postfix operations (index access, function calls, formatting)"""
        node = self.call()

        # Handle index access: variable[index] - supports N-dimensional
        while self.current_token.type == TokenType.LBRACKET:
            self.advance()
            index_node = self.expr()
            self.expect(TokenType.RBRACKET)
            node = IndexAccessNode(node, index_node)

        return node

    def call(self):
        """Parse function calls and other postfix operations"""
        node = self.primary()

        while True:
            if self.current_token.type == TokenType.LPAREN:
                next_token = self.peek(1)
                
                if next_token:
                    # Check for type cast: (type)
                    if next_token.type in (TokenType.INT, TokenType.FLOAT, TokenType.STR, TokenType.BOOL):
                        peek_after = self.peek(2)
                        if peek_after and peek_after.type == TokenType.RPAREN:
                            # It's a type cast
                            self.advance()  # Skip (
                            target_type = self.current_token.type
                            self.advance()  # Skip type
                            self.expect(TokenType.RPAREN)
                            node = TypeCastNode(node, target_type)
                            continue
                    
                    # Function call
                    self.advance()  # Skip (
                    
                    # Parse arguments
                    args = []
                    if self.current_token.type != TokenType.RPAREN:
                        args.append(self.expr())
                        while self.current_token.type == TokenType.COMMA:
                            self.advance()  # Skip comma
                            args.append(self.expr())
                    
                    self.expect(TokenType.RPAREN)
                    
                    # Handle range function specially
                    if isinstance(node, VarAccessNode) and node.name == "range":
                        if len(args) == 1:
                            node = RangeNode(NumberNode(1), args[0], NumberNode(1))
                        elif len(args) == 2:
                            node = RangeNode(args[0], args[1], NumberNode(1))
                        elif len(args) == 3:
                            node = RangeNode(args[0], args[1], args[2])
                        else:
                            raise ParserError("range() takes 1, 2, or 3 arguments")
                    # Handle lambda node (immediately invoked lambda)
                    elif isinstance(node, LambdaNode):
                        # Create a special function call node that holds the lambda directly
                        node = FunctionCallNode(node, args)
                    else:
                        node = FunctionCallNode(node.name if isinstance(node, VarAccessNode) else str(node), args)
                    continue
                else:
                    break

            # Format specifier: variable.2f
            elif self.current_token.type == TokenType.DOT:
                next_token = self.peek(1)
                if next_token and next_token.type == TokenType.NUMBER:
                    self.advance()
                    precision = int(self.current_token.value)
                    self.advance()
                    if self.current_token.type == TokenType.IDENT and self.current_token.value == "f":
                        self.advance()
                        node = FormatNode(node, precision)
                        continue
                    else:
                        raise ParserError("Expected 'f' after decimal precision")
                break
            else:
                break

        return node

    def primary(self):
        """Parse primary expression - WITH PREFIX TYPE CAST SUPPORT"""
        token = self.current_token

        # Lambda function
        if token.type == TokenType.LAMB:
            return self.lambda_func()

        # Parenthesized expression OR PREFIX TYPE CAST
        if token.type == TokenType.LPAREN:
            # Look ahead to check if it's a type cast: (int), (float), (str), (bool)
            next_token = self.peek(1)
            if next_token and next_token.type in (TokenType.INT, TokenType.FLOAT, TokenType.STR, TokenType.BOOL):
                peek_after = self.peek(2)
                if peek_after and peek_after.type == TokenType.RPAREN:
                    # It's a prefix type cast: (int)expression
                    self.advance()  # Skip (
                    target_type = self.current_token.type
                    self.advance()  # Skip type
                    self.expect(TokenType.RPAREN)
                    
                    # Parse the expression to be casted
                    expr = self.unary()  # Parse next expression
                    return TypeCastNode(expr, target_type)
            
            # Otherwise it's a regular parenthesized expression
            self.advance()
            expr = self.expr()
            self.expect(TokenType.RPAREN)
            return expr

        # Number literal
        if token.type == TokenType.NUMBER:
            self.advance()
            return NumberNode(token.value)

        # String literal
        if token.type == TokenType.STRING:
            self.advance()
            return StringNode(token.value)

        # Boolean literals
        if token.type == TokenType.TRUE:
            self.advance()
            return BoolNode(True)

        if token.type == TokenType.FALSE:
            self.advance()
            return BoolNode(False)

        # Array literal: [1, 2, 3]
        if token.type == TokenType.LBRACKET:
            return self.array_literal()

        # Dictionary literal or block
        if token.type == TokenType.LBRACE:
            next_token = self.peek(1)
            
            if next_token:
                if next_token.type == TokenType.RBRACE:
                    return self.dict_literal()
                
                temp_pos = self.pos + 1
                found_colon = False
                paren_depth = 0
                bracket_depth = 0
                brace_depth = 0
                
                while temp_pos < len(self.tokens) and temp_pos < self.pos + 15:
                    t = self.tokens[temp_pos]
                    
                    if t.type == TokenType.LPAREN:
                        paren_depth += 1
                    elif t.type == TokenType.RPAREN:
                        paren_depth -= 1
                    elif t.type == TokenType.LBRACKET:
                        bracket_depth += 1
                    elif t.type == TokenType.RBRACKET:
                        bracket_depth -= 1
                    elif t.type == TokenType.LBRACE:
                        brace_depth += 1
                    elif t.type == TokenType.RBRACE:
                        if brace_depth > 0:
                            brace_depth -= 1
                        else:
                            break
                    elif t.type == TokenType.COLON and paren_depth == 0 and bracket_depth == 0 and brace_depth == 0:
                        found_colon = True
                        break
                    elif t.type == TokenType.SEMICOLON:
                        break
                    
                    temp_pos += 1
                
                if found_colon:
                    return self.dict_literal()
            
            raise ParserError(f"Unexpected '{{' in expression context")
        
        # Set literal: #{1, 2, 3}
        if token.type == TokenType.HASH:
            return self.set_literal()
    
        # Input statement
        if token.type == TokenType.INPUT:
            return self.input_statement()

        # Variable access
        if token.type == TokenType.IDENT:
            name = token.value
            self.advance()
            return VarAccessNode(name)

        raise ParserError(f"Unexpected token in expression: {token}")

    def array_literal(self):
        """Parse array literal: [1, 2, 3, ...]"""
        self.expect(TokenType.LBRACKET)
        
        elements = []
        if self.current_token.type != TokenType.RBRACKET:
            elements.append(self.expr())
            while self.current_token.type == TokenType.COMMA:
                self.advance()  # Skip comma
                
                # Allow trailing comma
                if self.current_token.type == TokenType.RBRACKET:
                    break
                
                elements.append(self.expr())
        
        self.expect(TokenType.RBRACKET)
        return ArrayNode(elements)

    def set_literal(self):
        """Parse set literal: #{1, 2, 3, ...}"""
        self.expect(TokenType.HASH)
        self.expect(TokenType.LBRACE)
        
        elements = []
        if self.current_token.type != TokenType.RBRACE:
            elements.append(self.expr())
            while self.current_token.type == TokenType.COMMA:
                self.advance()  # Skip comma
                
                # Allow trailing comma
                if self.current_token.type == TokenType.RBRACE:
                    break
                
                elements.append(self.expr())
        
        self.expect(TokenType.RBRACE)
        return SetNode(elements)
        
    def dict_literal(self):
        """Parse dictionary literal: {key1: value1, key2: value2, ...}"""
        self.expect(TokenType.LBRACE)
        
        pairs = []
        if self.current_token.type != TokenType.RBRACE:
            # Parse first key-value pair
            key_node = self.expr()
            self.expect(TokenType.COLON)
            value_node = self.expr()
            pairs.append((key_node, value_node))
            
            # Parse remaining pairs
            while self.current_token.type == TokenType.COMMA:
                self.advance()  # Skip comma
                
                # Allow trailing comma
                if self.current_token.type == TokenType.RBRACE:
                    break
                
                key_node = self.expr()
                self.expect(TokenType.COLON)
                value_node = self.expr()
                pairs.append((key_node, value_node))
        
        self.expect(TokenType.RBRACE)
        return DictNode(pairs)

    def input_statement(self):
        """Parse input statement: input(type) or input()"""
        self.expect(TokenType.INPUT)
        self.expect(TokenType.LPAREN)

        input_type = None
        if self.current_token.type in (TokenType.INT, TokenType.FLOAT, TokenType.STR, TokenType.BOOL):
            input_type = self.current_token.type
            self.advance()

        self.expect(TokenType.RPAREN)

        return InputNode(input_type)
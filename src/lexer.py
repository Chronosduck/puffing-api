"""
Lexer for Puffing Language
Converts source code into tokens

UPDATED: Added set literal support with # symbol
"""

from enum import Enum
from src.errors import LexerError


class TokenType(Enum):
    # Keywords
    LET = "LET"
    LOCK = "LOCK"
    AS = "AS"
    IF = "IF"
    ELIF = "ELIF"
    ELSE = "ELSE"
    PRINT = "PRINT"
    INPUT = "INPUT"
    LIB = "LIB"
    FOR = "FOR"
    IN = "IN"
    WHILE = "WHILE"
    DO = "DO"
    BREAK = "BREAK"
    CONTINUE = "CONTINUE"
    
    # Types
    INT = "INT"
    FLOAT = "FLOAT"
    STR = "STR"
    BOOL = "BOOL"

    # Identifiers / literals
    IDENT = "IDENT"
    NUMBER = "NUMBER"
    STRING = "STRING"
    TRUE = "TRUE"
    FALSE = "FALSE"

    # Operators
    PLUS = "+"
    MINUS = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    MODULO = "%"
    POWER = "**"
    INCREMENT = "++"
    DECREMENT = "--"
    
    # Comparison operators
    EQUAL = "="
    NOT_EQUAL = "!="
    LESS = "<"
    GREATER = ">"
    LESS_EQUAL = "<="
    GREATER_EQUAL = ">="
    NOT = "!"
    AND = "AND"
    OR = "OR"

    # Symbols
    SEMICOLON = ";"
    LPAREN = "("
    RPAREN = ")"
    LBRACE = "{"
    RBRACE = "}"
    LBRACKET = "["
    RBRACKET = "]"
    DOT = "."
    DOLLAR = "$"
    COMMA = ","
    COLON = ":"
    HASH = "#"  # For set literals
    FUN = "FUN"
    LAMB = "LAMB"
    RETURN = "RETURN"
    ARROW = "=>"
    EOF = "EOF"


class Token:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, {self.value})"


class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.current_char = text[0] if text else None
        self.line = 1
        self.column = 1

    def advance(self):
        """Move to next character"""
        if self.current_char == '\n':
            self.line += 1
            self.column = 0
        
        self.pos += 1
        self.column += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def skip_whitespace(self):
        """Skip whitespace characters"""
        while self.current_char and self.current_char.isspace():
            self.advance()

    def skip_single_line_comment(self):
        """Skip single-line comment - from ? to end of line"""
        # Skip the ?
        self.advance()
        # Skip until newline or EOF
        while self.current_char and self.current_char != '\n':
            self.advance()
        # Skip the newline if present
        if self.current_char == '\n':
            self.advance()

    def skip_block_comment(self):
        """Skip block comment ?- ... -?"""
        # Skip ?-
        self.advance()  # Skip ?
        self.advance()  # Skip -
        
        # Look for -?
        while self.current_char:
            if self.current_char == '-' and self.peek() == '?':
                self.advance()  # Skip -
                self.advance()  # Skip ?
                break
            self.advance()

    def peek(self):
        """Look at next character without advancing"""
        peek_pos = self.pos + 1
        return self.text[peek_pos] if peek_pos < len(self.text) else None

    def number(self):
        """Parse number token"""
        result = ""
        while self.current_char and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        
        # Support decimal numbers
        if self.current_char == '.' and self.peek() and self.peek().isdigit():
            result += self.current_char
            self.advance()
            while self.current_char and self.current_char.isdigit():
                result += self.current_char
                self.advance()
            return Token(TokenType.NUMBER, float(result))
        
        return Token(TokenType.NUMBER, int(result))

    def string(self):
        """Parse string token"""
        self.advance()  # Skip opening quote
        result = ""
        
        while self.current_char and self.current_char != '"':
            if self.current_char == '\\':
                self.advance()
                # Handle escape sequences
                if self.current_char == 'n':
                    result += '\n'
                elif self.current_char == 't':
                    result += '\t'
                elif self.current_char == '"':
                    result += '"'
                elif self.current_char == '\\':
                    result += '\\'
                else:
                    result += self.current_char
                self.advance()
            else:
                result += self.current_char
                self.advance()
        
        if not self.current_char:
            raise LexerError(f"Unterminated string at line {self.line}, column {self.column}")
        
        self.advance()
        return Token(TokenType.STRING, result)

    def identifier(self):
        """Parse identifier or keyword"""
        result = ""
        while self.current_char and (self.current_char.isalnum() or self.current_char == "_"):
            result += self.current_char
            self.advance()

        keywords = {
            "let": TokenType.LET,
            "lock": TokenType.LOCK,
            "as": TokenType.AS,
            "if": TokenType.IF,
            "elif": TokenType.ELIF,
            "else": TokenType.ELSE,
            "print": TokenType.PRINT,
            "input": TokenType.INPUT,
            "lib": TokenType.LIB,
            "for": TokenType.FOR,
            "in": TokenType.IN,
            "while": TokenType.WHILE,
            "do": TokenType.DO,
            "break": TokenType.BREAK,
            "continue": TokenType.CONTINUE,
            "int": TokenType.INT,
            "float": TokenType.FLOAT,
            "str": TokenType.STR,
            "bool": TokenType.BOOL,
            "true": TokenType.TRUE,
            "false": TokenType.FALSE,
            "and": TokenType.AND,
            "or": TokenType.OR,
            "fun": TokenType.FUN,
            "lamb": TokenType.LAMB,
            "return": TokenType.RETURN,
        }

        if result in keywords:
            return Token(keywords[result])
        return Token(TokenType.IDENT, result)

    def tokenize(self):
        """Tokenize the entire source code"""
        tokens = []

        while self.current_char:
            # Skip whitespace
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            # Handle comments (both single-line and block)
            if self.current_char == '?':
                # Check for block comment ?-
                if self.peek() == '-':
                    self.skip_block_comment()
                else:
                    # Single-line comment
                    self.skip_single_line_comment()
                continue

            # Numbers
            if self.current_char.isdigit():
                tokens.append(self.number())
                continue

            # Strings
            if self.current_char == '"':
                tokens.append(self.string())
                continue

            # Identifiers and keywords
            if self.current_char.isalpha() or self.current_char == "_":
                tokens.append(self.identifier())
                continue

            # Operators and symbols
            char = self.current_char

            # Two-character operators
            if char == '*' and self.peek() == '*':
                tokens.append(Token(TokenType.POWER))
                self.advance()
                self.advance()
                continue
            
            if char == '+' and self.peek() == '+':
                tokens.append(Token(TokenType.INCREMENT))
                self.advance()
                self.advance()
                continue
            
            if char == '-' and self.peek() == '-':
                tokens.append(Token(TokenType.DECREMENT))
                self.advance()
                self.advance()
                continue
            
            if char == '<' and self.peek() == '=':
                tokens.append(Token(TokenType.LESS_EQUAL))
                self.advance()
                self.advance()
                continue
            
            if char == '>' and self.peek() == '=':
                tokens.append(Token(TokenType.GREATER_EQUAL))
                self.advance()
                self.advance()
                continue
            
            if char == '!' and self.peek() == '=':
                tokens.append(Token(TokenType.NOT_EQUAL))
                self.advance()
                self.advance()
                continue
            
            if char == '=' and self.peek() == '>':
                tokens.append(Token(TokenType.ARROW))
                self.advance()
                self.advance()
                continue
            
            # Single-character operators
            if char == "+":
                tokens.append(Token(TokenType.PLUS))
            elif char == "-":
                tokens.append(Token(TokenType.MINUS))
            elif char == "*":
                tokens.append(Token(TokenType.MULTIPLY))
            elif char == "/":
                tokens.append(Token(TokenType.DIVIDE))
            elif char == "%":
                tokens.append(Token(TokenType.MODULO))
            elif char == "=":
                tokens.append(Token(TokenType.EQUAL))
            elif char == "<":
                tokens.append(Token(TokenType.LESS))
            elif char == ">":
                tokens.append(Token(TokenType.GREATER))
            elif char == "!":
                tokens.append(Token(TokenType.NOT))
            elif char == ";":
                tokens.append(Token(TokenType.SEMICOLON))
            elif char == "(":
                tokens.append(Token(TokenType.LPAREN))
            elif char == ")":
                tokens.append(Token(TokenType.RPAREN))
            elif char == "{":
                tokens.append(Token(TokenType.LBRACE))
            elif char == "}":
                tokens.append(Token(TokenType.RBRACE))
            elif char == "[":
                tokens.append(Token(TokenType.LBRACKET))
            elif char == "]":
                tokens.append(Token(TokenType.RBRACKET))
            elif char == ".":
                tokens.append(Token(TokenType.DOT))
            elif char == "$":
                tokens.append(Token(TokenType.DOLLAR))
            elif char == ",":
                tokens.append(Token(TokenType.COMMA))
            elif char == ":":
                tokens.append(Token(TokenType.COLON))
            elif char == "#":
                tokens.append(Token(TokenType.HASH))
            else:
                raise LexerError(f"Unknown character '{char}' at line {self.line}, column {self.column}")

            self.advance()

        tokens.append(Token(TokenType.EOF))
        return tokens
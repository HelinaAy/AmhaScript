#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AmhaScript Translator — v1.0
Translates AmhaScript (Amharic-keyword language) to Python.

Usage:
    python translator.py program.as

Outputs:
    program.py  (translated Python file)

Author: CSEg 4306 Group Project — Adama Science and Technology University
"""

import sys
import os
import re

# ═══════════════════════════════════════════════════════════════
#  TOKEN TYPES
# ═══════════════════════════════════════════════════════════════
TT_VAR_DECL  = 'VAR_DECL'   # ቁጥር
TT_ASSIGN    = 'ASSIGN'     # ሰጥ
TT_IF        = 'IF'         # ከሆነ
TT_ELSE      = 'ELSE'       # ካልሆነ
TT_WHILE     = 'WHILE'      # እስኪሆን
TT_DEF       = 'DEF'        # ስራ
TT_RETURN    = 'RETURN'     # መልስ
TT_PRINT     = 'PRINT'      # ጥራ
TT_AND       = 'AND'        # እና
TT_OR        = 'OR'         # ወይም
TT_NOT       = 'NOT'        # አይደለም
TT_TRUE      = 'TRUE'       # እውነት
TT_FALSE     = 'FALSE'      # ሀሰት
TT_PASS      = 'PASS'       # ጨርስ

TT_IDENT     = 'IDENT'
TT_NUMBER    = 'NUMBER'
TT_STRING    = 'STRING'
TT_PLUS      = 'PLUS'
TT_MINUS     = 'MINUS'
TT_MUL       = 'MUL'
TT_DIV       = 'DIV'
TT_EQ        = 'EQ'
TT_NEQ       = 'NEQ'
TT_LT        = 'LT'
TT_GT        = 'GT'
TT_LTE       = 'LTE'
TT_GTE       = 'GTE'
TT_ASSIGN_OP = 'ASSIGN_OP'  # plain = inside expressions (not ሰጥ)
TT_LPAREN    = 'LPAREN'
TT_RPAREN    = 'RPAREN'
TT_COMMA     = 'COMMA'
TT_COLON     = 'COLON'
TT_NEWLINE   = 'NEWLINE'
TT_INDENT    = 'INDENT'
TT_DEDENT    = 'DEDENT'
TT_EOF       = 'EOF'

# ═══════════════════════════════════════════════════════════════
#  KEYWORD MAP (Amharic → token type)
# ═══════════════════════════════════════════════════════════════
KEYWORDS = {
    'ቁጥር':    TT_VAR_DECL,
    'ሰጥ':     TT_ASSIGN,
    'አስቀምጥ':  TT_ASSIGN,     # synonym
    'ከሆነ':    TT_IF,
    'ካልሆነ':  TT_ELSE,
    'እስኪሆን':  TT_WHILE,
    'ስራ':     TT_DEF,
    'መልስ':   TT_RETURN,
    'ጥራ':     TT_PRINT,
    'እና':     TT_AND,
    'ወይም':    TT_OR,
    'አይደለም':  TT_NOT,
    'እውነት':  TT_TRUE,
    'ሀሰት':    TT_FALSE,
    'ጨርስ':    TT_PASS,
}

# ═══════════════════════════════════════════════════════════════
#  TOKEN
# ═══════════════════════════════════════════════════════════════
class Token:
    def __init__(self, type_, value, line=0):
        self.type  = type_
        self.value = value
        self.line  = line

    def __repr__(self):
        return f'Token({self.type}, {self.value!r}, line={self.line})'


# ═══════════════════════════════════════════════════════════════
#  LEXER
# ═══════════════════════════════════════════════════════════════
class Lexer:
    """
    Tokenises AmhaScript source code.
    Handles Unicode (Ethiopic + ASCII) correctly.
    Produces INDENT / DEDENT tokens from indentation changes.
    """

    def __init__(self, source: str):
        self.source = source
        self.pos    = 0
        self.line   = 1
        self.tokens = []
        self.indent_stack = [0]   # stack of indentation levels

    def error(self, msg):
        raise SyntaxError(f"[AmhaScript ስህተት — መስመር {self.line}]: {msg}")

    def peek(self, offset=0):
        idx = self.pos + offset
        return self.source[idx] if idx < len(self.source) else ''

    def advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
        return ch

    def tokenize(self):
        self._tokenize_lines()
        # Flush remaining DEDENTs
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token(TT_DEDENT, '', self.line))
        self.tokens.append(Token(TT_EOF, '', self.line))
        return self.tokens

    def _tokenize_lines(self):
        lines = self.source.splitlines(keepends=True)
        logical_lines = self._join_continuation(lines)

        for raw_line in logical_lines:
            stripped = raw_line.rstrip('\n\r')
            # Skip blank / comment lines
            if not stripped.strip() or stripped.strip().startswith('#'):
                continue

            # Measure indentation
            indent = len(stripped) - len(stripped.lstrip())
            current = self.indent_stack[-1]

            if indent > current:
                self.indent_stack.append(indent)
                self.tokens.append(Token(TT_INDENT, indent, self.line))
            elif indent < current:
                while self.indent_stack[-1] > indent:
                    self.indent_stack.pop()
                    self.tokens.append(Token(TT_DEDENT, '', self.line))
                if self.indent_stack[-1] != indent:
                    self.error(f"ኢንዴንት ስህተት (indentation error)")

            # Tokenise the rest of the line (after indentation)
            self._tokenize_segment(stripped.lstrip())
            self.tokens.append(Token(TT_NEWLINE, '\n', self.line))
            self.line += 1

    def _join_continuation(self, lines):
        """Join lines ending with \\ (continuation). Simple pass-through here."""
        return lines

    def _tokenize_segment(self, segment: str):
        i = 0
        while i < len(segment):
            ch = segment[i]

            # Skip spaces / tabs
            if ch in (' ', '\t'):
                i += 1
                continue

            # Comment
            if ch == '#':
                break

            # String literal
            if ch in ('"', "'"):
                quote = ch
                j = i + 1
                while j < len(segment) and segment[j] != quote:
                    j += 1
                value = segment[i+1:j]
                self.tokens.append(Token(TT_STRING, value, self.line))
                i = j + 1
                continue

            # Number
            if ch.isdigit() or (ch == '.' and i+1 < len(segment) and segment[i+1].isdigit()):
                j = i
                while j < len(segment) and (segment[j].isdigit() or segment[j] == '.'):
                    j += 1
                self.tokens.append(Token(TT_NUMBER, segment[i:j], self.line))
                i = j
                continue

            # Two-char operators
            two = segment[i:i+2]
            if two == '==':
                self.tokens.append(Token(TT_EQ, '==', self.line)); i += 2; continue
            if two == '!=':
                self.tokens.append(Token(TT_NEQ, '!=', self.line)); i += 2; continue
            if two == '<=':
                self.tokens.append(Token(TT_LTE, '<=', self.line)); i += 2; continue
            if two == '>=':
                self.tokens.append(Token(TT_GTE, '>=', self.line)); i += 2; continue

            # Single-char operators / punctuation
            singles = {
                '+': TT_PLUS, '-': TT_MINUS, '*': TT_MUL, '/': TT_DIV,
                '<': TT_LT,   '>': TT_GT,    '(': TT_LPAREN, ')': TT_RPAREN,
                ',': TT_COMMA, ':': TT_COLON,
            }
            if ch in singles:
                self.tokens.append(Token(singles[ch], ch, self.line))
                i += 1
                continue

            # Amharic word or ASCII identifier
            # Amharic Unicode: Ethiopic block U+1200–U+137F and extended U+2D80–U+2DDF
            j = i
            while j < len(segment):
                c = segment[j]
                code = ord(c)
                is_ethiopic = (0x1200 <= code <= 0x137F) or (0x2D80 <= code <= 0x2DDF)
                is_alnum    = c.isalnum() or c == '_'
                if is_ethiopic or is_alnum:
                    j += 1
                else:
                    break

            if j > i:
                word = segment[i:j]
                if word in KEYWORDS:
                    self.tokens.append(Token(KEYWORDS[word], word, self.line))
                else:
                    self.tokens.append(Token(TT_IDENT, word, self.line))
                i = j
                continue

            self.error(f"ያልታወቀ ቁምፊ: '{ch}'")


# ═══════════════════════════════════════════════════════════════
#  AST NODES
# ═══════════════════════════════════════════════════════════════
class ProgramNode:
    def __init__(self, stmts): self.stmts = stmts

class AssignNode:
    def __init__(self, name, expr): self.name = name; self.expr = expr

class IfNode:
    def __init__(self, cond, then_body, else_body):
        self.cond = cond; self.then_body = then_body; self.else_body = else_body

class WhileNode:
    def __init__(self, cond, body): self.cond = cond; self.body = body

class FuncDefNode:
    def __init__(self, name, params, body):
        self.name = name; self.params = params; self.body = body

class ReturnNode:
    def __init__(self, expr): self.expr = expr

class PrintNode:
    def __init__(self, expr): self.expr = expr

class FuncCallNode:
    def __init__(self, name, args): self.name = name; self.args = args

class BinOpNode:
    def __init__(self, left, op, right): self.left = left; self.op = op; self.right = right

class UnaryOpNode:
    def __init__(self, op, operand): self.op = op; self.operand = operand

class NumberNode:
    def __init__(self, value): self.value = value

class StringNode:
    def __init__(self, value): self.value = value

class IdentNode:
    def __init__(self, name): self.name = name

class BoolNode:
    def __init__(self, value): self.value = value   # True / False

class PassNode:
    pass


# ═══════════════════════════════════════════════════════════════
#  PARSER  (Recursive-Descent)
# ═══════════════════════════════════════════════════════════════
class Parser:
    """
    Builds an AST from the token stream produced by the Lexer.
    Grammar (simplified):

    program   := stmt*
    stmt      := assign | if_stmt | while_stmt | func_def | return_stmt
                 | print_stmt | expr_stmt | pass_stmt
    assign    := VAR_DECL IDENT ASSIGN expr NEWLINE
    if_stmt   := IF expr COLON NEWLINE INDENT stmt+ DEDENT
                 (ELSE COLON NEWLINE INDENT stmt+ DEDENT)?
    while_stmt:= WHILE expr COLON NEWLINE INDENT stmt+ DEDENT
    func_def  := DEF IDENT LPAREN params RPAREN COLON NEWLINE INDENT stmt+ DEDENT
    return_st := RETURN expr NEWLINE
    print_st  := PRINT LPAREN expr RPAREN NEWLINE
    expr_stmt := expr NEWLINE
    expr      := comparison ((AND|OR) comparison)*
    comparison:= term ((==|!=|<|>|<=|>=) term)*
    term      := factor ((+|-) factor)*
    factor    := unary ((*|/) unary)*
    unary     := NOT unary | primary
    primary   := NUMBER | STRING | TRUE | FALSE | IDENT (LPAREN args RPAREN)?
                 | LPAREN expr RPAREN
    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos    = 0

    def error(self, msg):
        tok = self.current()
        raise SyntaxError(
            f"[AmhaScript ስህተት — line {tok.line}]: {msg} (got {tok.type!r}: {tok.value!r})"
        )

    def current(self):
        return self.tokens[self.pos]

    def peek(self, offset=1):
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else Token(TT_EOF, '')

    def consume(self, expected_type=None):
        tok = self.current()
        if expected_type and tok.type != expected_type:
            self.error(f"Expected {expected_type!r}")
        self.pos += 1
        return tok

    def skip_newlines(self):
        while self.current().type == TT_NEWLINE:
            self.pos += 1

    def parse(self):
        self.skip_newlines()
        stmts = []
        while self.current().type != TT_EOF:
            stmts.append(self.parse_stmt())
            self.skip_newlines()
        return ProgramNode(stmts)

    def parse_stmt(self):
        tok = self.current()

        if tok.type == TT_VAR_DECL:
            return self.parse_assign()
        elif tok.type == TT_IF:
            return self.parse_if()
        elif tok.type == TT_WHILE:
            return self.parse_while()
        elif tok.type == TT_DEF:
            return self.parse_func_def()
        elif tok.type == TT_RETURN:
            return self.parse_return()
        elif tok.type == TT_PRINT:
            return self.parse_print()
        elif tok.type == TT_PASS:
            self.consume(TT_PASS)
            self._eat_newline()
            return PassNode()
        else:
            # Expression statement (e.g. bare function call)
            node = self.parse_expr()
            self._eat_newline()
            return node

    def _eat_newline(self):
        if self.current().type == TT_NEWLINE:
            self.consume(TT_NEWLINE)

    # ── Assignment: ቁጥር <name> ሰጥ <expr>
    def parse_assign(self):
        self.consume(TT_VAR_DECL)
        name_tok = self.consume(TT_IDENT)
        self.consume(TT_ASSIGN)
        expr = self.parse_expr()
        self._eat_newline()
        return AssignNode(name_tok.value, expr)

    # ── If: ከሆነ <cond>: NEWLINE INDENT body DEDENT [ካልሆነ: …]
    def parse_if(self):
        self.consume(TT_IF)
        cond = self.parse_expr()
        self.consume(TT_COLON)
        self._eat_newline()
        then_body = self.parse_block()
        else_body = []
        if self.current().type == TT_ELSE:
            self.consume(TT_ELSE)
            self.consume(TT_COLON)
            self._eat_newline()
            else_body = self.parse_block()
        return IfNode(cond, then_body, else_body)

    # ── While: እስኪሆን <cond>: NEWLINE INDENT body DEDENT
    def parse_while(self):
        self.consume(TT_WHILE)
        cond = self.parse_expr()
        self.consume(TT_COLON)
        self._eat_newline()
        body = self.parse_block()
        return WhileNode(cond, body)

    # ── Function def: ስራ <name>(<params>): NEWLINE INDENT body DEDENT
    def parse_func_def(self):
        self.consume(TT_DEF)
        name_tok = self.consume(TT_IDENT)
        self.consume(TT_LPAREN)
        params = []
        while self.current().type != TT_RPAREN:
            params.append(self.consume(TT_IDENT).value)
            if self.current().type == TT_COMMA:
                self.consume(TT_COMMA)
        self.consume(TT_RPAREN)
        self.consume(TT_COLON)
        self._eat_newline()
        body = self.parse_block()
        return FuncDefNode(name_tok.value, params, body)

    # ── Return: መልስ <expr>
    def parse_return(self):
        self.consume(TT_RETURN)
        expr = self.parse_expr()
        self._eat_newline()
        return ReturnNode(expr)

    # ── Print: ጥራ(<expr>)
    def parse_print(self):
        self.consume(TT_PRINT)
        self.consume(TT_LPAREN)
        expr = self.parse_expr()
        self.consume(TT_RPAREN)
        self._eat_newline()
        return PrintNode(expr)

    # ── Block: INDENT stmt+ DEDENT
    def parse_block(self):
        self.skip_newlines()
        self.consume(TT_INDENT)
        stmts = []
        while self.current().type not in (TT_DEDENT, TT_EOF):
            stmts.append(self.parse_stmt())
            self.skip_newlines()
        self.consume(TT_DEDENT)
        return stmts

    # ── Expressions ──────────────────────────────────────────
    def parse_expr(self):
        node = self.parse_comparison()
        while self.current().type in (TT_AND, TT_OR):
            op = self.consume().value
            right = self.parse_comparison()
            node = BinOpNode(node, op, right)
        return node

    def parse_comparison(self):
        node = self.parse_term()
        cmp_types = (TT_EQ, TT_NEQ, TT_LT, TT_GT, TT_LTE, TT_GTE)
        while self.current().type in cmp_types:
            op = self.consume().value
            right = self.parse_term()
            node = BinOpNode(node, op, right)
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.current().type in (TT_PLUS, TT_MINUS):
            op = self.consume().value
            right = self.parse_factor()
            node = BinOpNode(node, op, right)
        return node

    def parse_factor(self):
        node = self.parse_unary()
        while self.current().type in (TT_MUL, TT_DIV):
            op = self.consume().value
            right = self.parse_unary()
            node = BinOpNode(node, op, right)
        return node

    def parse_unary(self):
        if self.current().type == TT_NOT:
            self.consume(TT_NOT)
            return UnaryOpNode('not', self.parse_unary())
        if self.current().type == TT_MINUS:
            self.consume(TT_MINUS)
            return UnaryOpNode('-', self.parse_unary())
        return self.parse_primary()

    def parse_primary(self):
        tok = self.current()

        if tok.type == TT_NUMBER:
            self.consume()
            val = float(tok.value) if '.' in tok.value else int(tok.value)
            return NumberNode(val)

        if tok.type == TT_STRING:
            self.consume()
            return StringNode(tok.value)

        if tok.type == TT_TRUE:
            self.consume()
            return BoolNode(True)

        if tok.type == TT_FALSE:
            self.consume()
            return BoolNode(False)

        if tok.type == TT_IDENT:
            name = self.consume().value
            # Function call?
            if self.current().type == TT_LPAREN:
                self.consume(TT_LPAREN)
                args = []
                while self.current().type != TT_RPAREN:
                    args.append(self.parse_expr())
                    if self.current().type == TT_COMMA:
                        self.consume(TT_COMMA)
                self.consume(TT_RPAREN)
                return FuncCallNode(name, args)
            return IdentNode(name)

        if tok.type == TT_LPAREN:
            self.consume(TT_LPAREN)
            expr = self.parse_expr()
            self.consume(TT_RPAREN)
            return expr

        self.error(f"ያልተጠበቀ ቶከን")


# ═══════════════════════════════════════════════════════════════
#  CODE GENERATOR  (AST → Python source)
# ═══════════════════════════════════════════════════════════════
class CodeGen:
    """Walks the AST and emits valid, readable Python code."""

    def __init__(self):
        self.indent_level = 0
        self.lines        = []

    def indent(self):
        return '    ' * self.indent_level

    def emit(self, line=''):
        self.lines.append(self.indent() + line)

    def generate(self, node):
        self.visit(node)
        return '\n'.join(self.lines) + '\n'

    def visit(self, node):
        method = 'visit_' + type(node).__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise NotImplementedError(f"No visitor for {type(node).__name__}")

    # ── Program
    def visit_ProgramNode(self, node):
        self.emit('# Generated by AmhaScript Translator v1.0')
        self.emit('# Adama Science and Technology University — CSEg 4306')
        self.emit()
        for stmt in node.stmts:
            self.visit(stmt)

    # ── Assignment
    def visit_AssignNode(self, node):
        self.emit(f'{node.name} = {self.visit(node.expr)}')

    # ── If / Else
    def visit_IfNode(self, node):
        self.emit(f'if {self.visit(node.cond)}:')
        self.indent_level += 1
        for stmt in node.then_body:
            self.visit(stmt)
        self.indent_level -= 1
        if node.else_body:
            self.emit('else:')
            self.indent_level += 1
            for stmt in node.else_body:
                self.visit(stmt)
            self.indent_level -= 1

    # ── While
    def visit_WhileNode(self, node):
        self.emit(f'while {self.visit(node.cond)}:')
        self.indent_level += 1
        for stmt in node.body:
            self.visit(stmt)
        self.indent_level -= 1

    # ── Function def
    def visit_FuncDefNode(self, node):
        params = ', '.join(node.params)
        self.emit(f'def {node.name}({params}):')
        self.indent_level += 1
        for stmt in node.body:
            self.visit(stmt)
        self.indent_level -= 1
        self.emit()

    # ── Return
    def visit_ReturnNode(self, node):
        self.emit(f'return {self.visit(node.expr)}')

    # ── Print
    def visit_PrintNode(self, node):
        self.emit(f'print({self.visit(node.expr)})')

    # ── Pass
    def visit_PassNode(self, node):
        self.emit('pass')

    # ── Expressions (return strings)
    def visit_FuncCallNode(self, node):
        args = ', '.join(self.visit(a) for a in node.args)
        return f'{node.name}({args})'

    def visit_BinOpNode(self, node):
        left  = self.visit(node.left)
        right = self.visit(node.right)
        op    = node.op
        # Map Amharic logical keywords to Python
        if op == 'እና': op = 'and'
        if op == 'ወይም': op = 'or'
        return f'({left} {op} {right})'

    def visit_UnaryOpNode(self, node):
        operand = self.visit(node.operand)
        op = 'not' if node.op == 'not' else node.op
        return f'({op} {operand})'

    def visit_NumberNode(self, node):
        return str(node.value)

    def visit_StringNode(self, node):
        # Escape any inner quotes
        escaped = node.value.replace('"', '\\"')
        return f'"{escaped}"'

    def visit_IdentNode(self, node):
        return node.name

    def visit_BoolNode(self, node):
        return 'True' if node.value else 'False'

    # Bare expression statement (e.g. standalone function call)
    def visit_FuncCallNode_stmt(self, node):
        self.emit(self.visit_FuncCallNode(node))


# ═══════════════════════════════════════════════════════════════
#  EXPRESSION STATEMENT HOOK
#  (Function call used as a statement needs emit, not return)
# ═══════════════════════════════════════════════════════════════
# Patch CodeGen so a bare FuncCallNode as a statement emits a line
_orig_visit = CodeGen.visit

def _patched_visit(self, node):
    # If a FuncCallNode appears where a statement is expected, emit it
    # (The parser returns it directly from parse_stmt)
    if isinstance(node, FuncCallNode) and self.indent_level >= 0:
        result = self.visit_FuncCallNode(node)
        # Only emit if this is a "statement context": check if lines[-1] doesn't end with result
        # Simplest: always emit for FuncCallNode at statement level
        # We detect statement context by checking the call stack depth — instead,
        # let CodeGen.visit handle FuncCallNode specially:
        pass
    return _orig_visit(self, node)

# Better approach: add a visit_FuncCallNode that emits when called from visit_ProgramNode
# The cleanest solution: the parser wraps bare calls in an ExprStmt node:
class ExprStmtNode:
    def __init__(self, expr): self.expr = expr

# Patch Parser.parse_stmt to wrap:
_orig_parse_stmt = Parser.parse_stmt
def _new_parse_stmt(self):
    tok = self.current()
    if tok.type not in (TT_VAR_DECL, TT_IF, TT_WHILE, TT_DEF,
                        TT_RETURN, TT_PRINT, TT_PASS):
        node = self.parse_expr()
        self._eat_newline()
        return ExprStmtNode(node)
    return _orig_parse_stmt(self)
Parser.parse_stmt = _new_parse_stmt

def visit_ExprStmtNode(self, node):
    self.emit(self.visit(node.expr))
CodeGen.visit_ExprStmtNode = visit_ExprStmtNode


# ═══════════════════════════════════════════════════════════════
#  MAIN  — CLI entry point
# ═══════════════════════════════════════════════════════════════
def translate(source_path: str) -> str:
    """Read an AmhaScript file, translate to Python, write .py file. Returns output path."""
    with open(source_path, 'r', encoding='utf-8') as f:
        source = f.read()

    # 1. Lex
    lexer  = Lexer(source)
    tokens = lexer.tokenize()

    # 2. Parse
    parser = Parser(tokens)
    ast    = parser.parse()

    # 3. Generate
    gen    = CodeGen()
    python = gen.generate(ast)

    # 4. Write output
    base = os.path.splitext(source_path)[0]
    out_path = base + '.py'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(python)

    return out_path


def main():
    if len(sys.argv) < 2:
        print("አጠቃቀም: python translator.py <program.as>")
        print("Usage : python translator.py <program.as>")
        sys.exit(1)

    source_path = sys.argv[1]
    if not os.path.isfile(source_path):
        print(f"ፋይል አልተገኘም: {source_path}")
        sys.exit(1)

    try:
        out = translate(source_path)
        print(f"ትርጉም ተሳካ! ↳  {out}")
        print(f"Translation successful! ↳  {out}")
    except SyntaxError as e:
        print(str(e))
        sys.exit(1)


def run(source_path: str):
    """
    Translate and immediately run an AmhaScript file.
    Use this inside any Python file:

        from translator import run
        run('calculator.as')
    """
    if not os.path.isfile(source_path):
        print(f"ፋይል አልተገኘም / File not found: {source_path}")
        return

    try:
        out_path = translate(source_path)
        print(f"✅ Translation successful! ↳  {out_path}")
        print("-" * 40)
        # Read and execute the generated Python file
        with open(out_path, 'r', encoding='utf-8') as f:
            code = f.read()
        exec(compile(code, out_path, 'exec'), {})
    except SyntaxError as e:
        print(str(e))


if __name__ == '__main__':
    main()

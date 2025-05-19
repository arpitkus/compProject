# lexer.py

import re

# Token specification: order matters (longer operators first)
token_specification = [
    ('INT',      r'\bint\b'),
    ('MAIN',     r'\bmain\b'),
    ('IF',       r'\bif\b'),
    ('ELSE',     r'\belse\b'),
    ('WHILE',    r'\bwhile\b'),
    ('FOR',      r'\bfor\b'),
    ('DO',       r'\bdo\b'),
    ('RETURN',   r'\breturn\b'),
    ('ID',       r'[A-Za-z_][A-Za-z0-9_]*'),
    ('NUM',      r'\d+'),
    ('STRING',   r'\".*?\"'),                         # string literals, non‐greedy
    ('OP',       r'==|!=|<=|>=|<<|>>|[+\-*/%=<>]'),    # include <<, >> and %
    ('LPAREN',   r'\('),
    ('RPAREN',   r'\)'),
    ('LBRACE',   r'\{'),
    ('RBRACE',   r'\}'),
    ('SEMI',     r';'),
    ('SKIP',     r'[ \t\n]+'),   # whitespace (skip)
    ('MISMATCH', r'.'),          # any other single character → error
]

# Build the combined regex with named groups
tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
get_token = re.compile(tok_regex).match

def lexer(code: str):
    """
    Convert source code string into a list of tokens.
    Each token is a dict: {'type': token_name, 'value': token_text}.
    Raises RuntimeError if an unexpected character is found.
    """
    pos = 0
    tokens = []
    mo = get_token(code)
    while mo is not None:
        typ = mo.lastgroup
        if typ == 'SKIP':
            pass
        elif typ == 'MISMATCH':
            # If a character doesn’t match any token pattern → error
            raise RuntimeError(f'Unexpected character {mo.group()!r} at position {pos}')
        else:
            val = mo.group(typ)
            tokens.append({'type': typ, 'value': val})
        pos = mo.end()
        mo = get_token(code, pos)
    return tokens

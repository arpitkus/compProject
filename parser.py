# parser.py

from astnode import ASTNode

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return {'type': 'EOF', 'value': None}

    def eat(self, token_type):
        """
        Consume the current token if it matches token_type; otherwise raise an error.
        """
        current = self.current()
        if current['type'] == token_type:
            self.pos += 1
            return current
        raise RuntimeError(f"Expected token type {token_type} but got {current['type']} ({current['value']})")

    def parse(self):
        return self.program()

    # ------------------------
    # PROGRAM / FUNCTION RULES
    # ------------------------
    def program(self):
        node = ASTNode('program')
        node.add_child(self.function())
        return node

    def function(self):
        node = ASTNode('function')
        node.add_child(self.type_spec())         # 'int'
        main_tok = self.eat('MAIN')              # 'main'
        node.add_child(ASTNode('main', main_tok['value']))
        self.eat('LPAREN')                       # '('
        self.eat('RPAREN')                       # ')'
        node.add_child(self.compound_stmt())     # '{ … }'
        return node

    def type_spec(self):
        # Only 'int' is supported as a type keyword in this mini‐parser
        tok = self.eat('INT')
        return ASTNode('type', tok['value'])

    # ------------------------
    # STATEMENT RULES
    # ------------------------
    def compound_stmt(self):
        """
        compound_stmt → '{' stmt* '}'
        """
        node = ASTNode('compound_stmt')
        self.eat('LBRACE')
        while self.current()['type'] in ('INT', 'ID', 'IF', 'RETURN', 'WHILE', 'FOR', 'DO'):
            node.add_child(self.stmt())
        self.eat('RBRACE')
        return node

    def stmt(self):
        """
        stmt → var_decl
             | assign_stmt
             | if_stmt
             | while_stmt
             | for_stmt
             | do_while_stmt
             | return_stmt
             | generic_stmt   ← anything up to next semicolon
        """
        tok = self.current()

        if tok['type'] == 'INT':
            return self.var_decl()

        elif tok['type'] == 'ID':
            # Could be assignment (x = …) or something else up to the next ';'.
            next_tok = self.tokens[self.pos + 1] if (self.pos + 1) < len(self.tokens) else {'type': 'EOF'}
            if next_tok['type'] == 'OP' and next_tok['value'] == '=':
                return self.assign_stmt()
            else:
                # Generic statement: gather tokens until the next SEMICOLON
                text_tokens = []
                while self.current()['type'] != 'SEMI' and self.current()['type'] != 'EOF':
                    text_tokens.append(self.current()['value'])
                    self.pos += 1
                if self.current()['type'] == 'SEMI':
                    text_tokens.append(self.eat('SEMI')['value'])
                raw_text = " ".join(text_tokens).strip()
                return ASTNode('stmt', raw_text)

        elif tok['type'] == 'IF':
            return self.if_stmt()

        elif tok['type'] == 'RETURN':
            return self.return_stmt()

        elif tok['type'] == 'WHILE':
            return self.while_stmt()

        elif tok['type'] == 'FOR':
            return self.for_stmt()

        elif tok['type'] == 'DO':
            return self.do_while_stmt()

        else:
            raise RuntimeError(f"Unexpected token in stmt(): {tok}")

    def var_decl(self):
        """
        var_decl → 'int' ID [ '=' expr ] ';'
        """
        node = ASTNode('var_decl')
        node.add_child(self.type_spec())     # 'int'
        id_tok = self.eat('ID')             # variable name
        node.add_child(ASTNode('id', id_tok['value']))
        if self.current()['type'] == 'OP' and self.current()['value'] == '=':
            self.eat('OP')
            node.add_child(self.expr())
        self.eat('SEMI')
        return node

    def assign_stmt(self):
        """
        assign_stmt → ID '=' expr ';'
        """
        node = ASTNode('assign')
        id_tok = self.eat('ID')
        node.add_child(ASTNode('id', id_tok['value']))
        self.eat('OP')       # '='
        node.add_child(self.expr())
        self.eat('SEMI')
        return node

    def if_stmt(self):
        """
        if_stmt → 'if' '(' expr ')' ( compound_stmt | stmt ) [ 'else' ( compound_stmt | stmt ) ]
        """
        node = ASTNode('if_stmt')
        self.eat('IF')
        self.eat('LPAREN')
        node.add_child(self.expr())
        self.eat('RPAREN')

        # THEN‐branch (either a block or a single statement)
        if self.current()['type'] == 'LBRACE':
            node.add_child(self.compound_stmt())
        else:
            node.add_child(self.stmt())

        # optional ELSE
        if self.current()['type'] == 'ELSE':
            self.eat('ELSE')
            if self.current()['type'] == 'LBRACE':
                node.add_child(self.compound_stmt())
            else:
                node.add_child(self.stmt())

        return node

    def while_stmt(self):
        """
        while_stmt → 'while' '(' expr ')' ( compound_stmt | stmt )
        """
        node = ASTNode('while')
        self.eat('WHILE')
        self.eat('LPAREN')
        node.add_child(self.expr())
        self.eat('RPAREN')
        if self.current()['type'] == 'LBRACE':
            node.add_child(self.compound_stmt())
        else:
            node.add_child(self.stmt())
        return node

    def for_stmt(self):
        """
        for_stmt → 'for' '(' ( var_decl | assign_stmt | ';' ) expr? ';' assign_expr? ')' ( compound_stmt | stmt )
        """
        node = ASTNode('for')
        self.eat('FOR')
        self.eat('LPAREN')

        # INIT clause
        if self.current()['type'] == 'INT':
            init_node = self.var_decl()
        elif self.current()['type'] == 'ID':
            init_node = self.assign_stmt()
        else:
            init_node = None
            self.eat('SEMI')
        node.add_child(init_node)

        # COND clause
        if self.current()['type'] != 'SEMI':
            cond_node = self.expr()
            self.eat('SEMI')
        else:
            cond_node = None
            self.eat('SEMI')
        node.add_child(cond_node)

        # UPDATE clause (no semicolon)
        if self.current()['type'] == 'ID':
            upd_node = self.assign_expr()
        else:
            upd_node = None
        node.add_child(upd_node)

        self.eat('RPAREN')

        # LOOP BODY
        if self.current()['type'] == 'LBRACE':
            node.add_child(self.compound_stmt())
        else:
            node.add_child(self.stmt())

        return node

    def do_while_stmt(self):
        """
        do_while_stmt → 'do' ( compound_stmt | stmt ) 'while' '(' expr ')' ';'
        """
        node = ASTNode('do_while')
        self.eat('DO')
        if self.current()['type'] == 'LBRACE':
            node.add_child(self.compound_stmt())
        else:
            node.add_child(self.stmt())
        self.eat('WHILE')
        self.eat('LPAREN')
        node.add_child(self.expr())
        self.eat('RPAREN')
        self.eat('SEMI')
        return node

    def return_stmt(self):
        """
        return_stmt → 'return' expr ';'
        """
        node = ASTNode('return_stmt')
        self.eat('RETURN')
        node.add_child(self.expr())
        self.eat('SEMI')
        return node

    def assign_expr(self):
        """
        assign_expr → ID '=' expr    (used in for‐loop update)
        """
        node = ASTNode('assign')
        id_tok = self.eat('ID')
        node.add_child(ASTNode('id', id_tok['value']))
        self.eat('OP')  # '='
        node.add_child(self.expr())
        return node

    # ------------------------
    # EXPRESSION RULES
    # ------------------------
    def expr(self):
        """
        expr → arith_expr ( (<|>|==|!=|<=|>=) arith_expr )?
        """
        node = self.arith_expr()
        if (self.current()['type'] == 'OP' and 
            self.current()['value'] in ('<', '>', '==', '!=', '<=', '>=')):
            op_tok = self.eat('OP')
            new_node = ASTNode('comparison', op_tok['value'])
            new_node.add_child(node)
            new_node.add_child(self.arith_expr())
            return new_node
        return node

    def arith_expr(self):
        """
        arith_expr → term ( (+|-) term )*
        """
        node = self.term()
        while self.current()['type'] == 'OP' and self.current()['value'] in ('+', '-'):
            op_tok = self.eat('OP')
            new_node = ASTNode('arith_expr', op_tok['value'])
            new_node.add_child(node)
            new_node.add_child(self.term())
            node = new_node
        return node

    def term(self):
        """
        term → factor ( (*|/|%) factor )*
        """
        node = self.factor()
        while self.current()['type'] == 'OP' and self.current()['value'] in ('*', '/', '%'):
            op_tok = self.eat('OP')
            new_node = ASTNode('term', op_tok['value'])
            new_node.add_child(node)
            new_node.add_child(self.factor())
            node = new_node
        return node

    def factor(self):
        """
        factor → NUM | ID | '(' expr ')'
        """
        tok = self.current()
        if tok['type'] == 'NUM':
            self.eat('NUM')
            return ASTNode('num', tok['value'])
        elif tok['type'] == 'ID':
            self.eat('ID')
            return ASTNode('id', tok['value'])
        elif tok['type'] == 'LPAREN':
            self.eat('LPAREN')
            node = self.expr()
            self.eat('RPAREN')
            return node
        else:
            raise RuntimeError(f"Unexpected factor token {tok}")

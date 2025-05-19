# semantic.py

class SemanticAnalyzer:
    def __init__(self):
        self.symbols = set()   # set of declared variable names
        self.errors = []       # list of error messages

    def analyze(self, node):
        method_name = 'visit_' + node.type
        visitor = getattr(self, method_name, self.generic_visit)
        visitor(node)

    def generic_visit(self, node):
        for child in (node.children or []):
            if child:
                self.analyze(child)

    def visit_var_decl(self, node):
        # var_decl: children = [ ASTNode('type','int'), ASTNode('id', var_name), optional initializer ]
        id_node = node.children[1]
        var_name = id_node.value
        if var_name in self.symbols:
            self.errors.append(f"Semantic Error: Variable '{var_name}' already declared")
        else:
            self.symbols.add(var_name)
        # If there is an initializer expression, analyze it
        if len(node.children) == 3:
            self.analyze(node.children[2])

    def visit_assign(self, node):
        # assign: children = [ ASTNode('id', var_name), expression_node ]
        id_node = node.children[0]
        var_name = id_node.value
        if var_name not in self.symbols:
            self.errors.append(f"Semantic Error: Variable '{var_name}' used before declaration")
        # Analyze right-hand side expression
        self.analyze(node.children[1])

    def visit_id(self, node):
        var_name = node.value
        if var_name not in self.symbols:
            self.errors.append(f"Semantic Error: Variable '{var_name}' used before declaration")

    def visit_if_stmt(self, node):
        # children: [ condition_expr, then_subtree, optional else_subtree ]
        self.analyze(node.children[0])
        self.analyze(node.children[1])
        if len(node.children) == 3:
            self.analyze(node.children[2])

    def visit_while(self, node):
        # children: [ condition_expr, body_subtree ]
        self.analyze(node.children[0])
        self.analyze(node.children[1])

    def visit_for(self, node):
        # children: [ init_subtree, cond_expr, upd_subtree, body_subtree ]
        if node.children[0]:
            self.analyze(node.children[0])
        if node.children[1]:
            self.analyze(node.children[1])
        if node.children[2]:
            self.analyze(node.children[2])
        self.analyze(node.children[3])

    def visit_do_while(self, node):
        # children: [ body_subtree, condition_expr ]
        self.analyze(node.children[0])
        self.analyze(node.children[1])

    def visit_return_stmt(self, node):
        # children: [ expression_node ]
        self.analyze(node.children[0])

# flowchart.py

import graphviz
from astnode import ASTNode

class FlowchartGenerator:
    def __init__(self):
        # Create a Graphviz Digraph; we’ll render as a PNG with top-to-bottom layout
        self.dot = graphviz.Digraph('flowchart', format='png')
        self.dot.attr(rankdir='TB')
        self.node_count = 0     # to generate unique node IDs like 'node1', 'node2', …
        self.last_node = None   # the ID of the most recently created node, so we know where to draw the next arrow from
        self.merge_stack = []   # stack of "invisible merge" node IDs for nested ifs

    def _new_node_id(self):
        self.node_count += 1
        return f'node{self.node_count}'

    def _formatter(self, node: ASTNode) -> str:
        """
        Return a human-readable label for each AST node type:
        - var_decl  → 'int x = 5'  or 'int x'
        - assign    → 'x = expr'
        - return    → 'return expr'
        - stmt      → raw statement text (e.g. 'cin >> x;')
        - if_stmt   → 'if (condition)'
        - while     → 'while (condition)'
        - for       → 'for (init; cond; update)'
        - do_while  → 'do … while'
        """
        if node.type == 'var_decl':
            # children = [ type_node, id_node, optional initializer ]
            var_type = node.children[0].value
            var_name = node.children[1].value
            if len(node.children) == 3:
                expr_str = self._expr_to_str(node.children[2])
                return f"{var_type} {var_name} = {expr_str}"
            return f"{var_type} {var_name}"

        elif node.type == 'assign':
            # children = [ id_node, expr_node ]
            var_name = node.children[0].value
            expr_str = self._expr_to_str(node.children[1])
            return f"{var_name} = {expr_str}"

        elif node.type == 'return_stmt':
            expr_str = self._expr_to_str(node.children[0])
            return f"return {expr_str}"

        elif node.type == 'stmt':
            # generic statement, e.g. 'cin >> x;'
            return node.value

        elif node.type == 'if_stmt':
            cond = self._expr_to_str(node.children[0])
            return f"if ({cond})"

        elif node.type == 'while':
            cond = self._expr_to_str(node.children[0])
            return f"while ({cond})"

        elif node.type == 'for':
            init = node.children[0]
            cond = node.children[1]
            upd = node.children[2]
            parts = []
            parts.append(self._formatter(init) if init else "")
            parts.append(self._expr_to_str(cond) if cond else "")
            parts.append(self._formatter(upd) if upd else "")
            return "for (" + "; ".join(parts) + ")"

        elif node.type == 'do_while':
            return "do … while"

        else:
            return str(node.type)

    def _expr_to_str(self, node: ASTNode) -> str:
        """
        Convert expression subtree into a single string.
        Recognizes: num, id, comparison, arith_expr, term.
        """
        if not node:
            return ""
        if node.type == 'num':
            return node.value
        elif node.type == 'id':
            return node.value
        elif node.type in ('comparison', 'arith_expr', 'term'):
            left = self._expr_to_str(node.children[0])
            right = self._expr_to_str(node.children[1])
            return f"{left} {node.value} {right}"
        else:
            return str(node.type)

    def generate(self, ast_root: ASTNode) -> graphviz.Digraph:
        """
        Given the root AST node (type='program'), build the entire Graphviz graph.
        1. Create a "Start" oval
        2. Walk the AST, creating boxes/diamonds and edges
        3. Create an "End" oval
        """
        # 1) Start oval
        start_id = self._new_node_id()
        self.dot.node(start_id, "Start", shape="oval")
        self.last_node = start_id

        # 2) Recursively process the AST
        self._process_node(ast_root)

        # 3) End oval
        end_id = self._new_node_id()
        self.dot.node(end_id, "End", shape="oval")
        if self.last_node:
            self.dot.edge(self.last_node, end_id)

        return self.dot

    def _make_invisible_merge(self) -> str:
        """
        Create an invisible point node so that multiple incoming edges visually merge
        rather than overlap. Return its node‐ID.
        """
        merge_id = self._new_node_id()
        self.dot.node(merge_id, "", shape="point", width="0.01", style="invis")
        return merge_id

    def _process_node(self, node: ASTNode):
        """
        Recursively walk the AST and create Graphviz nodes + edges:
          - var_decl, assign, return_stmt, stmt → a rectangle (box)
          - if_stmt → a diamond with two outgoing edges (true/false), plus an invisible merge
          - while, for, do_while → diamonds with loop‐back edges and a single false→merge
          - compound_stmt, function, program → just recurse into children
        """

        # 1) program / function / compound_stmt: just recurse over children
        if node.type in ('program', 'function', 'compound_stmt'):
            for child in (node.children or []):
                if child:
                    self._process_node(child)

        # 2) Basic “process” nodes:
        elif node.type in ('var_decl', 'assign', 'return_stmt', 'stmt'):
            box_id = self._new_node_id()
            label = self._formatter(node)
            self.dot.node(box_id, label, shape="box")
            if self.last_node:
                self.dot.edge(self.last_node, box_id)
            self.last_node = box_id

        # 3) IF statements
        elif node.type == 'if_stmt':
            decision_id = self._new_node_id()
            self.dot.node(decision_id, self._formatter(node), shape="diamond")
            if self.last_node:
                self.dot.edge(self.last_node, decision_id)

            # (a) THEN branch
            before_then = self.node_count
            self.last_node = decision_id
            self._process_node(node.children[1])  # then‐subtree
            then_end = self.last_node
            then_entry = f'node{before_then + 1}'

            # (b) ELSE branch?
            if len(node.children) == 3:
                before_else = self.node_count
                self.last_node = decision_id
                self._process_node(node.children[2])  # else‐subtree
                else_end = self.last_node
                else_entry = f'node{before_else + 1}'

                merge_id = self._make_invisible_merge()
                self.merge_stack.append(merge_id)

                self.dot.edge(then_end, merge_id)
                self.dot.edge(else_end, merge_id)
                self.dot.edge(decision_id, then_entry, label="true")
                self.dot.edge(decision_id, else_entry, label="false")

                self.last_node = merge_id

            else:
                # No ELSE: create or reuse a merge point
                reused = False
                if self.merge_stack and then_end == self.merge_stack[-1]:
                    merge_id = then_end
                    reused = True
                else:
                    merge_id = self._make_invisible_merge()
                    self.merge_stack.append(merge_id)

                if not reused:
                    self.dot.edge(then_end, merge_id)
                self.dot.edge(decision_id, then_entry, label="true")
                self.dot.edge(decision_id, mergerId, label="false")  # false → merge

                self.last_node = merge_id

        # 4) WHILE loops
        elif node.type == 'while':
            cond_id = self._new_node_id()
            self.dot.node(cond_id, self._formatter(node), shape="diamond")
            if self.last_node:
                self.dot.edge(self.last_node, cond_id)

            # Body: temporarily suppress auto-edge
            before_body = self.node_count
            self.last_node = None
            self._process_node(node.children[1])  # body
            body_end = self.last_node
            body_entry = f'node{before_body + 1}'

            self.dot.edge(cond_id, body_entry, label="true")
            self.dot.edge(body_end, cond_id)

            merge_id = self._make_invisible_merge()
            self.dot.edge(cond_id, merge_id, label="false")
            self.last_node = merge_id

        # 5) FOR loops
        elif node.type == 'for':
            # (a) init clause
            init_node = node.children[0]
            if init_node:
                self._process_node(init_node)

            # (b) condition diamond
            cond_id = self._new_node_id()
            cond_label = self._expr_to_str(node.children[1]) if node.children[1] else ""
            self.dot.node(cond_id, f"for_cond ({cond_label})", shape="diamond")
            if self.last_node:
                self.dot.edge(self.last_node, cond_id)

            # (c) body: suppress auto-edge
            before_body = self.node_count
            self.last_node = None
            self._process_node(node.children[3])
            body_end = self.last_node
            body_entry = f'node{before_body + 1}'

            self.dot.edge(cond_id, body_entry, label="true")

            # (d) update clause
            upd_node = node.children[2]
            if upd_node:
                upd_id = self._new_node_id()
                self.dot.node(upd_id, self._formatter(upd_node), shape="box")
                self.dot.edge(body_end, upd_id)
                self.dot.edge(upd_id, cond_id)
            else:
                self.dot.edge(body_end, cond_id)

            # (e) false → merge
            merge_id = self._make_invisible_merge()
            self.dot.edge(cond_id, merge_id, label="false")
            self.last_node = merge_id

        # 6) DO-WHILE loops
        elif node.type == 'do_while':
            before_body = self.node_count
            self._process_node(node.children[0])  # body
            body_end = self.last_node

            cond_id = self._new_node_id()
            cond_label = self._expr_to_str(node.children[1])
            self.dot.node(cond_id, f"while ({cond_label})", shape="diamond")
            self.dot.edge(body_end, cond_id)

            body_entry = f'node{before_body + 1}'
            self.dot.edge(cond_id, body_entry, label="true")

            merge_id = self._make_invisible_merge()
            self.dot.edge(cond_id, merge_id, label="false")
            self.last_node = merge_id

        # 7) ‘type’ and ‘main’ nodes are just structural—no visible shape
        elif node.type in ('type', 'main'):
            return

        # 8) Fallback: recurse on children
        else:
            for child in (node.children or []):
                if child:
                    self._process_node(child)

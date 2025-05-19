# astnode.py

class ASTNode:
    def __init__(self, nodetype, value=None):
        self.type = nodetype
        self.value = value    # e.g. 'id' node holds the identifier’s name, 'num' holds the number, 'stmt' holds raw statement text, etc.
        self.children = []    # list of child ASTNode instances

    def add_child(self, node):
        self.children.append(node)

    def __repr__(self, level=0):
        ret = "  " * level + f"{self.type}" + (f": {self.value}" if self.value else "") + "\n"
        for child in (self.children or []):
            if child:
                ret += child.__repr__(level + 1)
        return ret

Code to Flowchart Project
A compact Python/Tkinter app that:
- Lexes simple C/C++-style code into tokens
- Builds an AST and performs basic semantic checks
- Generates a flowchart PNG via Graphviz
Installation
1. Clone or download this repo:
   git clone https://github.com/arpitkus/compProject.git
   cd compProject
2. Install Python packages:
   pip install graphviz pillow
3. Install the Graphviz binary:
   - Windows: Download and install from https://graphviz.org/download/
   - macOS: brew install graphviz
   - Linux: sudo apt-get install graphviz
Usage
From the project folder, run:
python gui.py
- Code Input tab: paste or type your C/C++-style code.
- Click Parse & Analyze to view tokens, AST, and any semantic errors in the Analysis tab.
- Click Generate Flowchart to render flowchart.png and view it in the Flowchart tab.
File Overview
astnode.py
Defines ASTNode(type, value), with a children list and a __repr__ method.

lexer.py
lexer(code: str) → List[{ 'type', 'value' }]
Recognizes keywords (int, main, if, etc.), identifiers, numbers, strings, multi-char operators (==, !=, <<, >>), braces, semicolons. Raises on any mismatch.

parser.py
Parser(tokens).parse() → ASTNode('program')
Recursive-descent for:
- int main() { … }
- Declarations: int x; or int x = expr;
- Assignments: x = expr;
- if (expr) stmt [else stmt]
- while (expr) stmt
- for (init; cond; update) stmt
- do stmt while (expr);
- return expr;
- Any other …; becomes ASTNode('stmt', raw_text)

semantic.py
SemanticAnalyzer().analyze(ast)
- Tracks declared variables in one scope.
- Errors if variable used before declaration or redeclared.

flowchart.py
FlowchartGenerator().generate(ast) → graphviz.Digraph
- Creates 'Start' and 'End' ovals.
- Boxes for var_decl, assign, return, stmt.
- Diamonds for if, while, for, do_while (with true/false edges and invisible merge nodes).

gui.py
- Tkinter window with three tabs:
  1. Code Input (enter code + Parse & Analyze + Generate Flowchart)
  2. Analysis (displays tokens, AST, semantic errors)
  3. Flowchart (shows generated PNG via scrollable Canvas)
- Parse & Analyze runs lexer → parser → semantic and prints results.
- Generate Flowchart runs FlowchartGenerator, calls dot.render('flowchart', format='png'), and displays flowchart.png. If rendering fails, dumps raw DOT in Analysis tab.
Quick Start
1. Install dependencies (Python packages + Graphviz binary).
2. Run:
   python gui.py
3. Paste code, analyze, and generate a flowchart.

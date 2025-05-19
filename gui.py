# gui.py

import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
from PIL import Image, ImageTk

from lexer import lexer
from parser import Parser
from semantic import SemanticAnalyzer
from flowchart import FlowchartGenerator

class CodeToASTApp:
    def __init__(self, root):
        self.root = root
        root.title("C/C++-style Parser & Flowchart")

        # 1) Notebook with three tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # —— Tab 1: Code Input —— 
        self.input_frame = tk.Frame(self.notebook)
        self.notebook.add(self.input_frame, text="Code Input")

        self.input_text = scrolledtext.ScrolledText(
            self.input_frame, width=70, height=15
        )
        self.input_text.pack(fill=tk.BOTH, expand=True)

        self.btn_frame = tk.Frame(self.input_frame)
        self.btn_frame.pack(fill=tk.X)

        self.parse_btn = tk.Button(
            self.btn_frame, text="Parse & Analyze", command=self.parse_code
        )
        self.parse_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.flowchart_btn = tk.Button(
            self.btn_frame, text="Generate Flowchart", command=self.generate_flowchart
        )
        self.flowchart_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # —— Tab 2: Analysis Output —— 
        self.analysis_frame = tk.Frame(self.notebook)
        self.notebook.add(self.analysis_frame, text="Analysis")

        self.output_text = scrolledtext.ScrolledText(
            self.analysis_frame, width=70, height=25
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # —— Tab 3: Flowchart Display —— 
        self.flowchart_frame = tk.Frame(self.notebook)
        self.notebook.add(self.flowchart_frame, text="Flowchart")
        self.flowchart_canvas = None

        # Insert some sample code by default
        sample_code = """\
int main() {
    int x;
    cin >> x;
    if (x >= 10) {
        if ((x / 2) * 2 == x)
            cout << "A";
        else
            cout << "B";
    } else {
        cout << "C";
    }
    return 0;
}
"""
        self.input_text.insert(tk.END, sample_code)
        self.last_ast = None

    def parse_code(self):
        """Lex, parse, and run semantic analysis on the input code, then print results."""
        self.output_text.delete("1.0", tk.END)
        code = self.input_text.get("1.0", tk.END)
        try:
            # 1) Tokenize
            tokens = lexer(code)
            self.output_text.insert(tk.END, "Tokens:\n")
            self.output_text.insert(
                tk.END,
                " ".join(f"{t['type']}:{t['value']}" for t in tokens) + "\n\n"
            )

            # 2) Parse → AST
            parser = Parser(tokens)
            ast = parser.parse()
            self.last_ast = ast
            self.output_text.insert(tk.END, "AST:\n")
            self.output_text.insert(tk.END, repr(ast) + "\n")

            # 3) Semantic analysis
            analyzer = SemanticAnalyzer()
            analyzer.analyze(ast)
            if analyzer.errors:
                self.output_text.insert(tk.END, "Semantic Errors:\n")
                for err in analyzer.errors:
                    self.output_text.insert(tk.END, err + "\n")
            else:
                self.output_text.insert(tk.END, "No semantic errors detected.\n")

            # Switch to Analysis tab
            self.notebook.select(1)

        except Exception as e:
            self.output_text.insert(tk.END, f"Error: {e}\n")
            self.last_ast = None

    def generate_flowchart(self):
        """Generate a PNG flowchart from the last AST and display it."""
        if not self.last_ast:
            self.parse_code()
            if not self.last_ast:
                return

        try:
            flowchart_gen = FlowchartGenerator()
            dot = flowchart_gen.generate(self.last_ast)

            try:
                dot.render('flowchart', format='png', cleanup=True)
                self._display_flowchart('flowchart.png')
                self.notebook.select(2)
            except Exception as e:
                # If rendering fails, show raw DOT source in the Analysis tab
                self.output_text.insert(tk.END, "\nFlowchart DOT Source:\n")
                self.output_text.insert(tk.END, dot.source)
                self.output_text.insert(
                    tk.END,
                    "\n\nNote: Failed to render flowchart image. Error: "
                    + str(e)
                    + "\nMake sure Graphviz is installed: https://graphviz.org/download/"
                )
                self.notebook.select(1)

        except Exception as e:
            self.output_text.insert(tk.END, f"\nError generating flowchart: {e}\n")
            self.notebook.select(1)

    def _display_flowchart(self, filename):
        """Load the generated PNG and show it in a scrollable canvas."""
        if self.flowchart_canvas:
            self.flowchart_canvas.destroy()

        canvas_frame = tk.Frame(self.flowchart_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        h_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        v_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.flowchart_canvas = tk.Canvas(
            canvas_frame,
            xscrollcommand=h_scrollbar.set,
            yscrollcommand=v_scrollbar.set
        )
        self.flowchart_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        h_scrollbar.config(command=self.flowchart_canvas.xview)
        v_scrollbar.config(command=self.flowchart_canvas.yview)

        img = Image.open(filename)
        self.flowchart_img = ImageTk.PhotoImage(img)
        self.flowchart_canvas.create_image(0, 0, image=self.flowchart_img, anchor=tk.NW)
        self.flowchart_canvas.config(scrollregion=self.flowchart_canvas.bbox(tk.ALL))

if __name__ == "__main__":
    # Ensure the Graphviz Python package is installed at runtime
    try:
        import graphviz
    except ImportError:
        print("Graphviz Python package not found. Please install it (pip install graphviz).")
        print("Also install the Graphviz system binary (brew install graphviz, apt-get install graphviz, etc.).")

    root = tk.Tk()
    app = CodeToASTApp(root)
    root.mainloop()

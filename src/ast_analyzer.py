"""
AST Analyzer Module - CopilotAgent tarafından eklendi
Bu modül kod değişikliklerini AST seviyesinde analiz eder.
"""
import ast

def analyze_python_changes(old_code, new_code):
    """İki Python kodu arasındaki fonksiyon değişikliklerini tespit eder."""
    try:
        old_tree = ast.parse(old_code)
        new_tree = ast.parse(new_code)
        
        old_funcs = {node.name for node in ast.walk(old_tree) if isinstance(node, ast.FunctionDef)}
        new_funcs = {node.name for node in ast.walk(new_tree) if isinstance(node, ast.FunctionDef)}
        
        added = new_funcs - old_funcs
        removed = old_funcs - new_funcs
        
        return {
            "added_functions": list(added),
            "removed_functions": list(removed),
            "modified_functions": list(old_funcs & new_funcs)  # Basit tespit
        }
    except SyntaxError:
        return None

if __name__ == "__main__":
    # Test
    old = "def hello(): pass"
    new = "def hello(): pass\ndef world(): pass"
    print(analyze_python_changes(old, new))

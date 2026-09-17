from __future__ import annotations

import ast


def extract_chunks(file_path: str, relative_path: str) -> list[dict]:
    try:
        with open(file_path, 'r', encoding='utf-8') as file_handle:
            source_code = file_handle.read()
    except (OSError, UnicodeDecodeError):
        return []

    try:
        module = ast.parse(source_code)
    except SyntaxError:
        return []

    chunks: list[dict] = []

    for node in module.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            chunks.append(
                {
                    'name': node.name,
                    'qualified_name': node.name,
                    'source': ast.get_source_segment(source_code, node),
                    'docstring': ast.get_docstring(node),
                    'start_line': node.lineno,
                    'end_line': node.end_lineno,
                    'symbol_type': 'function',
                    'file_path': relative_path,
                }
            )
        elif isinstance(node, ast.ClassDef):
            chunks.append(
                {
                    'name': node.name,
                    'qualified_name': node.name,
                    'source': ast.get_source_segment(source_code, node),
                    'docstring': ast.get_docstring(node),
                    'start_line': node.lineno,
                    'end_line': node.end_lineno,
                    'symbol_type': 'class',
                    'file_path': relative_path,
                }
            )

            for class_node in node.body:
                if isinstance(class_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    chunks.append(
                        {
                            'name': class_node.name,
                            'qualified_name': f'{node.name}.{class_node.name}',
                            'source': ast.get_source_segment(source_code, class_node),
                            'docstring': ast.get_docstring(class_node),
                            'start_line': class_node.lineno,
                            'end_line': class_node.end_lineno,
                            'symbol_type': 'method',
                            'file_path': relative_path,
                        }
                    )

    return chunks

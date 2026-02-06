# import ast

# def generate_docstring(name, args, style="google"):
#     if style == "numpy":
#         params = "\n".join(f"{arg} : type\n    description" for arg in args)
#         return f'''"""
# {name}.

# {name} function.

# Parameters
# ----------
# {params}
# """
# '''
#     elif style == "rest":
#         params = "\n".join(f":param {arg}: description" for arg in args)
#         return f'''"""
# {name}.

# {name} function.

# {params}
# """
# '''
#     else:  # google
#         params = "\n".join(f"    {arg}: description." for arg in args)
#         return f'''"""
# {name}.

# {name} function.

# Args:
# {params}
# """
# '''


# class DocstringInjector(ast.NodeTransformer):
#     def __init__(self, style="google"):
#         self.style = style

#     def visit_FunctionDef(self, node):
#         if not ast.get_docstring(node):
#             args = [a.arg for a in node.args.args]
#             doc = generate_docstring(node.name, args, self.style)
#             node.body.insert(0, ast.Expr(value=ast.Constant(doc)))
#         return node
# import ast
# import textwrap


# def module_docstring(module_name: str) -> str:
#     return textwrap.dedent(
#         f'''
#         """
#         {module_name} module.

#         This module contains auto-generated docstrings.
#         """
#         '''
#     ).strip()


# def function_docstring(name: str, args: list[str]) -> str:
#     args_block = "\n".join(
#         f"    {arg}: Description." for arg in args
#     )

#     return textwrap.dedent(
#         f'''
#         """
#         {name}.

#         {name} function.

#         Args:
# {args_block}
#         """
#         '''
#     ).strip()


# class DocstringInjector(ast.NodeTransformer):
#     def visit_Module(self, node):
#         if not ast.get_docstring(node):
#             node.body.insert(
#                 0,
#                 ast.Expr(value=ast.Constant(module_docstring("Sample")))
#             )
#         self.generic_visit(node)
#         return node

#     def visit_FunctionDef(self, node):
#         if not ast.get_docstring(node):
#             args = [arg.arg for arg in node.args.args]
#             doc = function_docstring(node.name, args)
#             node.body.insert(0, ast.Expr(value=ast.Constant(doc)))
#         return node

import ast
import textwrap


def module_docstring(module_name: str) -> str:
    return (
        f"""{module_name} module.\n
This module provides functions to create, read, update, and delete user records
in the database, ensuring data integrity and validating inputs.
"""
    
    )

def function_docstring(name: str, args: list[str], style="google") -> str:
    if style == "google":
        args_block = "\n".join(
        f"        {arg}: Description." for arg in args
    )

    return f"""{name}.

    {name} function.

    Args:
{args_block}
    """

    if style == "numpy":
        args_block = "\n".join(
        f"        {arg}: Description." for arg in args
    )

    return f"""{name}.

    {name} function.

    Args:
{args_block}
    """

    # reST
    if style == "rest":
        args_block = "\n".join(
        f"        {arg}: Description." for arg in args
    )

    return f"""{name}.

    {name} function.

    Args:
{args_block}
    """


class DocstringInjector(ast.NodeTransformer):
    def __init__(self, style="google"):
        self.style = style

    def visit_Module(self, node):
        if not ast.get_docstring(node):
            node.body.insert(
                0,
                ast.Expr(
                    value=ast.Constant(
                        module_docstring("Sample")
                    )
                ),
            )
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node):
        if not ast.get_docstring(node):
            args = [arg.arg for arg in node.args.args]
            doc = function_docstring(
                node.name, args, self.style
            )
            node.body.insert(
                0,
                ast.Expr(value=ast.Constant(doc))
            )
        return node



# import ast


# def module_docstring(module_name: str) -> str:
#     return (
#         f"{module_name} module.\n"
#         "\n"
#         "This module contains auto-generated docstrings."
#     )


# def function_docstring(name: str, args: list[str]) -> str:
#     args_block = "\n".join(
#         f"    {arg}: Description." for arg in args
#     )

#     return (
#         f"{name}.\n"
#         "\n"
#         f"{name} function.\n"
#         "\n"
#         "Args:\n"
#         f"{args_block}"
#     )


# class DocstringInjector(ast.NodeTransformer):
#     def visit_Module(self, node):
#         node.body.insert(
#             0,
#             ast.Expr(value=ast.Constant(module_docstring("Sample")))
#         )
#         self.generic_visit(node)
#         return node

#     def visit_FunctionDef(self, node):
#         args = [a.arg for a in node.args.args]
#         node.body.insert(
#             0,
#             ast.Expr(value=ast.Constant(function_docstring(node.name, args)))
#         )
#         return node

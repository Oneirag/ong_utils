"""
General utils to set up a default configuration file or edit it
"""

import ast
from pathlib import Path

import warnings
warnings.filterwarnings("error", category=SyntaxWarning)


def extract_parameters(call_node) -> list:
    """Returns a list. config function has 1 parameter (the config item) and the second parameter, optional
    is the default value"""
    parameters = []
    if isinstance(call_node, ast.Call):
        # Only store parameters if the first parameter is a string
        if isinstance(call_node.args[0], ast.Constant):
            args = tuple([arg.value for arg in call_node.args if isinstance(arg, ast.Constant)])
            parameters.append(args)
    return parameters


class FindConfigCalls:

    function_names = ("config", "test_config")

    def find_config_calls(self, node, function_name: str):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                # print(node.func.id)
                if node.func.id == function_name:
                    if function_name not in self.__config_parameters:
                        self.__config_parameters[function_name] = set()
                    params = extract_parameters(node)
                    if params:
                        self.__config_parameters[function_name].update(params)
        for child_node in ast.iter_child_nodes(node):
            self.find_config_calls(child_node, function_name)

    def iter_files(self):
        for file_path in self.folder_path.rglob("*.py"):
            # Skip files in a virtual environment, by looking for files with "site-packages" and "lib" in the path
            file_path_parts_lower = list(p.lower() for p in file_path.relative_to(folder_path).parent.parts)
            if all(p in file_path_parts_lower for p in ("site-packages", "lib")):
                continue
            # Skip activate_this.py that appear in virtual environments,
            # look for that that ends with bin/activate_this.py
            if file_path.stem == "activate_this" and file_path.parent.name == "bin":
                continue
            print(file_path)
            yield file_path

    def __init__(self, folder_path: str | Path):
        self.__config_parameters = dict()
        self.folder_path = Path(folder_path)
        for function_name in self.function_names:
            for file_path in self.iter_files():
                with file_path.open() as file:
                    try:
                        tree = ast.parse(file.read())
                        self.find_config_calls(tree, function_name)
                    except SyntaxError:
                        print(f"SyntaxError: Unable to parse {file_path}")

    @property
    def config_parameters(self) -> dict:
        return self.__config_parameters


if __name__ == '__main__':
    # Example usage:
    folder_path = '/Users/oneirag/PycharmProjects/ong_esios'
    # folder_path = '/Users/oneirag/PycharmProjects/commodity_data'
    # folder_path = Path.cwd().parent.parent.parent
    print(folder_path)
    print(FindConfigCalls(folder_path).config_parameters)
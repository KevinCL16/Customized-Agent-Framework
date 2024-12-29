import ast
import astor
import random

class StealthBugInjector(ast.NodeTransformer):
    """
    Enhanced framework for injecting subtle and realistic bugs into Python code using AST.
    """

    def __init__(self, error_config):
        """
        :param error_config: {
            "exception_type": {  # ValueError, TypeError 等
                "enabled": bool,
                "targets": [{
                    "function": str,          # 目标函数名
                    "class_name": str,        # 目标类名
                    "line_number": int,       # 目标行号
                    "variable": str,          # 目标变量名
                    "condition": str,         # 注入条件
                    "error_params": dict      # 错误特定参数
                }]
            }
        }
        """
        self.error_config = error_config
        self.current_line = 0
        self.current_class = None
        self.current_function = None
        self.scope_variables = set()
        self.imported_modules = set()

    def visit_Import(self, node):
        """跟踪导入的模块"""
        for name in node.names:
            self.imported_modules.add(name.name)
        return self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """跟踪从特定模块导入的内容"""
        self.imported_modules.add(node.module)
        return self.generic_visit(node)

    def visit_Call(self, node):
        """函数调用错误注入"""
        self.current_line = getattr(node, 'lineno', 0)
        
        func_name = None
        obj_name = None
        
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
            if isinstance(node.func.value, ast.Name):
                obj_name = node.func.value.id

        context = {
            "function": func_name,
            "object": obj_name,
            "node": node
        }

        # ValueError: 参数值不合法
        if params := self.should_inject_error("ValueError", **context):
            if params.get("type") == "invalid_argument":
                # 修改函数参数为非法值
                arg_name = params.get("argument_name")
                invalid_value = params.get("invalid_value")
                for kw in node.keywords:
                    if kw.arg == arg_name:
                        kw.value = ast.Num(n=invalid_value)

        # TypeError: 参数类型错误
        if params := self.should_inject_error("TypeError", **context):
            if params.get("type") == "wrong_type":
                # 替换参数为错误类型
                if params.get("target") == "fit_data":
                    # 特别处理 fit 方法的数据参数
                    node.args = [ast.Str(s="wrong_type_value"), node.args[1]]
                else:
                    arg_index = params.get("argument_index", 0)
                    if len(node.args) > arg_index:
                        node.args[arg_index] = ast.Str(s="wrong_type_value")

        # AttributeError: 访问不存在的属性
        if params := self.should_inject_error("AttributeError", **context):
            if params.get("type") == "invalid_attribute":
                if isinstance(node.func, ast.Attribute):
                    node.func.attr = params.get("invalid_attr", "nonexistent_method")

        return self.generic_visit(node)

    def visit_Subscript(self, node):
        """下标访问错误注入"""
        if isinstance(node.value, ast.Name):
            # 处理直接变量访问，如 df['column']
            obj_name = node.value.id
        elif isinstance(node.value, ast.Attribute):
            # 处理属性访问，如 obj.attr['key']
            obj_name = node.value.value.id if isinstance(node.value.value, ast.Name) else None
        else:
            obj_name = None

        if isinstance(node.slice, ast.Index):
            if isinstance(node.slice.value, ast.Str):
                # 获取访问的键名
                key = node.slice.value.s
            else:
                key = None
        else:
            key = None

        context = {
            "object": obj_name,
            "attribute": key,
            "node": node
        }

        # KeyError: 处理DataFrame列访问
        if params := self.should_inject_error("KeyError", **context):
            if params.get("type") == "invalid_column":
                if isinstance(node.slice, ast.Index) and isinstance(node.slice.value, ast.Str):
                    node.slice.value = ast.Str(s=params.get("invalid_column"))
                    return node

        return self.generic_visit(node)

    def visit_BinOp(self, node):
        """二元运算错误注入"""
        self.current_line = getattr(node, 'lineno', 0)
        
        context = {"node": node}

        # ZeroDivisionError: 除零错误
        if params := self.should_inject_error("ZeroDivisionError", **context):
            if params.get("type") == "divide_by_zero":
                if isinstance(node.op, ast.Div):
                    node.right = ast.Num(n=0)

        return self.generic_visit(node)

    def visit_FunctionDef(self, node):
        """函数定义错误注入"""
        old_function = self.current_function
        self.current_function = node.name
        
        context = {
            "function": node.name,
            "node": node
        }

        # RecursionError: 无限递归
        if params := self.should_inject_error("RecursionError", **context):
            if params.get("type") == "infinite_recursion":
                # 创建一个递归调用
                recursive_call = ast.Return(
                    value=ast.Call(
                        func=ast.Name(id=node.name, ctx=ast.Load()),
                        args=node.args,
                        keywords=[]
                    )
                )
                node.body = [recursive_call]

        result = self.generic_visit(node)
        self.current_function = old_function
        return result

    def visit_ClassDef(self, node):
        """
        Track current class context
        """
        old_class = self.current_class
        self.current_class = node.name
        result = self.generic_visit(node)
        self.current_class = old_class
        return result

    def should_inject_error(self, error_type, **context):
        """
        检查是否应该在当前上下文注入错误
        """
        if error_type not in self.error_config:
            return False
            
        config = self.error_config[error_type]
        if not config.get("enabled", False):
            return False

        for target in config.get("targets", []):
            # 检查所有配置的键值是否匹配
            match = True
            for key, value in target.items():
                if key != "error_params":
                    if key not in context or context[key] != value:
                        match = False
                        break
            
            if match:
                return target.get("error_params", {})
            
        return False

    def visit_Attribute(self, node):
        """属性访问错误注入"""
        # 初始化默认的 context
        context = {
            "node": node
        }
        
        if isinstance(node.value, ast.Name):
            # 处理直接属性访问，如 obj.attr
            context.update({
                "object": node.value.id,
                "attribute": node.attr
            })
        elif isinstance(node.value, ast.Attribute):
            # 处理链式属性访问，如 obj.attr1.attr2
            if isinstance(node.value.value, ast.Name):
                context.update({
                    "object": node.value.attr,  # 使用前一个属性作为对象
                    "attribute": node.attr
                })
        elif isinstance(node.value, ast.Subscript):
            # 处理下标访问后的属性，如 obj['key'].attr
            if isinstance(node.value.value, ast.Name):
                context.update({
                    "object": node.attr,  # 使用当前属性作为对象名
                    "attribute": node.attr
                })
        
        # KeyError: 通过属性访问不存在的列
        if params := self.should_inject_error("KeyError", **context):
            if params.get("type") == "invalid_column":
                node.attr = params.get("invalid_column", "nonexistent_column")
                return node

        # AttributeError: 处理方法调用
        if params := self.should_inject_error("AttributeError", **context):
            if params.get("type") == "invalid_attribute":
                node.attr = params.get("invalid_attr", "nonexistent_method")
                return node

        return self.generic_visit(node)

# 基于Python异常层次的错误配置示例
error_config = {
    "ValueError": {
        "enabled": True,
        "targets": [{
            "function": "train_test_split",
            "error_params": {
                "type": "invalid_argument",
                "argument_name": "test_size",
                "invalid_value": -0.5
            }
        }]
    },
    "TypeError": {
        "enabled": True,
        "targets": [{
            "function": "fit",
            "object": "model",
            "error_params": {
                "type": "wrong_type",
                "target": "fit_data"
            }
        }]
    },
    "KeyError": {
        "enabled": True,
        "targets": [
            {
                "object": "df",
                "attribute": "Mar.2019",
                "error_params": {
                    "type": "invalid_column",
                    "invalid_column": "NonExistentMonth2019"
                }
            },
            {
                "object": "df",
                "attribute": "Mar.2020",
                "error_params": {
                    "type": "invalid_column",
                    "invalid_column": "NonExistentMonth2020"
                }
            }
        ]
    },
    "AttributeError": {
        "enabled": True,
        "targets": [
            {
                "object": "model",
                "error_params": {
                    "type": "invalid_attribute",
                    "invalid_attr": "invalid_method"
                }
            },
            {
                "object": "values",
                "attribute": "reshape",
                "error_params": {
                    "type": "invalid_attribute",
                    "invalid_attr": "invalid_reshape"
                }
            }
        ]
    }
}

# 使用示例
def inject_bugs(source_code, error_config):
    tree = ast.parse(source_code)
    injector = StealthBugInjector(error_config)
    modified_tree = injector.visit(tree)
    return astor.to_source(modified_tree)

# Example usage
source_code = """
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

# Load the data
df = pd.read_csv('unemployement_industry.csv')
print('Columns in the DataFrame:', df.columns)

# Prepare the data
X = df['Mar.2019'].values.reshape(-1, 1)
y = df['Mar.2020'].values.reshape(-1, 1)

# Check data
if X.size == 0 or y.size == 0:
    print('No data found for the specified columns. Please check the column names.')
    exit()

# Handle missing values
from sklearn.impute import SimpleImputer
imputer = SimpleImputer(strategy='mean')
X = imputer.fit_transform(X)
y = imputer.fit_transform(y)

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# Train the model
model = LinearRegression()
model.fit(X_train, y_train)

# Evaluate the model
y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
print(f"Mean Squared Error: {round(mse, 2)}")
"""

modified_code = inject_bugs(source_code, error_config)
print(modified_code)


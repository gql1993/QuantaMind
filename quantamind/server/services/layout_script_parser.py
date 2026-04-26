"""
Parse Qiskit Metal style ``layout_*.py`` scripts to extract component/route semantics.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class LayoutInstanceSpec:
    name: str
    class_name: str
    options: dict[str, Any] = field(default_factory=dict)
    variable_name: str = ""
    is_route: bool = False


class _Unknown:
    def __init__(self, label: str = "unknown") -> None:
        self.label = label

    def __repr__(self) -> str:
        return f"<Unknown:{self.label}>"


UNKNOWN = _Unknown()


def _is_unknown(value: Any) -> bool:
    return isinstance(value, _Unknown)


class _MiniInterpreter:
    """
    Tiny AST interpreter for a narrow subset used in the provided layout scripts.
    """

    def __init__(self) -> None:
        self.env: dict[str, Any] = {}
        self.instances: dict[str, LayoutInstanceSpec] = {}

    def run(self, node: ast.AST) -> None:
        for stmt in getattr(node, "body", []):
            self.exec_stmt(stmt)

    def exec_stmt(self, stmt: ast.stmt) -> None:
        if isinstance(stmt, ast.Assign):
            value = self.eval_expr(stmt.value)
            for target in stmt.targets:
                self.assign_target(target, value)
            self._capture_constructor_assign(stmt.targets, stmt.value)
            return

        if isinstance(stmt, ast.AugAssign):
            current = self.eval_expr(stmt.target)
            value = self.eval_expr(stmt.value)
            self.assign_target(stmt.target, self._apply_binop(current, stmt.op, value))
            return

        if isinstance(stmt, ast.Expr):
            self._capture_constructor_expr(stmt.value)
            self.eval_expr(stmt.value)
            return

        if isinstance(stmt, ast.For):
            iterable = self.eval_expr(stmt.iter)
            if _is_unknown(iterable):
                return
            for item in iterable:
                self.assign_target(stmt.target, item)
                for sub in stmt.body:
                    self.exec_stmt(sub)
            return

        if isinstance(stmt, ast.If):
            cond = self.eval_expr(stmt.test)
            if _is_unknown(cond):
                for sub in stmt.body:
                    self.exec_stmt(sub)
                for sub in stmt.orelse:
                    self.exec_stmt(sub)
            elif cond:
                for sub in stmt.body:
                    self.exec_stmt(sub)
            else:
                for sub in stmt.orelse:
                    self.exec_stmt(sub)
            return

        if isinstance(stmt, ast.FunctionDef):
            for sub in stmt.body:
                self.exec_stmt(sub)
            return

    def assign_target(self, target: ast.expr, value: Any) -> None:
        if isinstance(target, ast.Name):
            self.env[target.id] = value
            return
        if isinstance(target, ast.Subscript):
            owner = self.eval_expr(target.value)
            key = self.eval_expr(target.slice)
            if isinstance(owner, dict) and not _is_unknown(key):
                owner[key] = value

    def eval_expr(self, node: ast.AST | None) -> Any:
        if node is None:
            return None
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            return self.env.get(node.id, UNKNOWN)
        if isinstance(node, ast.List):
            return [self.eval_expr(e) for e in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(self.eval_expr(e) for e in node.elts)
        if isinstance(node, ast.Dict):
            return {
                self.eval_expr(k): self.eval_expr(v)
                for k, v in zip(node.keys, node.values)
            }
        if isinstance(node, ast.Attribute):
            base = self.eval_expr(node.value)
            if _is_unknown(base):
                return UNKNOWN
            if isinstance(base, dict):
                return base.get(node.attr, UNKNOWN)
            return getattr(base, node.attr, UNKNOWN)
        if isinstance(node, ast.Subscript):
            owner = self.eval_expr(node.value)
            key = self.eval_expr(node.slice)
            try:
                return owner[key]
            except Exception:
                return UNKNOWN
        if isinstance(node, ast.UnaryOp):
            value = self.eval_expr(node.operand)
            if _is_unknown(value):
                return UNKNOWN
            if isinstance(node.op, ast.USub):
                return -value
            if isinstance(node.op, ast.UAdd):
                return +value
            if isinstance(node.op, ast.Not):
                return not value
        if isinstance(node, ast.BinOp):
            left = self.eval_expr(node.left)
            right = self.eval_expr(node.right)
            return self._apply_binop(left, node.op, right)
        if isinstance(node, ast.Compare):
            left = self.eval_expr(node.left)
            if _is_unknown(left):
                return UNKNOWN
            result = True
            current = left
            for op, comp in zip(node.ops, node.comparators):
                right = self.eval_expr(comp)
                if _is_unknown(right):
                    return UNKNOWN
                if isinstance(op, ast.Eq):
                    ok = current == right
                elif isinstance(op, ast.NotEq):
                    ok = current != right
                elif isinstance(op, ast.Lt):
                    ok = current < right
                elif isinstance(op, ast.Gt):
                    ok = current > right
                elif isinstance(op, ast.LtE):
                    ok = current <= right
                elif isinstance(op, ast.GtE):
                    ok = current >= right
                else:
                    return UNKNOWN
                result = result and ok
                current = right
            return result
        if isinstance(node, ast.Call):
            return self._eval_call(node)
        if isinstance(node, ast.JoinedStr):
            parts: list[str] = []
            for value in node.values:
                item = self.eval_expr(value)
                if _is_unknown(item):
                    return UNKNOWN
                parts.append(str(item))
            return "".join(parts)
        if isinstance(node, ast.FormattedValue):
            return self.eval_expr(node.value)
        return UNKNOWN

    def _apply_binop(self, left: Any, op: ast.operator, right: Any) -> Any:
        if _is_unknown(left) or _is_unknown(right):
            return UNKNOWN
        try:
            if isinstance(op, ast.Add):
                return left + right
            if isinstance(op, ast.Sub):
                return left - right
            if isinstance(op, ast.Mult):
                return left * right
            if isinstance(op, ast.Div):
                return left / right
            if isinstance(op, ast.FloorDiv):
                return left // right
            if isinstance(op, ast.Mod):
                return left % right
            if isinstance(op, ast.Pow):
                return left**right
        except Exception:
            return UNKNOWN
        return UNKNOWN

    def _eval_call(self, node: ast.Call) -> Any:
        func_name = self._func_name(node.func)
        if func_name == "Dict":
            result: dict[str, Any] = {}
            for arg in node.args:
                value = self.eval_expr(arg)
                if isinstance(value, dict):
                    result.update(value)
            for kw in node.keywords:
                if kw.arg is not None:
                    result[kw.arg] = self.eval_expr(kw.value)
            return result
        if func_name == "OrderedDict":
            return {}
        if func_name == "range":
            args = [self.eval_expr(a) for a in node.args]
            if any(_is_unknown(a) for a in args):
                return UNKNOWN
            return list(range(*args))
        return UNKNOWN

    def _capture_constructor_assign(self, targets: list[ast.expr], value: ast.AST) -> None:
        if not isinstance(value, ast.Call):
            return
        spec = self._extract_instance_spec(value)
        if spec is None:
            return
        for target in targets:
            if isinstance(target, ast.Name):
                spec.variable_name = target.id
                break
        self.instances[spec.name] = spec

    def _capture_constructor_expr(self, value: ast.AST) -> None:
        if not isinstance(value, ast.Call):
            return
        spec = self._extract_instance_spec(value)
        if spec is not None:
            self.instances[spec.name] = spec

    def _extract_instance_spec(self, call: ast.Call) -> LayoutInstanceSpec | None:
        class_name = self._func_name(call.func)
        if not class_name or class_name in {"DesignPlanar", "MetalGUI"}:
            return None
        if len(call.args) < 2:
            return None
        design_arg = self.eval_expr(call.args[0])
        name_arg = self.eval_expr(call.args[1])
        if design_arg is not UNKNOWN and design_arg != UNKNOWN:
            # Constructor may still be relevant even if we do not know design object.
            pass
        if _is_unknown(name_arg) or not isinstance(name_arg, str):
            return None
        options: dict[str, Any] = {}
        for kw in call.keywords:
            if kw.arg == "options":
                raw = self.eval_expr(kw.value)
                if isinstance(raw, dict):
                    options = raw
        return LayoutInstanceSpec(
            name=name_arg,
            class_name=class_name,
            options=options,
            is_route=class_name.startswith("Route"),
        )

    def _func_name(self, func: ast.AST) -> str:
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            return func.attr
        return ""


def parse_layout_script(path: Path | str) -> dict[str, LayoutInstanceSpec]:
    p = Path(path)
    source = p.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(p))
    interpreter = _MiniInterpreter()
    interpreter.run(tree)
    return interpreter.instances


def find_companion_layout(json_path: Path | str) -> Path | None:
    p = Path(json_path)
    candidates = [
        p.with_name(f"layout_{p.stem}.py"),
        p.parent / f"layout_{p.stem}.py",
        p.parent.parent / f"layout_{p.stem}.py",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    for parent in [p.parent, p.parent.parent]:
        if parent.exists():
            matches = sorted(parent.glob("layout_*.py"))
            if matches:
                return matches[0]
    return None


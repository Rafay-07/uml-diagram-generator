"""Parse Python source with the ast module and build a UML class model.

The model captures what a UML class diagram shows: classes, attributes,
methods, inheritance (generalization), and composition/association between
classes. Rendering to PlantUML and Mermaid text lives in the same file so the
tool has no dependencies beyond the standard library.
"""
import ast
import sys
from dataclasses import dataclass, field


@dataclass
class ClassInfo:
    name: str
    bases: list = field(default_factory=list)      # parent class names
    attrs: dict = field(default_factory=dict)      # attribute name -> type text
    methods: list = field(default_factory=list)    # (name, [params], return text)
    abstract: bool = False


def _text(node):
    """Return source text for an annotation node, or '' when missing."""
    return ast.unparse(node) if node is not None else ""


def _visibility(name):
    """UML visibility marker from Python naming conventions."""
    if name.startswith("__") and not name.endswith("__"):
        return "-"      # name-mangled -> private
    if name.startswith("_"):
        return "#"      # single underscore -> protected
    return "+"


def parse_source(source):
    """Return {class name: ClassInfo} for every top-level class in source."""
    classes = {}
    for node in ast.parse(source).body:
        if not isinstance(node, ast.ClassDef):
            continue
        info = ClassInfo(node.name, bases=[_text(b) for b in node.bases])
        for item in node.body:
            # Class-level annotated fields, e.g. `price: float = 0`
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                info.attrs[item.target.id] = _text(item.annotation)
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                params = [a.arg for a in item.args.args if a.arg != "self"]
                info.methods.append((item.name, params, _text(item.returns)))
                if any(_text(d).endswith("abstractmethod") for d in item.decorator_list):
                    info.abstract = True
                if item.name == "__init__":
                    _collect_init_attrs(item, info)
        if "ABC" in info.bases:
            info.abstract = True
        classes[node.name] = info
    return classes


def _collect_init_attrs(init, info):
    """Find `self.x = ...` and `self.x: T = ...` inside __init__."""
    # Map parameter names to their annotations so `self.x = x` keeps the type.
    ann = {a.arg: _text(a.annotation) for a in init.args.args}
    for stmt in ast.walk(init):
        if isinstance(stmt, ast.AnnAssign) and _is_self_attr(stmt.target):
            info.attrs[stmt.target.attr] = _text(stmt.annotation)
        elif isinstance(stmt, ast.Assign):
            for t in stmt.targets:
                if _is_self_attr(t):
                    guess = ann.get(getattr(stmt.value, "id", ""), "")
                    info.attrs.setdefault(t.attr, guess)


def _is_self_attr(node):
    return (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
            and node.value.id == "self")


def relationships(classes):
    """Return (inherits, has) edges between classes found in the model.

    inherits: (child, parent) from base-class lists.
    has: (owner, part) when an attribute's type text names another known class.
    """
    inherits, has = [], []
    for c in classes.values():
        for b in c.bases:
            if b in classes:
                inherits.append((c.name, b))
        for attr_type in c.attrs.values():
            for other in classes:
                if other != c.name and other in attr_type.replace("[", " ").replace("]", " ").replace(",", " ").split():
                    if (c.name, other) not in has:
                        has.append((c.name, other))
    return inherits, has


def to_plantuml(classes):
    inherits, has = relationships(classes)
    out = ["@startuml"]
    for c in classes.values():
        kind = "abstract class" if c.abstract else "class"
        out.append(f"{kind} {c.name} {{")
        for n, t in c.attrs.items():
            out.append(f"  {_visibility(n)}{n}" + (f": {t}" if t else ""))
        for n, params, ret in c.methods:
            if n == "__init__":
                continue
            out.append(f"  {_visibility(n)}{n}({', '.join(params)})" + (f": {ret}" if ret else ""))
        out.append("}")
    out += [f"{p} <|-- {ch}" for ch, p in inherits]
    out += [f"{o} *-- {p}" for o, p in has]
    out.append("@enduml")
    return "\n".join(out)


def to_mermaid(classes):
    inherits, has = relationships(classes)
    out = ["classDiagram"]
    for c in classes.values():
        out.append(f"  class {c.name} {{")
        for n, t in c.attrs.items():
            out.append(f"    {_visibility(n)}{n}" + (f" {t}" if t else ""))
        for n, params, ret in c.methods:
            if n != "__init__":
                out.append(f"    {_visibility(n)}{n}({', '.join(params)})" + (f" {ret}" if ret else ""))
        out.append("  }")
    out += [f"  {p} <|-- {ch}" for ch, p in inherits]
    out += [f"  {o} *-- {p}" for o, p in has]
    return "\n".join(out)


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print("usage: python classdiagram.py FILE.py [plantuml|mermaid]")
        return 2
    classes = parse_source(open(argv[0]).read())
    fmt = argv[1] if len(argv) > 1 else "plantuml"
    print(to_mermaid(classes) if fmt == "mermaid" else to_plantuml(classes))
    return 0


if __name__ == "__main__":
    sys.exit(main())

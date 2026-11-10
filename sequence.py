"""Record method calls at runtime and render a UML sequence diagram.

Usage: wrap code in `with Recorder() as r:` and call `r.to_plantuml()` after.
Only methods on instances of classes listed in `track` are recorded, so the
diagram stays readable. Caller -> callee arrows come from the call stack.
"""
import sys


class Recorder:
    def __init__(self, track):
        self.track = tuple(track)       # classes whose methods we record
        self.events = []                # (caller, callee, method)
        self._stack = ["Client"]        # who is currently executing

    def _name(self, frame):
        obj = frame.f_locals.get("self")
        return type(obj).__name__ if isinstance(obj, self.track) else None

    def _trace(self, frame, event, arg):
        if event == "call":
            callee = self._name(frame)
            if callee and not frame.f_code.co_name.startswith("__"):
                self.events.append((self._stack[-1], callee, frame.f_code.co_name))
                self._stack.append(callee)
                return self._trace      # keep tracing to catch the return
        elif event == "return":
            if self._name(frame) and len(self._stack) > 1:
                self._stack.pop()
        return None

    def __enter__(self):
        sys.setprofile(lambda f, e, a: self._trace(f, e, a) and None)
        return self

    def __exit__(self, *exc):
        sys.setprofile(None)

    def participants(self):
        seen = []
        for a, b, _ in self.events:
            for p in (a, b):
                if p not in seen:
                    seen.append(p)
        return seen

    def to_plantuml(self):
        out = ["@startuml"] + [f"participant {p}" for p in self.participants()]
        out += [f"{a} -> {b}: {m}()" for a, b, m in self.events]
        out.append("@enduml")
        return "\n".join(out)

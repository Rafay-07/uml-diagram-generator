# uml-diagram-generator

Generates UML diagrams from Python code, with no dependencies beyond the standard library.

- `classdiagram.py` parses source with `ast` and outputs a UML **class diagram** (PlantUML or Mermaid): attributes, methods, visibility (`+ # -`), abstract classes, inheritance and composition.
- `sequence.py` records real method calls at runtime and outputs a UML **sequence diagram** (PlantUML).
- `example_shop.py` is a small order/payment model used as input and in the tests.

## Usage

```
python classdiagram.py example_shop.py            # PlantUML
python classdiagram.py example_shop.py mermaid    # Mermaid
```

```python
from sequence import Recorder
with Recorder([Order, CardPayment]) as r:
    order.checkout()
print(r.to_plantuml())
```

Paste the output into any PlantUML or Mermaid renderer.

## Tests

```
pip install -r requirements.txt
pytest -q
```

7 tests cover class parsing, inheritance, composition edges, visibility, both output formats and sequence recording. GitHub Actions runs them on every push.

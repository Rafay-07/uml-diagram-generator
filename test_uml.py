import classdiagram as cd
from sequence import Recorder
import example_shop as shop

SRC = open("example_shop.py").read()


def test_finds_classes_and_inheritance():
    classes = cd.parse_source(SRC)
    assert set(classes) == {"Payment", "CardPayment", "Item", "Order"}
    inherits, _ = cd.relationships(classes)
    assert ("CardPayment", "Payment") in inherits


def test_abstract_detected():
    assert cd.parse_source(SRC)["Payment"].abstract


def test_composition_edges():
    _, has = cd.relationships(cd.parse_source(SRC))
    assert ("Order", "Payment") in has and ("Order", "Item") in has


def test_visibility_markers():
    assert cd._visibility("_paid") == "#" and cd._visibility("__x") == "-" and cd._visibility("x") == "+"


def test_plantuml_output():
    uml = cd.to_plantuml(cd.parse_source(SRC))
    assert uml.startswith("@startuml") and "Payment <|-- CardPayment" in uml
    assert "abstract class Payment" in uml and "#_paid: bool" in uml


def test_mermaid_output():
    assert "Payment <|-- CardPayment" in cd.to_mermaid(cd.parse_source(SRC))


def test_sequence_recording():
    order = shop.Order(shop.CardPayment("4242"))
    order.add(shop.Item("pen", 2.0))
    with Recorder([shop.Order, shop.CardPayment]) as r:
        order.checkout()
    assert ("Client", "Order", "checkout") in r.events
    assert ("Order", "CardPayment", "charge") in r.events
    assert "Order -> CardPayment: charge()" in r.to_plantuml()

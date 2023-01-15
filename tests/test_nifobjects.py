import pytest

from nifigator import NifContext, OffsetBasedString
from rdflib.term import URIRef


def test_nif_context():
    """API Tests"""
    context = NifContext(
        uri="https://mangosaurus.eu/rdf-data/doc_1",
        URIScheme=OffsetBasedString,
        isString="The cat sat on the mat. Felix was his name.",
    )
    assert type(context) == NifContext
    assert context.isString == "The cat sat on the mat. Felix was his name."
    assert context.uri == URIRef("https://mangosaurus.eu/rdf-data/doc_1")
    assert context.URIScheme == OffsetBasedString

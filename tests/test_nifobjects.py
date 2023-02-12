import pytest

import nifigator

from rdflib.term import URIRef
import stanza

def test_nif_context():
    """API Tests"""
    context = nifigator.NifContext(
        uri="https://mangosaurus.eu/rdf-data/doc_1",
        URIScheme=nifigator.OffsetBasedString,
        isString="The cat sat on the mat. Felix was his name.",
    )
    assert type(context) == nifigator.NifContext
    assert context.isString == "The cat sat on the mat. Felix was his name."
    assert context.uri == URIRef("https://mangosaurus.eu/rdf-data/doc_1")
    assert context.URIScheme == nifigator.OffsetBasedString

def test_nif_collection():

    context = nifigator.NifContext(
        uri="https://mangosaurus.eu/rdf-data/doc_1",
        URIScheme=nifigator.OffsetBasedString,
        isString="The cat sat on the mat. Felix was his name.",
    )
    collection = nifigator.NifContextCollection(uri="https://mangosaurus.eu/rdf-data")
    collection.add_context(context)
    assert type(collection) == nifigator.NifContextCollection
    assert collection.conformsTo == URIRef('http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core/2.1')
    assert collection.contexts == [context]

def test_load_from_dict():

    context = nifigator.NifContext(
        uri="https://mangosaurus.eu/rdf-data/doc_1",
        URIScheme=nifigator.OffsetBasedString,
        isString="The cat sat on the mat. Felix was his name.",
    )

    nlp = stanza.Pipeline("en", verbose=False)
    stanza_dict = nlp(context.isString).to_dict()
    context.load_from_dict(stanza_dict)
    assert context.sentences[0].anchorOf == "The cat sat on the mat."
    assert context.sentences[1].anchorOf == "Felix was his name."

    word = context.sentences[1].words[0]
    assert word.uri == URIRef("https://mangosaurus.eu/rdf-data/doc_1#offset_24_29")
    assert str(word.referenceContext) == str(context)
    assert word.beginIndex == 24
    assert word.endIndex == 29
    assert word.anchorOf == "Felix"
    assert word.lemma == "Felix"
    assert word.morphofeats == [URIRef('http://purl.org/olia/olia.owl#Singular')]
    assert word.dependency[0].uri == URIRef('https://mangosaurus.eu/rdf-data/doc_1#offset_38_42')
    assert word.dependencyRelationType == 'nsubj'

def test_nif_graph():

    context = nifigator.NifContext(
        uri="https://mangosaurus.eu/rdf-data/doc_1",
        URIScheme=nifigator.OffsetBasedString,
        isString="The cat sat on the mat. Felix was his name.",
    )
    collection = nifigator.NifContextCollection(uri="https://mangosaurus.eu/rdf-data")
    collection.add_context(context)

    nlp = stanza.Pipeline("en", verbose=False)
    stanza_dict = nlp(context.isString).to_dict()
    context.load_from_dict(stanza_dict)

    g = nifigator.NifGraph(collection=collection)
    collection = g.collection

    context = collection.contexts[0]
    assert type(context) == nifigator.NifContext
    assert context.isString == "The cat sat on the mat. Felix was his name."
    assert context.uri == URIRef("https://mangosaurus.eu/rdf-data/doc_1")
    assert context.URIScheme == URIRef('http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#OffsetBasedString')
    assert context.sentences[0].anchorOf == "The cat sat on the mat."
    assert context.sentences[1].anchorOf == "Felix was his name."
    
    word = context.sentences[1].words[0]
    assert word.uri == URIRef("https://mangosaurus.eu/rdf-data/doc_1#offset_24_29")
    assert str(word.referenceContext) == str(context)
    assert word.beginIndex == 24
    assert word.endIndex == 29
    assert word.anchorOf == "Felix"
    assert word.lemma == "Felix"
    assert word.morphofeats == [URIRef('http://purl.org/olia/olia.owl#Singular')]
    assert word.dependency[0].uri == URIRef('https://mangosaurus.eu/rdf-data/doc_1#offset_38_42')
    assert word.dependencyRelationType == 'nsubj'

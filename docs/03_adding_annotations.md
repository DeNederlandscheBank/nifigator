---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.14.4
  kernelspec:
    display_name: Python 3 (ipykernel)
    language: python
    name: python3
---

# Adding annotations

You can add annotations to the Nif data in the following way.

## Entity occurrences

First we create a collection with one context.

```python
# For the NLP data we create a NifContext and a NifContextCollection
from nifigator import NifContext, NifContextCollection, OffsetBasedString

# Create context with two sentences
context = NifContext(
  uri="https://mangosaurus.eu/rdf-data/doc_1",
  URIScheme=OffsetBasedString,
  isString="The cat sat on the mat. Felix was his name."
)

# Create a collection and add the context above
collection = NifContextCollection(uri="https://mangosaurus.eu/rdf-data")
collection.add_context(context)
```

An annotation refers to a part of the string of the NifContext called a Phrase.

Here is how to create a new annotations for the named entity 'Felix'.

```python
# a NifPhrase can be an EntityOccurrence or a TermOccurrence
from nifigator import NifPhrase, EntityOccurrence

# Create the EntityOccurrence
entity = NifPhrase(
    uri="https://mangosaurus.eu/rdf-data/doc_1",
    URIScheme=OffsetBasedString,
    referenceContext=context,
    beginIndex=24,
    endIndex=29,
    taIdentRef="https://mangosaurus.eu/rdf-data/entities/Felix",
    taClassRef="https://mangosaurus.eu/rdf-data/classes/cat",
    taConfidence=1.0,
    PhraseType=EntityOccurrence,
)

# set the phrases as a list with one element
context.set_Phrases([entity])
```

For referencing the taIdentRef, taClassRef and taConfidence from the Internationalization Tag Set (itsrdf) are used.

The phrases can then be accessed with

```python
# the string representation of the phrases in the context then looks like this
print(context.phrases)
```

```console
[(nif:EntityOccurrence) uri = <https://mangosaurus.eu/rdf-data/doc_1#offset_24_29>
  referenceContext : https://mangosaurus.eu/rdf-data/doc_1
  beginIndex : 24
  endIndex : 29
  anchorOf : "Felix"
  taIdentRef : https://mangosaurus.eu/rdf-data/entities/Felix
  taClassRef : https://mangosaurus.eu/rdf-data/classes/cat
  taConfidence : 1.0
]
```

We can then create a graph and convert back to a collection.

```python
from nifigator import NifGraph

g = NifGraph(collection=collection)
```

The phrases can be accessed with

```python
g.collection.contexts[0].phrases
```

```console
[(nif:TermOccurrence) uri = <https://mangosaurus.eu/rdf-data/doc_1#offset_24_29>
   referenceContext : https://mangosaurus.eu/rdf-data/doc_1
   beginIndex : 24
   endIndex : 29
   anchorOf : "Felix"]
   taIdentRef : https://mangosaurus.eu/rdf-data/entities/Felix
   taClassRef : https://mangosaurus.eu/rdf-data/classes/cat
   taConfidence : 1.0   
```

Checking whether the serialized data is the samen as the NifGraph:

```python
from rdflib import Graph
g1 = Graph().parse(data=g.serialize(format="ttl"))
print(g1.isomorphic(g))
```

In some situations you might want to store the annotations in a different graph. You can do that in the following way:

```python
g_annotations = NifGraph()

for phrase in collection.contexts[0].phrases:
    for triple in phrase.triples():
        g_annotations.add(triple)
```

Then the graph contains all data about the phrases and nothing else.

```python
from rdflib import RDF

# retrieve and print all triples where the predicatie is rdf:type
for triple in g_annotations.triples([None, RDF.type, None]):
    print(triple)
```

```console
(rdflib.term.URIRef('https://mangosaurus.eu/rdf-data/doc_1#offset_24_29'), rdflib.term.URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'), rdflib.term.URIRef('http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#Phrase'))
(rdflib.term.URIRef('https://mangosaurus.eu/rdf-data/doc_1#offset_24_29'), rdflib.term.URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'), rdflib.term.URIRef('http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#EntityOccurrence'))
(rdflib.term.URIRef('https://mangosaurus.eu/rdf-data/doc_1#offset_24_29'), rdflib.term.URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'), rdflib.term.URIRef('http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#OffsetBasedString'))
(rdflib.term.URIRef('https://mangosaurus.eu/rdf-data/doc_1#offset_24_29'), rdflib.term.URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'), rdflib.term.URIRef('http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#String'))
```

```python

```

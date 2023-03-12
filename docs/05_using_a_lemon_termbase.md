---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.14.5
  kernelspec:
    display_name: Python 3 (ipykernel)
    language: python
    name: python3
---


# Using a Ontolex-Lemon termbase


## Open a graph with NIF data

```python
from nifigator import NifGraph, generate_uuid

original_uri = "https://www.dnb.nl/media/4kobi4vf/dnb-annual-report-2021.pdf"
uri = "https://dnb.nl/rdf-data/"+generate_uuid(uri=original_uri)

# create a NifGraph from this collection and serialize it 
g = NifGraph().parse(
    "..//data//"+generate_uuid(uri=original_uri)+".ttl", format="turtle"
)
```

Open a Ontolex-Lemon termbase and add to graph

```python
TAXO_NAME = "EIOPA_SolvencyII_XBRL_Taxonomy_2.6.0_PWD_with_External_Files"

termbase = Graph().parse(
    "P://projects//rdf-data//termbases//"+TAXO_NAME+".ttl", format="turtle"
)
```

```python
# bind namespaces
from rdflib import Namespace, namespace
termbase.bind("tbx", Namespace("http://tbx2rdf.lider-project.eu/tbx#"))
termbase.bind("ontolex", Namespace("http://www.w3.org/ns/lemon/ontolex#"))
termbase.bind("lexinfo", Namespace("http://www.lexinfo.net/ontology/3.0/lexinfo#"))
termbase.bind("decomp", Namespace("http://www.w3.org/ns/lemon/decomp#"))
termbase.bind("skos", namespace.SKOS)
```

```python
g += termbase
```

```python
# all terms that contain the canonical word risk
q = """
SELECT ?wr
WHERE {
    ?e decomp:constituent ?c1 .
    ?e ontolex:canonicalForm ?cf .
    ?cf ontolex:writtenRep ?wr .
    ?c1 decomp:correspondsTo ?l .
    ?l ontolex:canonicalForm ?can .
    ?can ontolex:writtenRep "mitigation"@en .
}
"""
# execute the query
results = list(g.query(q))

print(len(results))
# print the results
for result in results[0:5]:
    print(result[0].value)
```

## Running SPARQL queries

```python
# 
q = """
SELECT ?r ?word ?concept
WHERE {
    ?word nif:lemma ?t .
    ?entry ontolex:canonicalForm [ rdfs:label ?t ; ontolex:writtenRep ?r] .
    ?entry ontolex:sense [ ontolex:reference ?concept ] .
    ?concept skos:altLabel "S.26.01.01.01,C0030"@en .
}
"""
# execute the query
results = list(g.query(q))

print(len(results))
# print the results
for result in results[0:5]:
    print((result[0].value, result[1:]))
```

```python
# 
q = """
SELECT ?s ?w
WHERE {
    ?o rdf:type ontolex:Form .
    ?o ontolex:writtenRep "S.26.01.01.01,C0030"@en .
    ?s rdf:type ontolex:LexicalEntry .
    ?s ?p ?o .
    ?s ontolex:canonicalForm [rdf:type ontolex:Form ; ontolex:writtenRep ?w ] .
}
"""
# execute the query
results = list(g.query(q))

print(len(results))
# print the results
for result in results[0:5]:
    print(result)
```

```python

```

```python
# including the page that the word contains
q = """
SELECT ?r ?word ?page ?concept
WHERE {
    ?word nif:lemma ?t .
    ?word nif:beginIndex ?word_beginIndex .
    ?word nif:endIndex ?word_endIndex .
    ?entry ontolex:canonicalForm [ rdfs:label ?t ; ontolex:writtenRep ?r] .
    ?entry ontolex:sense [ ontolex:reference ?concept ] .
    ?concept skos:altLabel "S.26.01.01.01,C0030"@en .
    ?page rdf:type nif:Page .
    ?page nif:beginIndex ?page_beginIndex .
    FILTER( ?page_beginIndex <= ?word_beginIndex ) .
    ?page nif:endIndex ?page_endIndex .
    FILTER( ?page_endIndex >= ?word_endIndex ) .
}
"""
# execute the query
results = g.query(q)

print(len(results))
for result in results:
    print((result[0].value, result[1:]))
```

```python
# all terms that contain the canonical word risk
q = """
SELECT ?wr
WHERE {
    ?e decomp:constituent ?c1 .
    ?e ontolex:canonicalForm ?cf .
    ?cf ontolex:writtenRep ?wr .
    ?c1 decomp:correspondsTo ?l .
    ?l ontolex:canonicalForm ?can .
    ?can ontolex:writtenRep "reinsurance"@en .
}
"""
# execute the query
results = g.query(q)

print(len(results))
# print the results
for result in results:
    print(result)
```

```python
# all terms that contain the canonical word risk
q = """
SELECT distinct ?label
WHERE {
    ?e a ontolex:Word .
    ?e lexinfo:partOfSpeech <http://purl.org/olia/olia.owl#ProperNoun> .
    ?e ontolex:sense ?sense .
    ?sense ontolex:reference ?ref .
    ?ref skos:prefLabel ?label .
    FILTER ( lang(?label) = "en" )
}
"""
# execute the query
results = g.query(q)

print(len(results))
# print the results
for result in results:
    print(result)
```

## Creating a lexicon from NIF data

```python
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib.graph import DATASET_DEFAULT_GRAPH_ID as default
import pandas as pd

import ruleminer
import logging, sys
logging.basicConfig(stream=sys.stdout,
                    format='%(asctime)s %(message)s',
                    level=logging.INFO)

# Connect to triplestore.
store = SPARQLUpdateStore()
query_endpoint = 'http://localhost:3030/nifigator/sparql'
update_endpoint = 'http://localhost:3030/nifigator/update'
store.open((query_endpoint, update_endpoint))

from nifigator import NifGraph

# Open a graph in the open store and set identifier to default graph ID.
graph = NifGraph(store=store, identifier=default)
```

```python
q = """
SELECT ?anchor ?lemma ?pos
WHERE {
    SERVICE <http://localhost:3030/nifigator/sparql> 
    {
        ?w rdf:type nif:Word .
        ?w nif:anchorOf ?anchor .
        OPTIONAL {?w nif:lemma ?lemma . } .
        OPTIONAL {?w nif:pos ?pos . } .
    }
}
"""
# execute the query
results = list(graph.query(q))
```

```python
def noNumber(s: str=""):
    return not s.replace('.', '', 1).replace(',', '', 1).isdigit()

from termate import Lexicon, LexicalEntry, Form
from rdflib.term import URIRef
from iribaker import to_iri

lexicon = Lexicon(uri=URIRef("https://mangosaurus.eu/rdf-data/lexicon/en"))
lexicon.set_language("en")

for anchorOf, lemma, pos in results:

    if lemma is not None and noNumber(lemma):
        
        entry_uri = to_iri(str(lexicon.uri)+"/"+lemma)
        
        entry = LexicalEntry(
            uri=entry_uri,
            language=lexicon.language
        )
        # set canonicalForm (this is the lemma)
        entry.set_canonicalForm(
            Form(
                uri=URIRef(entry_uri),
                formVariant="canonicalForm",
                writtenReps=[lemma])
            )
        # set otherForm if the anchorOf is not the same as the lemma
        if anchorOf != lemma:
            entry.set_otherForms([
                Form(
                    uri=URIRef(entry_uri),
                    formVariant="otherForm",
                    writtenReps=[anchorOf]
                )])
        if pos is not None:
            entry.set_partOfSpeechs([pos])
        lexicon.add_entry(entry)
```

```python

```

```python
from rdflib import Graph, Namespace, namespace

lexicon_graph = Graph()
lexicon_graph.bind("tbx", Namespace("http://tbx2rdf.lider-project.eu/tbx#"))
lexicon_graph.bind("ontolex", Namespace("http://www.w3.org/ns/lemon/ontolex#"))
lexicon_graph.bind("lexinfo", Namespace("http://www.lexinfo.net/ontology/3.0/lexinfo#"))
lexicon_graph.bind("decomp", Namespace("http://www.w3.org/ns/lemon/decomp#"))
lexicon_graph.bind("skos", namespace.SKOS)
for triple in lexicon.triples():
    lexicon_graph.add(triple)
```

```python
len(lexicon_graph)
```

```python
import os
file = os.path.join("P:\\projects\\rdf-data\\termbases", "dnb.ttl")
lexicon_graph.serialize(file, format="turtle")
```

```python

```

```python

```

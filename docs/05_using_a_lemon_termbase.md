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


# Using a Ontolex-Lemon termbase


## 

Open a graph

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

g += NifGraph().parse(
    "P://projects//rdf-data//termbases//"+TAXO_NAME+".ttl", format="turtle"
)
```

```python
from rdflib import Namespace, namespace
g.bind("tbx", Namespace("http://tbx2rdf.lider-project.eu/tbx#"))
g.bind("ontolex", Namespace("http://www.w3.org/ns/lemon/ontolex#"))
g.bind("lexinfo", Namespace("http://www.lexinfo.net/ontology/3.0/lexinfo#"))
g.bind("decomp", Namespace("http://www.w3.org/ns/lemon/decomp#"))
g.bind("skos", namespace.SKOS)
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
results = g.query(q)

print(len(results))
# print the results
for result in results:
    print((result[0].value, result[1:]))
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

```

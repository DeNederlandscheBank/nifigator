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

# Running SPARQL queries

To analyze the complete Nif data set SPARQL queries are useful.

## Examples

First we create a collection with one context (created earlier).

```python
from nifigator import NifGraph

g = NifGraph.parse("..//data//nif-5282967702ae37d486ad338b9771ca8f.hext", format="hext")
```

### The total number of words in the collection

```python
  # number of words
  q = """
  SELECT (count(?s) as ?num) WHERE {
      ?s rdf:type nif:Word . 
  }
  """
  results = g.query(q)
  for result in results:
      print(result[0].value)
```

This returns

```console
(rdflib.term.URIRef('https://dnb.nl/rdf-data/nif-5282967702ae37d486ad338b9771ca8f'), 68139)
```

### The frequency of words per context

```python
  # frequency of words per context
  q = """
  SELECT ?p (count(?w) as ?num) WHERE {
      ?s rdf:type nif:Word . 
      ?s nif:anchorOf ?w .
      ?s nif:referenceContext ?c .
      ?c dcterms:provenance ?p .
  }
  GROUP BY ?p 
  ORDER BY DESC(?num)
  """
  results = g2.query(q)
  for result in results:
      print((result[0].value, result[1].value))
```

This returns

```console
('the', 3713)
('.', 2280)
(',', 2077)
('of', 1877)
('and', 1736)
('to', 1420)
('in', 1411)
('-', 904)
(')', 892)
('(', 865)
```

### Adjective-noun combinations in the context

```python
# ADJ-NOUN combinations
q = """
SELECT ?a1 ?a WHERE {
    ?s rdf:type nif:Word . 
    ?s nif:pos olia:CommonNoun .
    ?s nif:anchorOf ?a .
    ?s nif:previousWord [ 
        nif:pos olia:Adjective ;
        nif:anchorOf ?a1
    ]
    }
LIMIT 10
"""
results = g.query(q)
for result in results:
```

This returns

```console
('further', 'details')
('more', 'opportunities')
('detailed', 'substantiation')
('functional', 'management')
('entire', 'result')
('European', 'limit')
('significant', 'institutions')
('financial', 'crime')
('Current', 'policies')
('net', 'result')
```

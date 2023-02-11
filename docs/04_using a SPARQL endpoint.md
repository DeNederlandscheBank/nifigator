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


# Using a SPARQL endpoint and running SPARQL queries


## Connecting to a (local) SPARQL endpoint


You can use an existing SPARQL endpoint in the following way.

```python
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib.graph import DATASET_DEFAULT_GRAPH_ID as default

# Connect to triplestore.
store = SPARQLUpdateStore()
query_endpoint = 'http://localhost:3030/nifigator/sparql'
update_endpoint = 'http://localhost:3030/nifigator/update'
store.open((query_endpoint, update_endpoint))
```

Then open a NifGraph in the same way as a rdflib.Graph

```python
from nifigator import NifGraph

# Open a graph in the open store and set identifier to default graph ID.
graph = NifGraph(store=store, identifier=default)
```

We can then check the number of triples in the store

```python
# count the number of triples in the store
print("Number of triples: "+str(len(graph)))
```

```console
Number of triples: 1081392
``` 


To check the contexts in the graph you can use the catalog property. This property return a Pandas DataFrame with the context uris (in the index) with collection uri and the metadata (from DC and DCTERMS) available.

```python
# get the catalog with all contexts within the graph
catalog = graph.catalog
catalog
```

```console

```

```python
from nifigator import NIF

# get the context uri and the collection uri of the first row in the catalog
context_uri = catalog.index[0]
collection_uri = catalog.loc[context_uri, NIF.ContextCollection]

# extract the collection with one context from the graph
collection = graph.extract_collection(collection_uri=collection_uri, 
                                      context_uris=[context_uri])
```

```python
# show the string representation of the collection
collection
```

```console
(nif:ContextCollection) uri = https://dnb.nl/rdf-data/
  conformsTo : http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core/2.1
  hasContext : https://dnb.nl/rdf-data/nif-5282967702ae37d486ad338b9771ca8f
```

## Running SPARQL queries


### The total number of words in the collection


```python
# define the query for the total number of words
q = """
SELECT (count(?s) as ?num) WHERE {
    SERVICE <http://localhost:3030/nifigator/sparql> {
          ?s rdf:type nif:Word . 
    }
}
"""

# execute the query
results = graph.query(q)

# print the results
for result in results:
    print(result[0].value)
```

This returns

```console
68070
```


### The frequency of words per context

```python
# query for the frequency of words per context
q = """
SELECT ?w (count(?w) as ?num) WHERE {
    SERVICE <http://localhost:3030/nifigator/sparql> {
        ?s rdf:type nif:Word . 
        ?s nif:anchorOf ?w .
        ?s nif:referenceContext ?c .
    }
}
GROUP BY ?w
ORDER BY DESC(?num)
LIMIT 10
"""

# execute the query
results = graph.query(q)

# print the results
for result in results:
    print((result[0].value, result[1].value))
```

This returns

```console
('the', 3713)
('.', 2281)
(',', 2077)
('of', 1877)
('and', 1736)
('to', 1420)
('in', 1411)
(')', 892)
('-', 874)
('(', 865)
```


### Adjective-noun combinations in the context

```python
# query for the first 10 ADJ-NOUN combinations
q = """
SELECT ?a1 ?a WHERE {
    SERVICE <http://localhost:3030/nifigator/sparql> {
        ?s rdf:type nif:Word . 
        ?s nif:pos olia:CommonNoun .
        ?s nif:anchorOf ?a .
        ?s nif:previousWord [ 
            nif:pos olia:Adjective ;
            nif:anchorOf ?a1
        ]
    }
}
LIMIT 10
"""

# execute the query
results = graph.query(q)

# print the results
for result in results:
    print((result[0].value, result[1].value))
```

This returns

```console
('Annual', 'Report')
('supervisory', 'authorities')
('financial', 'crime')
('illegal', 'use')
('non-commercial', 'purposes')
('wide', 'availability')
('terrorist', 'financing')
('regular', 'supervision')
('pre-pandemic', 'levels')
('new', 'market')
```

```python
# All two-word phrases ending with the lemma 'insurer' and starting with an adjective
q = """
SELECT distinct ?c ?a WHERE {
    SERVICE <http://localhost:3030/nifigator/sparql> {
        ?s rdf:type nif:Word . 
        ?s nif:lemma "insurer"^^xsd:string .
        ?s nif:anchorOf ?a .
        ?s nif:previousWord [ 
            nif:pos olia:Adjective ;
            nif:anchorOf ?c ;
        ]
    }
}
"""

# execute the query
results = graph.query(q)

# print the results
for result in results:
    print((result[0].value, result[1].value))
```

This gives:

```console
('eligible', 'insurers')
('Non-life', 'insurers')
('Dutch', 'insurers')
('relevant', 'insurers')
('non-life', 'insurers')
('individual', 'insurers')
```

```python

```

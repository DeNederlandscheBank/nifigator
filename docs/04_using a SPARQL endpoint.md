---
jupyter:
  jupytext:
    formats: ipynb,md
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

# Using a SPARQL endpoint


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
collection
```

```console
(nif:ContextCollection) uri = https://dnb.nl/rdf-data/
  conformsTo : http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core/2.1
  hasContext : https://dnb.nl/rdf-data/nif-5282967702ae37d486ad338b9771ca8f
```

```python

```

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

# Creating a nif2vec graph

```python
import os, sys, logging
logging.basicConfig(stream=sys.stdout, 
                    format='%(asctime)s %(message)s',
                    level=logging.INFO)
```

```python
# The NifContext contains a context which uses a URI scheme
from nifigator import NifGraph, NifContext, OffsetBasedString, NifContextCollection

# Make a context by passing uri, uri scheme and string
context = NifContext(
  uri="https://mangosaurus.eu/rdf-data/doc_1",
  URIScheme=OffsetBasedString,
  isString="Leo Tolstoy wrote the book War and Peace. Jane Austen wrote the book Pride and Prejudice."
)
# Make a collection by passing a uri
collection = NifContextCollection(uri="https://mangosaurus.eu/rdf-data")
collection.add_context(context)
nif_graph = NifGraph(collection=collection)
```

```python
from nifigator import NifVecGraph

params = {
    "min_phrase_count": 1, 
    "min_context_count": 1,
    "min_phrasecontext_count": 1
}

# the nifvec graph can be created from a NifGraph and a set of optional parameters
nifvec_graph = NifVecGraph(
    nif_graph=nif_graph, 
    params=params
)
```

```python
phrase = "War and Peace"
for line in nifvec_graph.phrase_contexts(phrase):
    print(line)
```

```console
(('book', 'SENTEND'), 1)
(('the+book', 'SENTEND'), 1)
(('wrote+the+book', 'SENTEND'), 1)
(('Tolstoy+wrote+the+book', 'SENTEND'), 1)
```

```python
phrase = "Pride and Prejudice"
for line in nifvec_graph.most_similar(phrase):
    print(line)
```

```console
('Pride and Prejudice', 0.0)
('War and Peace', 0.25)
```

```python
# from nifigator import NifVecGraph, NifGraph

# lang = 'en'

# params = {
#     "min_phrase_count": 2, 
#     "min_context_count": 2,
#     "min_phrasecontext_count": 2,
#     "max_phrase_length": 4,
#     "max_context_length": 2,
# }
# for j in range(1, 11):
    
#     # the nifvec graph can be created from a NifGraph and a set of optional parameters
#     file = os.path.join("D:\\data\\dbpedia\\extracts", lang, "dbpedia_"+"{:04d}".format(j)+"_lang="+lang+".ttl")
#     nifvec_graph = NifVecGraph(
#         nif_graph=NifGraph(file=file),
#         params=params
#     )
#     logging.info(".. Serializing graph")
#     nifvec_graph.serialize(destination=os.path.join("D:\\data\\dbpedia\\nifvec\\", "nifvec_"+"{:04d}".format(j)+"_lang="+lang+".xml"), format="xml")
```

# querying the nif2vec graph

```python
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib.graph import DATASET_DEFAULT_GRAPH_ID as default
from nifigator import NifVecGraph

# Connect to triplestore
store = SPARQLUpdateStore()
query_endpoint = 'http://localhost:3030/nif2vec_en/sparql'
update_endpoint = 'http://localhost:3030/nif2vec_en/update'
store.open((query_endpoint, update_endpoint))

# create NifVecGraph with this store
g = NifVecGraph(store=store, identifier=default)
```

```python

```

```python
# most frequent contexts of the word "has"

g.phrase_contexts("has", topn=10)
```

```python
# top phrase similarities of the word "has"

g.most_similar("has", topn=10)
```

```python
# top phrase similarities of the word "King"

g.most_similar("King", topn=15)
```

```python
# simple masks

context = ("King", "of England")
for r in g.context_words(context):
    print(r)
```

```python

```

```python

```

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

## Querying the nif2vec graph


These are results of a nif2vec graph created with 15.000 DBpedia pages.

```python
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib.graph import DATASET_DEFAULT_GRAPH_ID as default
from nifigator import NifVecGraph

# Connect to triplestore
store = SPARQLUpdateStore()
query_endpoint = 'http://localhost:3030/nif2vec_en/sparql'
update_endpoint = 'http://localhost:3030/nif2vec_en/update'
store.open((query_endpoint, update_endpoint))

# Create NifVecGraph with this store
g = NifVecGraph(store=store, identifier=default)
```

### Most frequent contexts

```python
# most frequent contexts of the word "has"
g.phrase_contexts("has", topn=10)
```

This results in

```console
[(('it', 'been'), 1429),
 (('It', 'been'), 1353),
 (('SENTSTART+It', 'been'), 1234),
 (('and', 'been'), 579),
 (('which', 'been'), 556),
 (('there', 'been'), 516),
 (('also', 'a'), 509),
 (('and', 'a'), 479),
 (('that', 'been'), 451),
 (('which', 'a'), 375)]
```

This means that the corpus contains 1429 occurrences of 'it has been', i.e. occurrences where the word 'has' occurred in the context ('it', 'been').

SENTSTART and SENTEND are tokens to indicate the start and end of a sentence.


### Top phrase similarities

```python
# top phrase similarities of the word "has"
g.most_similar("has", topn=10, topcontexts=15)
```

This results in

```console
[('had', 0.0),
 ('has', 0.0),
 ('may have', 0.2666666666666667),
 ('would have', 0.2666666666666667),
 ('have', 0.33333333333333337),
 ('has also', 0.4666666666666667),
 ('has never', 0.4666666666666667),
 ('has not', 0.4666666666666667),
 ('must have', 0.4666666666666667),
 ('also has', 0.5333333333333333)]
```

```python
# top phrase similarities of the word "King"
g.most_similar("King", topn=10, topcontexts=15)
```

This results in

```console
[('King', 0.0),
 ('Emperor', 0.4666666666666667),
 ('Prince', 0.4666666666666667),
 ('President', 0.5333333333333333),
 ('Queen', 0.5333333333333333),
 ('State', 0.5333333333333333),
 ('king', 0.5333333333333333),
 ('Chancellor', 0.6),
 ('Church', 0.6),
 ('City', 0.6)]
```


### Simple 'masks'

```python
# simple 'masks'
context = ("King", "of England")
for r in g.context_words(context, topn=10):
    print(r)
```

```console
('Henry VIII', 11)
('Edward I', 10)
('Edward III', 6)
('Charles II', 5)
('Edward IV', 5)
('Henry III', 5)
('Henry VII', 5)
('James I', 5)
('John', 5)
('Richard I', 4)
```

```python

```

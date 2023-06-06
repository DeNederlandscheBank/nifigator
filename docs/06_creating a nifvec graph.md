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

# Creating nifvec graph

```python
import os, sys, logging
logging.basicConfig(stream=sys.stdout, 
                    format='%(asctime)s %(message)s',
                    level=logging.WARNING)
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

# the nifvec graph can be creaated from a NifGraph and a set of optional parameters
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

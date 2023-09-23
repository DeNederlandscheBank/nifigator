---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.14.6
  kernelspec:
    display_name: Python 3 (ipykernel)
    language: python
    name: python3
---

# Creating NifVector graphs

```python
import os, sys, logging
logging.basicConfig(stream=sys.stdout, 
                    format='%(asctime)s %(message)s',
                    level=logging.DEBUG)
```

First connect to a graph database.

```python
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib import ConjunctiveGraph, Graph, URIRef
from nifigator import NifVectorGraph

# Connect to triplestore
store = SPARQLUpdateStore()
query_endpoint = 'http://localhost:3030/dbpedia_en/sparql'
update_endpoint = 'http://localhost:3030/dbpedia_en/update'
store.open((query_endpoint, update_endpoint))

# Graph identifier
identifier = URIRef("https://mangosaurus.eu/dbpedia")
```

```python
lang = 'en'

stop_words = [
    
#     'i', 'me', 'my', 'myself',
#     'we', 'our', 'ours', 'ourselves',
#     'you', 'your', 'yours', 'yourself', 'yourselves',
#     'he', 'him', 'his', 'himself',
#     'she', 'her', 'hers', 'herself',
#     'it', 'its', 'itself',
#     'they', 'them', 'their', 'theirs', 'themselves',
    
#     'what', 'which', 'who', 'whom',
#     'this', 'that', 'these', 'those',
    
    'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of',
    'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during',
    'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off',
    'over', 'under', 'further'
]

# set the parameters to create the NifVector graph
params = {
    "min_phrase_count": 2,
    "min_context_count": 2,
    "min_phrasecontext_count": 2,
    "max_phrase_length": 5,
    "max_context_length": 5,
    "words_filter": {
        "data": stop_words,
        "name": "nifvec.stopwords"
    }
}
```


## Add some DBpedia data to graph



```python
from nifigator import NifGraph, NifSentence

nif_graph = NifGraph(
    identifier=identifier,
)

context_uris = list()

for j in range(1, 11):
    
    file = os.path.join("E:\\data\\dbpedia\\extracts\\", lang, "dbpedia_"+"{:04d}".format(j)+"_lang="+lang+".ttl")

    temp = NifGraph(
        identifier=identifier,
        file=file,
    )
    for context in temp.contexts:
        
        context.extract_sentences(forced_sentence_split_characters=["*"])                            

        for r in context.triples([NifSentence]):
            temp.add(r)

        context_uris.append(context.uri)

    nif_graph += temp
```


```python
from nifigator import NifVectorGraph

chunk_size = 2000

for i in range(0, 5):

    nifvec_graph = NifVectorGraph(
        store=store,
        identifier=identifier,
        params=params,
        context_uris=context_uris[i*chunk_size:(i+1)*chunk_size],
        nif_graph=nif_graph
    )
```

```python
nifvec_graph += nif_graph
```

```python
nifvec_graph.compact()
```

```python
!curl -XPOST http://localhost:3030/$/compact/dbpedia_en
```

```python
g = NifGraph(
    store=store,
    identifier=identifier,
)
g += nif_graph
```

```python

```

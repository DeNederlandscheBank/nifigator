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


In a NifVector graph vector embeddings are defined from words and phrases, and the original contexts in which they occur (all in Nif). No dimensionality reduction is applied and this enables to obtain some understanding about why certain word are found to be close to each other.

```python
import os, sys, logging
logging.basicConfig(stream=sys.stdout, 
                    format='%(asctime)s %(message)s',
                    level=logging.INFO)
```

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
```

```python
from nifigator import NifGraph

g = NifGraph(
    store=store,
    identifier=identifier,
)
```

## Add some DBpedia data to graph

```python
from nifigator import NifVectorGraph, NifGraph, URIRef, RDF, NIF, NifContext, tokenize_text, NifSentence

nif_graph = NifGraph(
    identifier=identifier,
)

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
            
            
    nif_graph += temp

g += nif_graph

```

## Derive NifVector graph from DBpedia

```python
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

params = {
    "min_phrase_count": 2, 
    "min_context_count": 2,
    "min_phrasecontext_count": 2,
    "max_phrase_length": 5,
    "max_left_length": 3,
    "max_right_length": 3,
    "min_left_length": 1,
    "min_right_length": 1,
    "min_window_relation_count": 2,
    "words_filter": {
        "data": stop_words,
        "name": "nifvec.stopwords"
    }
}
```

```python
from nifigator import RDF, NIF

# extract uris of all contexts
context_uris = list(nif_graph.subjects(RDF.type, NIF.Context))
```

```python
from nifigator import NifVectorGraph

# add the NifVectorGraph derived from the document strings to the Nif graph
for i in range(0, 10):

    nifvec_graph = NifVectorGraph(
        identifier=identifier,
        params=params,
        context_uris=context_uris[i*1000:(i+1)*1000],
        nif_graph=nif_graph
    )
    
    g += nifvec_graph
    
    del nifvec_graph
```

```python

```

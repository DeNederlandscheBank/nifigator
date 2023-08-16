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

## Add some DBpedia data to graph

```python
from nifigator import NifVectorGraph, NifGraph, URIRef, RDF, NIF, NifContext, tokenize_text, NifSentence

nif_graph = NifGraph(
    identifier=identifier,
)
```

```python
for j in range(1, 2):
    
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

```

## Derive NifVector graph from DBpedia

```python
from nifigator import RDF, NIF

# extract uris of all contexts
context_uris = sorted(list(nif_graph.subjects(RDF.type, NIF.Context)))
```

```python
stop_words = [
    'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of',
    'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during',
    'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off',
    'over', 'under', 'further'
]
```

```python
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
        "name": "nltk.stopwords"
    }
}
```

```python
from nifigator import NifVectorGraph

# add the NifVectorGraph derived from the document strings to the Nif graph
for i in range(0, 1):

    nifvec_graph = NifVectorGraph(
        identifier=identifier,
        params=params,
        context_uris=context_uris[0:100],
        nif_graph=nif_graph,
    )
```

```python
len(nifvec_graph)
```

```python
nifvec_graph.serialize(destination="test.ttl", format='turtle')
```

```python
# 2023-08-16 08:38:59,007 .. Extracting text from graph
# 2023-08-16 08:38:59,837 .. Creating windows dict
# 2023-08-16 08:40:31,589 .. Creating phrase and context dicts
# 2023-08-16 08:40:33,326 .... deleting 8997075 windows from 9047654
# 2023-08-16 08:40:34,828 .... deleting 0 phrases from 6428
# 2023-08-16 08:40:34,834 .... deleting 0 contexts from 46827
# 2023-08-16 08:40:34,834 .. Collecting triples
# 2023-08-16 08:40:41,839 .. Finished initialization

```

```python

```

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

# NifVector graphs (English)


In a NifVector graph vector embeddings are defined from words and phrases, and the original contexts in which they occur (all in Nif). No dimensionality reduction whatsoever is applied. This enables to obtain some understanding about why certain word are found to be close to each other.

```python
import os, sys, logging
logging.basicConfig(stream=sys.stdout, 
                    format='%(asctime)s %(message)s',
                    level=logging.INFO)
```

```python
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from nifigator import NifVectorGraph, URIRef

# Connect to triplestore
store = SPARQLUpdateStore()
query_endpoint = 'http://localhost:3030/dbpedia_en/sparql'
update_endpoint = 'http://localhost:3030/dbpedia_en/update'
store.open((query_endpoint, update_endpoint))

# Graph identifier
identifier = URIRef("https://mangosaurus.eu/dbpedia")
```

```python
from nifigator import NifVectorGraph

nif_graph = NifVectorGraph(
    store=store,
    identifier=identifier
)
```

### Extracting contexts in sentences


```python
context_1 = nif_graph.get(URIRef("http://dbpedia.org/resource/Aldebaran?dbpv=2020-07&nif=context"))
context_2 = nif_graph.get(URIRef("http://dbpedia.org/resource/Antares?dbpv=2020-07&nif=context"))
```

```python
print(context_1)
```

```python
print(context_2)
```

```python
from nifigator import tokenize_text, generate_phrase_context, NIFVEC, NifVector

context_1_sentences = {}
for sentence in context_1.sentences:
    sentences = [[t['text'] for t in s] for s in tokenize_text(sentence.anchorOf, forced_sentence_split_characters=["*"])]
    s = set([i[1] for i in generate_phrase_context(sentences=sentences)])
    if len(s) > 1:
        context_1_sentences[sentence.anchorOf] = s
    
context_2_sentences = {}
for sentence in context_2.sentences:
    sentences = [[t['text'] for t in s] for s in tokenize_text(sentence.anchorOf, forced_sentence_split_characters=["*"])]
    s = set([i[1] for i in generate_phrase_context(sentences=sentences)])
    if len(s) > 1:
        context_2_sentences[sentence.anchorOf] = s    

```

```python
total = dict()

for sent_1 in context_1_sentences.keys():
    contexts_1 = context_1_sentences[sent_1]
    results = {}
    for key in list(context_2_sentences.keys()):
        contexts_2 = context_2_sentences[key]
        jaccard_distance = 1 - len(contexts_1 & contexts_2) / (len(contexts_1 | contexts_2))
        results[key] = jaccard_distance
    sent_2 = min(results, key=results.get)
    total[(sent_1, sent_2)] = results[sent_2]

```

```python
dict(sorted(total.items(), key=lambda item: item[1]))
```

```python
def weighted_jaccard_similarity(phrase_1: str=None):
    """ 
    """
    contexts_1 = nif_graph.phrase_contexts(phrase_1)
    
    phrases = set([
        item2 
        for item in contexts_1
        for item2 in nif_graph.context_phrases(item).keys()
    ])    
    r = dict()
    for phrase in phrases:
        contexts_2 = nif_graph.phrase_contexts(phrase)
        contexts = set(contexts_1.keys()) & set(contexts_2.keys())
        r_min = 0
        r_max = 0
        for context in contexts:
            r_min += min(contexts_1.get(context), contexts_2.get(context))
            r_max += max(contexts_1.get(context), contexts_2.get(context))
        if r_max != 0:
            r[phrase] = 1 - r_min / r_max
        else:
            r[phrase] = 1
    return dict(sorted(r.items(), key=lambda item: item[1]))
```

```python
weighted_jaccard_similarity("although")
```

```python
def tversky_index(phrase_1: str=None, alfa: float=None, beta: float=None):
    """ 
    """
    c_1 = nif_graph.phrase_contexts(phrase_1, topn=15).keys()
    phrases = set([
        item2 
        for item in c_1
        for item2 in nif_graph.context_phrases(item, topn=15).keys()
    ])
    print("Number of candidates: "+str(len(phrases)))
    r = dict()
    for phrase in phrases:
        c_2 = nif_graph.phrase_contexts(phrase, topn=15).keys()
        r[phrase] = (len(c_1 & c_2) / len(c_1 | c_2)) # + alfa * len(c_1 - c_2 ) + beta * len(c_2 - c_1)))
        
    return dict(sorted(r.items(), key=lambda item: item[1], reverse=True))

```

```python
tversky_index("author", 0, 0)
```

```python

```

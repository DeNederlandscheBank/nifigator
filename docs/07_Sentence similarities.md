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

# Sentence similarities and searching




```python
import os, sys, logging
logging.basicConfig(stream=sys.stdout, 
                    format='%(asctime)s %(message)s',
                    level=logging.INFO)
```

```python
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore

# Create store
store = SPARQLUpdateStore()
query_endpoint = 'http://localhost:3030/dbpedia_en/sparql'
update_endpoint = 'http://localhost:3030/dbpedia_en/update'
store.open((query_endpoint, update_endpoint))
```

```python
from nifigator import NifVectorGraph, URIRef

# Create NifVector graph to store
nif_graph = NifVectorGraph(
    store=store,
    identifier=URIRef("https://mangosaurus.eu/dbpedia")
)
```

### Extracting contexts in sentences


```python
context_1 = nif_graph.get(
    URIRef("http://dbpedia.org/resource/Aldebaran?dbpv=2020-07&nif=context")
)
context_2 = nif_graph.get(
    URIRef("http://dbpedia.org/resource/Antares?dbpv=2020-07&nif=context")
)
```

```python
print(context_1)
```

```python
print(context_2)
```

```python

```

```python

```

```python
from nifigator import STOPWORDS, generate_windows

# setup a dictionary with phrases and contexts to speed up
def setup_phrase_contexts_dict(documents: list=None, phrase_contexts_dict: dict={}, topn: int=15):

    params = {"words_filter": {'data': {phrase: True for phrase in STOPWORDS}}}

    for s in documents:

        phrases = generate_windows(
            documents={"id": s}, 
            params=params
        ).keys()

        for phrase in phrases:
            phrase_contexts = phrase_contexts_dict.get(phrase, None)
            if phrase_contexts is None:
                phrase_contexts = nif_graph.phrase_contexts(phrase, topn=topn)
                phrase_contexts_dict[phrase] = phrase_contexts
    
    return phrase_contexts_dict
```

```python
phrase_contexts_dict = setup_phrase_contexts_dict([context_1.isString, context_2.isString], {})
```

```python
from nifigator import generate_windows, STOPWORDS
from collections import Counter

def extract_contexts(s: str=None):
    
    params = {"words_filter": {'data': {phrase: True for phrase in STOPWORDS}}}

    phrases = generate_windows(
        documents={"id": s}, 
        params=params
    ).keys()
    
    c = Counter()
    for phrase in phrases:
        if phrase_contexts_dict.get(phrase, None) is None:
            print(phrase)
        c += phrase_contexts_dict.get(phrase, None)
            
    return c
```

```python
from nifigator import tokenize_text, generate_phrase_context, NIFVEC

context_sentences = {}
for sentence in context_1.sentences+context_2.sentences:
    context_sentences[sentence.anchorOf] = extract_contexts(sentence.anchorOf)
```

### Find similar sentences

```python
def jaccard_distance(c1: set=None, c2: set=None):
    if len(c1 | c2 ) > 0:
        return 1 - len(c1 & c2)/(len(c1 | c2))
    else:
        return 1
```

```python
from itertools import combinations
        
similarities = dict()

for sent_1, sent_2 in combinations(context_sentences.keys(), 2):
    
    c1 = context_sentences[sent_1].keys()
    c2 = context_sentences[sent_2].keys()

    similarities[(sent_1, sent_2)] = jaccard_distance(c1, c2)

similarities = sorted(similarities.items(), key=lambda item: item[1])
```

```python
similarities[0:10]
```

# Searching

```python
def tversky_index(c1: set=None, c2: set=None, alfa: float=0, beta: float=0):
    denom = len(c1 & c2)+alfa*len(c1 - c2)+beta*len(c2 - c1)
    if denom != 0:
        return len(c1 & c2) / denom
    else:
        return 0

```

```python
question = "the brightest star in the constellation of Taurus"
# question = "the sun in the constellation of Taurus"
# question = "When is Antares visible to the naked eye?"
# question = "What is the Chinese name of Aldebaran"
# question = "How do the Māori people call Antares"
# question = "What did astronomer William Herschel discover on Aldebaran?"
# question = "What stars are visible to the naked eye?"
# question = "bass guitar of which guitar family?"
phrase_contexts_dict = setup_phrase_contexts_dict([question], phrase_contexts_dict)

question_contexts = extract_contexts(question)
c1 = question_contexts.keys()

similarities = {}
for sent in context_sentences.keys():

    c2 = context_sentences[sent].keys()
    
    tversky_distance = 1 - tversky_index(c1, c2, 1, 0)

    a = list()
    for key in c1:
        context_1_item = question_contexts.get(key, 0)
        context_2_item = context_sentences[sent].get(key, 0)
        a.append([key, context_1_item, context_2_item])

    similarities[sent] = ((tversky_distance, a))
```

```python
for item in list(dict(sorted(similarities.items(), key=lambda item: item[1][0])).items())[0:10]:
    print(item[0])
    print((item[1][0]))
#     for item2 in item[1][1]:
#         print(item2)
    print("--")
```

```python

```

```python

```

```python

```

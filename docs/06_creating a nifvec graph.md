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

```python
from rdflib import URIRef

# set language
lang = 'nl'

# Graph identifier
identifier = URIRef("https://mangosaurus.eu/dbpedia")

# Database location
database_url = 'http://localhost:3030/dbpedia_'+lang
```

First connect to a graph database.

```python
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore

# Connect to triplestore
store = SPARQLUpdateStore(
    query_endpoint = database_url+'/sparql',
    update_endpoint = database_url+'/update'
)
```

```python
stop_words_en = [
    
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
    'over', 'under', 'further',
    'per'
]

stop_words_nl = [
    'een', 'de', 'het', 'en', 'maar', 'als', 'of', 'omdat', 'van',
    'te', 'in', 'op', 'aan', 'met', 'voor', 'er', 'om', 'dan', 'of',
    'door', 'over', 'bij', 'ook', 'tot', 'uit', 'naar', 'want', 'nog',
    'toch', 'al', 'dus', 'onder', 'tegen', 'na', 'reeds'
]

# set the parameters to create the NifVector graph
params = {
    "min_phrase_count": 5,
    "min_context_count": 5,
    "min_phrasecontext_count": 1,
    "max_phrase_length": 5,
    "max_context_length": 5,
    "words_filter": {
        "data": stop_words_en if lang=="en" else stop_words_nl,
        "name": "nifvec.stopwords"
    },
    "regex_filter": "^[0-9]*[a-zA-Z,;:]*$"
}
```


## Add some DBpedia data to graph



```python
from nifigator import NifGraph, NifVectorGraph, NifSentence

file_size = 50

for i in range(0, 1):
    
    # read dbpedia files and tokenize
    nif_graph = NifGraph(
        identifier=identifier,
    )
    context_uris = list()
    for j in range(i*file_size+1, (i+1)*file_size+1):
        file = os.path.join("E:\\data\\dbpedia\\extracts\\", lang, "dbpedia_"+"{:04d}".format(j)+"_lang="+lang+".ttl")
        temp = NifGraph(
            identifier=identifier,
            file=file,
        )
        for context in temp.contexts:
            if context.isString is not None:
                context.extract_sentences(forced_sentence_split_characters=["*"])
                for r in context.triples([NifSentence]):
                    temp.add(r)
            context_uris.append(context.uri)
        nif_graph += temp

    # create nifvec and store in graph database
    nifvec_graph = NifVectorGraph(
        store=store,
        identifier=identifier,
        params=params,
        context_uris=context_uris,
        nif_graph=nif_graph
    )
    
    nifvec_graph += nif_graph
```


```python
nifvec_graph.compact()
```

```python
!curl -XPOST http://localhost:3030/$/compact/dbpedia_nl
```

```python

```

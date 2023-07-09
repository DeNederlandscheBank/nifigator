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

## Creating NifVector graphs

```python
from nltk.corpus import stopwords
stop_words = list(stopwords.words('english'))+[word[0].upper()+word[1:] for word in stopwords.words('english')]

from nifigator import NifVectorGraph, NifGraph, tokenizer

lang = 'en'

params = {
    "min_phrase_count": 2, 
    "min_context_count": 2,
    "min_phrasecontext_count": 2,
    "max_phrase_length": 3,
    "max_left_length": 2,
    "max_right_length": 2,
    "min_left_length": 1,
    "min_right_length": 1,
#     "words_filter": {"name": "NLTK_stopwords", 
#                      "data": stop_words}
}
for j in range(1, 26):
    
    # the nifvector graph can be created from a NifGraph and a set of optional parameters
    file = os.path.join("E:\\data\\dbpedia\\extracts", lang, "dbpedia_"+"{:04d}".format(j)+"_lang="+lang+".ttl")
    
    nif_graph = NifGraph(file=file)
    collection = nif_graph.collection
    documents = [context.isString for context in collection.contexts]
    vec_graph = NifVectorGraph(
        documents=documents,
        params=params
    )
    logging.info(".. Serializing graph")
    vec_graph.serialize(destination=os.path.join("E:\\data\\dbpedia\\nifvec\\", "nifvec_test2_"+"{:04d}".format(j)+"_lang="+lang+".xml"), format="xml")
```

```python

```

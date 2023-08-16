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

# Introduction to NifVector graphs


In a NifVector graph vector embeddings are defined from words and phrases, and the original contexts in which they occur (all in Nif). No dimensionality reduction whatsoever is applied. This enables to obtain some understanding about why certain word are found to be close to each other.

```python
import os, sys, logging
logging.basicConfig(stream=sys.stdout, 
                    format='%(asctime)s %(message)s',
                    level=logging.INFO)
```

## Simple NifVector graph example to introduce the idea

Let's setup a nif graph with a context with two sentences.

```python
# The NifContext contains a context which uses a URI scheme
from nifigator import NifGraph, NifContext, OffsetBasedString, NifContextCollection

# Make a context by passing uri, uri scheme and string
context = NifContext(
  uri="https://mangosaurus.eu/rdf-data/doc_1",
  URIScheme=OffsetBasedString,
  isString="""Leo Tolstoy wrote the book War and Peace. 
              Jane Austen wrote the book Pride and Prejudice."""
)
context.extract_sentences()
# Make a collection by passing a uri
collection = NifContextCollection(uri="https://mangosaurus.eu/rdf-data")
collection.add_context(context)
nif_graph = NifGraph(collection=collection)
```

Then we create a NifVectorGraph from this data.

```python
from nifigator import NifVectorGraph

# set up the params of the NifVector graph
params = {
    "min_phrase_count": 1, 
    "min_context_count": 1,
    "min_phrasecontext_count": 1,
    "max_phrase_length": 4,
    "max_left_length": 4,
    "max_right_length": 4,
}

# the NifVector graph can be created from a NifGraph and a set of optional parameters
vec_graph = NifVectorGraph(
    nif_graph=nif_graph, 
    params=params
)
```

The phrase contexts of'the phrase 'War and Peace' are found in this way.

```python
phrase = "War and Peace"
vec_graph.phrase_contexts(phrase)
```

Resulting in the following contexts:

```console
{('book', 'SENTEND'): 1,
 ('the+book', 'SENTEND'): 1,
 ('wrote+the+book', 'SENTEND'): 1,
 ('Tolstoy+wrote+the+book', 'SENTEND'): 1}
 ```


So the context ('book', 'SENTEND') with the phrase 'War and Peace' occurs once in the text. You see that contrary to the original Word2Vec model multiple word contexts are generated with '+' as word separator.

Now we can find the most similar phrases of the phrase 'Pride and Prejudice'.

```python
phrase = "Pride and Prejudice"
vec_graph.most_similar(phrase)
```

This results in:

```console
{'Pride and Prejudice': (4, 4), 'War and Peace': (3, 4)}
```


The phrase 'War and Peace' has three out of four similar contexts.

## Querying the NifVector graph based on DBpedia


These are results of a NifVector graph created with 15.000 DBpedia pages. We defined a context of a word in it simplest form: the tuple of the previous word and the next word (no preprocessing, no changes to the text, i.e. no deletion of stopwords and punctuation).

```python
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from nifigator import NifVectorGraph, URIRef

# Connect to triplestore
store = SPARQLUpdateStore()
query_endpoint = 'http://localhost:3030/dbpedia_en/sparql'
update_endpoint = 'http://localhost:3030/dbpedia_en/update'
store.open((query_endpoint, update_endpoint))

# Create NifVectorGraph with this store
g = NifVectorGraph(store=store, identifier=URIRef("https://mangosaurus.eu/dbpedia"))
```

### Most frequent contexts


The eight most frequent contexts in which the word 'has' occurs with their number of occurrences are the following:

```python
# most frequent contexts of the word "has"
g.phrase_contexts("Washington Smithsonian Institution", topn=10)
```

This results in

```console
{('It', 'been'): 1031,
 ('it', 'been'): 1021,
 ('SENTSTART+It', 'been'): 848,
 ('and', 'been'): 642,
 ('which', 'been'): 414,
 ('that', 'been'): 390,
 ('also', 'a'): 388,
 ('and', 'a'): 380,
 ('there', 'been'): 378,
 ('it', 'a'): 326}
```

This means that the corpus contains 1429 occurrences of 'it has been', i.e. occurrences where the word 'has' occurred in the context ('it', 'been').

SENTSTART and SENTEND are tokens to indicate the start and end of a sentence.

### Contexts and phrase similarities

Only specific words and phrases occur in the contexts mentioned above. If you derive the phrases that share the most frequent contexts with the word 'has' then you get the following table (the columns contains the contexts, the rows the phrases that have the most contexts in common):

```python
import pandas as pd
pd.DataFrame().from_dict(
    g.dict_phrases_contexts("has", topcontexts=7), orient='tight'
)
```

This results in:

```console
                  it 	It      SENTSTART+It and     which   year   this+year
                  been 	been    been         been    been    been   been
             
has               1682 	1544 	1484         727     664     638    633
had 	          589 	53      63           196     1381    3      0
may have          79   	17      17           42      62      0      0
would have        66    9       9            9       44      0      0
have 	          5     0       0            244     300     0      0
has also          51    204     213          9       5       0      0
has never         20    6       6            5       2       0      0

```

The number of contexts that a word has in common with the most frequent contexts of another word can be used as a measure of distance to that word. You see that most of them are forms of the verb 'have'. Contexts ending with 'been' describe perfect tenses. The word 'had' (second row) has 6 contexts in common with the word 'has' so this word is very similar. The phrase 'would have' (fourth row) has 5 contexts in common, so 'could have' is also similar but less similar than the word 'had'. Normally a much higher number of most frequent contexts are used for similarity.

Note that the list contains 'had not' and 'has not'.

### Top phrase similarities


Based on the approach above we can derive top phrase similarities.

```python
# top phrase similarities of the word "has"
g.most_similar("has", topn=10, topcontexts=15)
```

This results in

```console
{
 'had': (15, 15),
 'has': (15, 15),
 'would have': (11, 15),
 'have': (9, 15),
 'may have': (9, 15),
 'is': (8, 15),
 'was': (8, 15),
 'also has': (7, 15),
 'could have': (7, 15),
 'has never': (7, 15)
}
```

The contexts in which words occur convey a lot of information about these words. Take a look at similar words of 'larger'. If we find the words with the lowest distance of this word in the way described above then we get:

```python
# top phrase similarities of the word "larger"
g.most_similar("larger", topn=10, topcontexts=15)
```

Resulting in:

```console
{
 'larger': (15, 15),
 'smaller': (14, 15),
 'greater': (12, 15),
 'higher': (11, 15),
 'less': (11, 15),
 'lower': (11, 15),
 'better': (10, 15),
 'longer': (10, 15),
 'more': (10, 15),
 'faster': (9, 15)
}
```

Like the word 'larger', these are all comparative adjectives. These words are close because they share the most frequent contexts. In general, you can derive (to some extent) the word class (the part of speech tag and the morphological features) from the contexts in which a word occurs. For example, if the previous word is 'the' and the next word is 'of' then the word between these words will probably be a noun. The word between 'have' and 'been' is almost always an adverb, the word between 'the' and 'book' is almost always an adjective. There are contexts that indicate the grammatical number, the verb tense, and so on.

Some contexts are close to each other in the sense that the same words occur in the same contexts, for example, the tuples (much, than) and (is, than) are close because both contexts allow the same words, in this case comparative adjectives. The contexts can therefore be combined and reduced in number. That is what happens when embeddings are calculated with the Word2Vec model. Similar contexts are summarized into one or a limited number of contexts. So it is no surprise that in a well-trained word2vec model adverbs are located near other adverbs, nouns near other nouns, etc. [It might be worthwhile to apply a bi-clustering algorithm here (clustering both rows and columns).]

Contexts can also be used to find 'semantic' similarities.

```python
# top phrase similarities of the word "given"
g.most_similar("given", topn=10, topcontexts=15)
```

```python
# top phrase similarities of the word "King"
g.most_similar("King", topn=10, topcontexts=15)
```

This results in

```console
{
 'King': (15, 15),
 'Emperor': (7, 15),
 'Queen': (7, 15),
 'king': (7, 15),
 'Chief Justice': (6, 15),
 'Church': (6, 15),
 'City': (6, 15),
 'Director': (6, 15),
 'Governor': (6, 15),
 'House': (6, 15)
}
```

However, what closeness and similarity exactly mean in relation to embeddings is not formalized. As you can see, closeness relates to syntactical closeness as well as semantic closeness without a distinction being made. Word and their exact opposite are close to each other because they can occur in the same context, i.e. the embeddings cannot distinguish the difference between larger and smaller. This is because embeddings are only based on the form of text, and not on meaning. Even if we have all original contexts, then the model would still not be able to distinguish antonyms like large and small.

### Simple 'masks'


Here are some examples of 'masks'.

```python
# simple 'masks'
context = ("King", "of England")
for r in g.context_phrases(context, topn=10).items():
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
# simple 'masks'
context = ("the", "city")
for r in g.context_phrases(context, topn=10).items():
    print(r)
```

```console
('largest', 156)
('capital', 148)
('old', 62)
('inner', 48)
('first', 42)
('second largest', 38)
('capital and largest', 33)
('Greek', 26)
('most populous', 26)
('south of the', 26)
```

### Vector calculations

The set of contexts in which a phrase occurs can be seen as a vector.

```python
from nifigator import NifVector

context = ("a", "woman")
woman = NifVector(g.context_phrases(context, topn=None))
context = ("a", "man")
man = NifVector(g.context_phrases(context, topn=None))
```

```python
print(woman - man)
```

```python
print(man - woman)
```

Word embeddings are necessarily derived from contexts and thereby only from the form of the text.

```python
d1 = NifVector(g.phrase_contexts("rainfall", topn=None))
d2 = NifVector(g.phrase_contexts("rain", topn=None))
(d1 & d2).topn(15)
```

```python
d1 = NifVector(g.phrase_contexts("cat", topn=None))
d2 = NifVector(g.phrase_contexts("dog", topn=None))
(d1 & d2).topn(15)
```

The Jaccard index is 
$J(A, B)=$$ | A\bigcap B | \over | A \bigcup B |$
and the Jaccard distance is 
$d_{J}(A, B)=1-J(A, B)$

```python

```

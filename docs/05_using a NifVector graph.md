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

# NifVector graphs

## Introduction


A NifVector graph is a network of phrases and contexts that occur in a certain document set (in Nif). It can be used as if it were a language model.

From a Nifvector graph you can derive phrase (multiwords) and context vectors with their frequencies in the document set. The main difference to traditional word vector embeddings is that no dimensionality reduction is applied; and there is no model created with real-valued vector embeddings. Instead, the NifVectors are derived directly from the corpus itself without any transformation.

The phrase and context vectors can be used for word and sentence similarities, and for search engines. They can also be combined to create a vector that is a representation of the phrase with the context in which it occurs.

```python
import os, sys, logging
logging.basicConfig(stream=sys.stdout, 
                    format='%(asctime)s %(message)s',
                    level=logging.INFO)
```

### Simple NifVector graph example to introduce the idea

Let's setup a nif graph with a context with two sentences.

```python
# The NifContext contains a context which uses a URI scheme
from nifigator import NifGraph, NifContext, OffsetBasedString, NifContextCollection

# Make a context by passing uri, uri scheme and string
context = NifContext(
  uri="https://mangosaurus.eu/rdf-data/doc_1",
  URIScheme=OffsetBasedString,
  isString="""We went to the park to walk. 
              Yesterday, we went to the city to do some shopping."""
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
    "max_phrase_length": 3,
    "max_left_length": 3,
    "max_right_length": 3,
}

# the NifVector graph can be created from a NifGraph and a set of optional parameters
g = NifVectorGraph(
    nif_graph=nif_graph, 
    params=params
)
```

The contexts of the work 'park' are found in this way.

```python
phrase = "park"
g.phrase_contexts(phrase)
```

Resulting in the following contexts:

```console
Counter({('the', 'to'): 1,
         ('the', 'to+walk'): 1,
         ('the', 'to+walk+SENTEND'): 1,
         ('to+the', 'to'): 1,
         ('to+the', 'to+walk'): 1,
         ('to+the', 'to+walk+SENTEND'): 1,
         ('went+to+the', 'to'): 1,
         ('went+to+the', 'to+walk'): 1,
         ('went+to+the', 'to+walk+SENTEND'): 1})
 ```


So the context ('the', 'to+walk+SENTEND') with the phrase 'park' occurs once in the text. You see that contrary to the original Word2Vec model multiple word contexts are generated with '+' as word separator.

Now we can find the most similar words of the word 'park'.


```python
phrase = "park"
g.most_similar(phrase)
```

This results in:

```console
{'park': (9, 9), 'city': (3, 9)}
```

The word 'city' has three out of nine similar contexts.


## Querying the NifVector graph based on DBpedia


These are results of a NifVector graph created with 10.000 DBpedia pages. We defined a context of a word in it simplest form: the tuple of the previous multiwords and the next multiwords (no preprocessing, no changes to the text, i.e. no deletion of stopwords and punctuation). The maximum phrase length is five words, the maximum left and right context is three words.

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
g.phrase_contexts("has", topn=10)
```

This results in

```console
Counter({('it', 'been'): 1021,
         ('SENTSTART+It', 'been'): 858,
         ('It', 'been'): 827,
         ('and', 'been'): 575,
         ('that', 'been'): 428,
         ('there', 'been'): 420,
         ('which', 'been'): 420,
         ('also', 'a'): 388,
         ('and', 'a'): 323,
         ('which', 'a'): 233})
```

This means that the corpus contains 1021 occurrences of 'it has been', i.e. occurrences where the word 'has' occurred in the context ('it', 'been').

SENTSTART and SENTEND are tokens to indicate the start and end of a sentence.


### Contexts and phrase similarities


The contexts in which a word occurs to some extent represent the properties and the meaning of a word. If you can derived the phrases that share the most frequent contexts of the word 'has' you get the following table (the columns contains the contexts, the rows the phrases that have the most contexts in common):

```python
import pandas as pd
pd.DataFrame().from_dict(
    g.dict_phrases_contexts("has", topcontexts=8), orient='tight'
)
```

This results in:

```console
                  it 	SENTSTART+It 	It      and 	that 	there 	which   also
                  been 	been 	        been 	been 	been 	been 	been    a
            
has 	          1021 	858 	        827 	575 	428 	420 	420     388
had 	          326 	47             	40    	169 	559 	112 	786     153
could have        11 	2               2      	2       15      2    	5       2 
has never         12 	6               6       5     	5       3    	2       0
has not           28    7               7    	12      20      2    	7       0
may have          46 	17              17   	42   	16  	18  	50      0
would have        61 	9               6   	2       37   	10   	32      0
```


The number of contexts that a word has in common with contexts of another word can be used as a measure of similarity. So, the word 'had' (second row) has eight contexts in common with the word 'has' so this word is very similar. The phrase 'would have' (seventh row) has seven contexts in common, so 'would have' is also similar but less similar than the word 'had'. We used a limited number of contexts to show the idea; normally a higher number of contexts are used to compare the similarity of words.

The similarities found can explained as follows. In this case, you see that similar words are all forms of the verb 'have'. This is because the verb is often used in the construction of perfect tenses, where the verb 'have' is combined with the past participle of another verb, in this case the often occuring 'been'.

Note that the list contains 'has not'.


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

Now take a look at similar words of 'larger'.

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

Like the word 'larger', these are all comparative adjectives. These words are close because they share the most frequent contexts. In general, you can derive (to some extent) the word class (the part of speech tag and the morphological features) from the contexts in which a word occurs. For example, if the previous word is 'the' and the next word is 'of' then the word between these words will probably be a noun. The word between 'have' and 'been' is almost always an adverb, the word between 'the' and 'book' is almost always an adjective. Likewise, there are contexts that indicate the grammatical number, the verb tense, and so on.

Some contexts are close to each other in the sense that the same words occur in the same contexts, for example, the tuples (much, than) and (is, than) are close because both contexts allow the same words, in this case comparative adjectives. The contexts can therefore be combined and reduced in number. That is what happens when embeddings are calculated with the Word2Vec model. Similar contexts are summarized into one or a limited number of contexts. So it is no surprise that in a well-trained word2vec model adverbs are located near other adverbs, nouns near other nouns, etc. [It might be worthwhile to apply a bi-clustering algorithm here (clustering both rows and columns).]

```python
# top phrase similarities of the word "given"
g.most_similar("given", topn=10, topcontexts=15)
```

Contexts can also be used to find 'semantic' similarities.

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



Instead of single words we can also find the similarities of multiwords

```python
# top phrase similarities of Barack Obama
g.most_similar("Barack Obama", topn=10, topcontexts=15)
```

```console
Counter({'Barack Obama': (11, 11),
         'Franklin D Roosevelt': (4, 11),
         'Bill Clinton': (3, 11),
         'George W Bush': (3, 11),
         'John F Kennedy': (3, 11),
         'Lukashenko': (3, 11),
         'Richard Nixon': (3, 11),
         'Ronald Reagan': (3, 11),
         'Abraham Lincoln': (2, 11),
         'Bush': (2, 11)})
```



As you can see, similarity relates to syntactical similarity as well as semantic similarity without a distinction being made. Word and their exact opposite are close to each other because they can occur in the same context, i.e. with the context vector you cannot distinguish the difference between the words larger and smaller. This is because we only use the form of text, and not its meaning.


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


### Context sets


We calculate with sets of contexts instead of real-valued vectors.

For example, different adverbs for the words man and woman (results are highly depended on documents used).

```python
context = ("the", "woman")
c1 = g.context_phrases(context, topn=None)
context = ("the", "man")
c2 = g.context_phrases(context, topn=None)
```

Result of set substraction W \ M (adverbs that are used between 'the' and 'woman' but not between 'the' and 'man':

```python
(c1 - c2).most_common(5)
```

```console
[('first', 93), ('sinful', 12), ('pregnant', 5), ('only', 4), ('Hawksian', 3)]
```

Result of set substraction M \ W (adverbs that are used between 'the' and 'man' but not between 'the' and 'woman':

```python
(c2 - c1).most_common(5)
```
```console
[('white', 17), ('young', 16), ('common', 16), ('last', 13), ('great', 11)]
```


### Phrase similarities given a specific context

Some phrases have multiple meanings. Take a look at the contexts of the word 'deal':

```python
g.phrase_contexts("deal", topn=10)
```

In some of these contexts 'deal' is a verb meaning 'to do business' and in other contexts 'deal' is a noun meaning a 'contract' or an 'agreement'. The specific meaning can be derived from the context in which the phrase is used.

It is possible to take into account a specific context when using the most_similar function in the following way:

```python
g.most_similar(phrase="deal", context=("to", "with"), topcontexts=50, topphrases=15)
```

```console
{'deal': (50, 50),
 'work': (17, 50),
 'play': (10, 50),
 'compete': (7, 50),
 'cope': (6, 50),
 'coincide': (5, 50),
 'comply': (5, 50),
 'interact': (5, 50),
 'help': (4, 50),
 'meet': (4, 50),
 'be confused': (3, 50),
 'communicate': (3, 50),
 'do': (3, 50),
 'live': (3, 50),
 'be associated': (2, 50)}
```


The results consists of only verbs.

```python
g.most_similar(phrase="deal", context=("a", "with"), topcontexts=5000, topphrases=15)
```

```console
{'deal': (50, 50),
 'contract': (13, 50),
 'treaty': (12, 50),
 'meeting': (11, 50),
 'relationship': (11, 50),
 'problem': (10, 50),
 'man': (9, 50),
 'person': (8, 50),
 'partnership': (7, 50),
 'coalition': (6, 50),
 'collaboration': (4, 50),
 'friendship': (3, 50),
 'joint venture': (3, 50),
 'duet': (1, 50),
 'female householder': (1, 50)
}
```


Now the results are nouns.

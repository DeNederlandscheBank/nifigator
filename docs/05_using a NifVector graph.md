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


A NifVector graph is a network of phrases and related contexts that occur in a certain document set (in Nif). It can be used as if it were a language model.

From a NifVector graph you can derive vectors of phrases (i.e. a multiword expression) and contexts that contain the number of occurrences in a document set. The main difference of a NifVector graph to traditional word vector embeddings is that no dimensionality reduction is applied; and there is no model created with real-valued vector embeddings. Instead, the NifVectors are derived directly from the document set itself without any transformation.

The phrase and context vectors can be used for word and sentence similarities and for search engines. They can also be combined to create a vector that is a representation of the phrase together with the context in which it occurs.

```python
import os, sys, logging
logging.basicConfig(stream=sys.stdout, 
                    format='%(asctime)s %(message)s',
                    level=logging.INFO)
```

### Simple NifVector graph example to introduce the idea

Let's setup a NifVector graph with a context with two sentences.

```python
# The NifContext contains a context which uses a URI scheme
from nifigator import NifGraph, NifContext, OffsetBasedString, NifContextCollection

isString = "We went to the small park to walk.\n Yesterday, we went to the city to shop."

# Make a context by passing uri, uri scheme and string
context = NifContext(
  uri="https://mangosaurus.eu/rdf-data/doc_1",
  URIScheme=OffsetBasedString,
  isString=isString
)
context.extract_sentences()

# Make a Nif context collection
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
    "max_context_length": 3,
}

# the NifVector graph can be created from a NifGraph and a set of optional parameters
g = NifVectorGraph(
    nif_graph=nif_graph, 
    params=params
)
```

```python
# g.serialize(destination="test.ttl", format="ttl")
```

The contexts of the work 'park' are found in this way.

```python
phrase = "small park"
g.phrase_contexts(phrase)
```

Resulting in the following contexts:

```console
Counter({('to the', 'to'): 1,
         ('the', 'to walk'): 1,
         ('to the', 'to walk'): 1,
         ('went to the', 'to'): 1,
         ('the', 'to'): 1})
 ```

So the context ('to the', 'to') with the phrase 'small park' occurs once in the text.

You see that, contrary to Word2Vec models a NifVector graph also derives contexts of phrases (i.e. multiword expressions).

The phrases that occurs within this context can be found in the following way:

```python
g.context_phrases(('to the', 'to'))
```

Now we can find the most similar words of the word 'park'.

```python
phrase = "city"
g.most_similar(phrase)
```

This results in:

```console
{'city': (5, 5), 'small park': (3, 5)}
```

The word 'small park' has three out of five similar contexts.

Similarly the most similar phrases to walk are:

```python
phrase = "walk"
g.most_similar(phrase)
```

This results in:

```console
{'walk': (2, 2), 'shop': (1, 2)}
```

The most similar phrases are derived from the contexts in which the words occur. You see that, given the two sentences above, the most similar words of 'park' are nouns (park and city) and likewise the most similar word of 'walk' are verbs (walk and shop).


## Querying the NifVector graph based on DBpedia


These are results of a NifVector graph created with 10.000 DBpedia pages. We defined a context of a word in it simplest form: the tuple of the previous multiwords and the next multiwords (no preprocessing, no changes to the text, i.e. no deletion of stopwords and punctuation). The maximum phrase length is five words, the maximum left and right context length is also five words.

```python
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from nifigator import NifVectorGraph, URIRef

# Connect to triplestore
store = SPARQLUpdateStore()
query_endpoint = 'http://localhost:3030/dbpedia_en/sparql'
update_endpoint = 'http://localhost:3030/dbpedia_en/update'
store.open((query_endpoint, update_endpoint))

# Create NifVectorGraph with this store
g = NifVectorGraph(store=store, 
                   identifier=URIRef("https://mangosaurus.eu/dbpedia")
)
```


### Most frequent contexts


The eight most frequent contexts in which the word 'has' occurs with their number of occurrences are the following:

```python
# most frequent contexts of the word "has"
g.phrase_contexts("has", topn=10)
```

This results in

```console
Counter({('It', 'been'): 1031,
         ('SENTSTART It', 'been'): 951,
         ('it', 'been'): 836,
         ('and', 'been'): 642,
         ('which', 'been'): 521,
         ('also', 'a'): 436,
         ('there', 'been'): 420,
         ('and', 'a'): 418,
         ('that', 'been'): 339,
         ('it', 'a'): 270})
```

This means that the corpus contains 1031 occurrences of 'It has been', i.e. occurrences where the word 'has' occurred in the context ('It', 'been').

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

                  It 	it      SENTSTART It    and     which   also    there   and
                  been 	been 	been 	        been    been    a       been    a
          
has               1031  1021    954             642   521     436     420     418
had               71    402     53              169   886     266     171     336
would have        14 	75   	10              9     53      2       15 	2
may have          26 	82  	26              37    61      0       33 	2
could have        2 	24  	2               2     7       0       4 	0
has also          149 	60  	180             12    5       0       11 	0
has always        2 	3   	2               2     3       0       2 	0          

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
{'had': (15, 15),
 'has': (15, 15),
 'would have': (12, 15),
 'have': (10, 15),
 'may have': (10, 15),
 'could have': (9, 15),
 'has never': (8, 15),
 'has not': (8, 15),
 'also has': (7, 15),
 'had long': (7, 15)}
```

Now take a look at similar words of 'larger'.

```python
# top phrase similarities of the word "larger"
g.most_similar("larger", topn=10, topcontexts=15)
```

Resulting in:

```console
{'larger': (15, 15),
 'smaller': (14, 15),
 'greater': (13, 15),
 'higher': (12, 15),
 'longer': (11, 15),
 'better': (10, 15),
 'faster': (10, 15),
 'less': (10, 15),
 'lower': (10, 15),
 'shorter': (10, 15)}
```

Like the word 'larger', these are all comparative adjectives. These words are close because they share the most frequent contexts. In general, you can derive (to some extent) the word class (the part of speech tag and the morphological features) from the contexts in which a word occurs. For example, if the previous word is 'the' and the next word is 'of' then the word between these words will probably be a noun. The word between 'have' and 'been' is almost always an adverb, the word between 'the' and 'book' is almost always an adjective. Likewise, there are contexts that indicate the grammatical number, the verb tense, and so on.

Some contexts are close to each other in the sense that the same words occur in the same contexts, for example, the tuples (much, than) and (is, than) are close because both contexts allow the same words, in this case comparative adjectives. The contexts can therefore be combined and reduced in number. That is what happens when embeddings are calculated with the Word2Vec model. Similar contexts are summarized into one or a limited number of contexts. So it is no surprise that in a well-trained word2vec model adverbs are located near other adverbs, nouns near other nouns, etc. [It might be worthwhile to apply a bi-clustering algorithm here (clustering both rows and columns).]

```python
# top phrase similarities of the word "given"
g.most_similar("given", topn=10, topcontexts=15)
```

```console
{'given': (15, 15),
 'awarded': (12, 15),
 'called': (12, 15),
 'made': (12, 15),
 'assigned': (11, 15),
 'considered': (11, 15),
 'granted': (11, 15),
 'offered': (11, 15),
 'released': (11, 15),
 'used': (11, 15)}
```

Contexts can also be used to find 'semantic' similarities.

```python
# top phrase similarities of the word "King"
g.most_similar("King", topn=10, topcontexts=15)
```

This results in

```console
{'King': (15, 15),
 'President': (8, 15),
 'Queen': (8, 15),
 'king': (8, 15),
 'Emperor': (7, 15),
 'Kingdom': (7, 15),
 'Prince': (7, 15),
 'enemies': (7, 15),
 'kings': (7, 15),
 'president': (7, 15)}
```



Instead of single words we can also find the similarities of multiwords

```python
# top phrase similarities of Barack Obama
g.most_similar("Barack Obama", topn=10, topcontexts=15)
```

```console
{'Barack Obama': (15, 15),
 'Bill Clinton': (5, 15),
 'Ronald Reagan': (5, 15),

 'Franklin D Roosevelt': (4, 15),
 'George W Bush': (4, 15),
 'Richard Nixon': (4, 15),
 'Bush': (3, 15),
 'Dwight D Eisenhower': (3, 15),
 'George H W Bush': (3, 15)}
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
('Henry VIII', 15)
('Charles II', 12)
('John', 12)
('Henry III', 8)
('James I', 8)
('Edward I', 7)
('Edward III', 6)
('Charles I', 5)
('Henry VII', 5)
('Henry II', 4)
```

```python
# simple 'masks'
context = ("the", "city")
for r in g.context_phrases(context, topn=10).items():
    print(r)
```

```console
('capital', 141)
('largest', 140)
('old', 55)
('inner', 52)
('first', 48)
('second largest', 44)
('ancient', 43)
('most populous', 39)
('Greek', 37)
('port', 31)
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
[('first', 133),
 ('sinful', 12),
 ('number of children born per', 7),
 ('pregnant', 6),
 ('high of children born per', 5)]
```

Result of set substraction M \ W (adverbs that are used between 'the' and 'man' but not between 'the' and 'woman':

```python
(c2 - c1).most_common(5)
```
This results in:

```console
[('common', 23), ('last', 21), ('white', 18), ('young', 15), ('great', 13)]
```


### Phrase similarities given a specific context

Some phrases have multiple meanings. Take a look at the contexts of the word 'deal':

```python
g.phrase_contexts("deal", topn=10)
```

<!-- #region -->
This results in:

```console
Counter({('to', 'with'): 487,
         ('great', 'of'): 348,
         ('a great', 'of'): 326,
         ('to', 'with the'): 165,
         ('a', 'with'): 84,
         ('a good', 'of'): 36,
         ('had to', 'with'): 35,
         ('good', 'of'): 28,
         ('SENTSTART The', 'was'): 25,
         ('The', 'was'): 25})
```


In some of these contexts 'deal' is a verb meaning 'to do business' and in other contexts 'deal' is a noun meaning a 'contract' or an 'agreement'. The specific meaning can be derived from the context in which the phrase is used.

It is possible to take into account a specific context when using the most_similar function in the following way:
<!-- #endregion -->

```python
g.most_similar(phrase="deal", context=("to", "with"), topcontexts=50, topphrases=15, topn=10)
```

The result is:

```console
{'deal': (50, 50),
 'work': (20, 50),
 'comply': (9, 50),
 'compete': (7, 50),
 'cope': (7, 50),
 'interact': (7, 50),
 'coincide': (6, 50),
 'communicate': (6, 50),
 'do': (6, 50),
 'help': (6, 50)}
```

So these are all verbs, similar to the verb 'deal'.

```python
g.most_similar(phrase="deal", context=("a", "with"), topcontexts=50, topphrases=15, topn=10)
```

In this case the result is:

```console
{'deal': (50, 50),
 'contract': (12, 50),
 'treaty': (12, 50),
 'meeting': (11, 50),
 'relationship': (11, 50),
 'man': (10, 50),
 'dispute': (8, 50),
 'partnership': (8, 50),
 'person': (8, 50),
 'coalition': (7, 50)}
```

So, now the results are nouns, and similar to the noun 'deal'.


### Most similar phrases given a set of contexts

If you want to find the phrases that fit a set of contexts then this is also possible.

```python
c1 = [
        c[0] for c in (
            g.phrase_contexts("considered", topn=None) &
            g.phrase_contexts("believed", topn=None)
         ).most_common(15)
]
c1
```

This results in:

```console
[('is', 'to'),
 ('is', 'to be'),
 ('are', 'to'),
 ('was', 'to'),
 ('are', 'to be'),
 ('is', 'to have'),
 ('is', 'to be the'),
 ('was', 'to be'),
 ('were', 'to'),
 ('generally', 'to'),
 ('are', 'to have'),
 ('is', 'to be a'),
 ('is', 'by'),
 ('widely', 'to'),
 ('he', 'to')]
```

```python
g.most_similar(contexts=c1, topn=10)
```

Resulting in:

```console
{'believed': (15, 15),
 'considered': (15, 15),
 'thought': (14, 15),
 'expected': (13, 15),
 'known': (13, 15),
 'reported': (13, 15),
 'said': (13, 15),
 'assumed': (12, 15),
 'claimed': (12, 15),
 'held': (12, 15)}
```

```python

```

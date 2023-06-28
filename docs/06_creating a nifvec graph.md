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


In a NifVector graph vector embeddings are defined from words and phrases, and the original contexts in which they occur (all in Nif). No dimensionality reduction is applied and this enables to obtain some understanding about why certain word are found to be close to each other.

```python
import os, sys, logging
logging.basicConfig(stream=sys.stdout, 
                    format='%(asctime)s %(message)s',
                    level=logging.INFO)
```

## Simple NifVector graph example to introduce the idea

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
# Make a collection by passing a uri
collection = NifContextCollection(uri="https://mangosaurus.eu/rdf-data")
collection.add_context(context)
nif_graph = NifGraph(collection=collection)
```

```python
from nifigator import NifVectorGraph

# set up the params of the NifVector graph
params = {
    "min_phrase_count": 1, 
    "min_context_count": 1,
    "min_phrasecontext_count": 1,
    "max_phrase_length": 4,
    "max_context_length": 4,
}

# the NifVector graph can be created from a NifGraph and a set of optional parameters
vec_graph = NifVectorGraph(
    nif_graph=nif_graph, 
    params=params
)
```

```python
phrase = "War and Peace"
for line in vec_graph.phrase_contexts(phrase):
    print(line)
```

```console
(('book', 'SENTEND'), 1)
(('the+book', 'SENTEND'), 1)
(('wrote+the+book', 'SENTEND'), 1)
(('Tolstoy+wrote+the+book', 'SENTEND'), 1)
```

```python
phrase = "Pride and Prejudice"
for line in vec_graph.most_similar(phrase):
    print(line)
```

```console
('Pride and Prejudice', 0.0)
('War and Peace', 0.25)
```


## Creating NifVector graphs

```python
# from nltk.corpus import stopwords
# stop_words = list(stopwords.words('english'))+[word[0].upper()+word[1:] for word in stopwords.words('english')]

# from nifigator import NifVectorGraph, NifGraph, tokenizer

# lang = 'en'

# params = {
#     "min_phrase_count": 2, 
#     "min_context_count": 2,
#     "min_phrasecontext_count": 2,
#     "max_phrase_length": 4,
#     "max_context_length": 2,
#     "words_filter": {"name": "NLTK_stopwords", 
#                      "data": stop_words}
# }
# for j in range(16, 26):
    
#     # the nifvector graph can be created from a NifGraph and a set of optional parameters
#     file = os.path.join("E:\\data\\dbpedia\\extracts", lang, "dbpedia_"+"{:04d}".format(j)+"_lang="+lang+".ttl")
    
#     nif_graph = NifGraph(file=file)
#     collection = nif_graph.collection
#     documents = [context.isString for context in collection.contexts]
#     vec_graph = NifVectorGraph(
#         documents=documents,
#         params=params
#     )
#     logging.info(".. Serializing graph")
#     vec_graph.serialize(destination=os.path.join("E:\\data\\dbpedia\\nifvec\\", "nifvec_filtered_"+"{:04d}".format(j)+"_lang="+lang+".xml"), format="xml")
```

## Querying the NifVector graph


These are results of a NifVector graph created with 15.000 DBpedia pages.

The text contains in total almost 2.7 million unique words, and 2.8 million unique contexts, i.e. (previous-word, next-word)-tuples. It is a relatively small data set, but it fits the purpose.

In the Word2Vec model the 2.8 million contexts would be reduced to a few hundred dimensions. In what follows we keep the original contexts.

We defined a context of a word in it simplest form: the tuple of the previous word and the next word (no preprocessing, no changes to the text, i.e. no deletion of stopwords and punctuation).

The original Word2Vec produces embeddings for each single word. But because the data is stored in a graph database, we can easily allow multiple words between the contexts. So below, you will find the results allowing for multiples words.

```python
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib.graph import DATASET_DEFAULT_GRAPH_ID as default
from nifigator import NifVectorGraph

# Connect to triplestore
store = SPARQLUpdateStore()
query_endpoint = 'http://localhost:3030/nifvec_en/sparql'
update_endpoint = 'http://localhost:3030/nifvec_en/update'
store.open((query_endpoint, update_endpoint))

# Create NifVectorGraph with this store
g = NifVectorGraph(store=store, identifier=default)
```

### Most frequent contexts


The eight most frequent contexts in which the word 'has' occurs with their number of occurrences are the following:

```python
# most frequent contexts of the word "has"
g.phrase_contexts("has", topn=7)
```

This results in

```console
[(('it', 'been'), 1429),
 (('It', 'been'), 1353),
 (('SENTSTART+It', 'been'), 1234),
 (('and', 'been'), 579),
 (('which', 'been'), 556),
 (('there', 'been'), 516),
 (('also', 'a'), 509),
 (('and', 'a'), 479),
 (('that', 'been'), 451),
 (('which', 'a'), 375)]
```

This means that the corpus contains 1429 occurrences of 'it has been', i.e. occurrences where the word 'has' occurred in the context ('it', 'been').

SENTSTART and SENTEND are tokens to indicate the start and end of a sentence.


### Top phrase similarities


Only specific words and phrases occur in the contexts mentioned above. If you derive the phrases that share the most frequent contexts then you get the following table (the columns contains the contexts, the rows the phrases that have the most contexts in common):

```python
# top phrase similarities of the word "has"
g.most_similar("has", topn=10, topcontexts=15)
```

This results in

```console
[('had', 0.0),
 ('has', 0.0),
 ('may have', 0.2666666666666667),
 ('would have', 0.2666666666666667),
 ('have', 0.33333333333333337),
 ('has also', 0.4666666666666667),
 ('has never', 0.4666666666666667),
 ('has not', 0.4666666666666667),
 ('must have', 0.4666666666666667),
 ('also has', 0.5333333333333333)]
```

You see that most of them are forms of the verb 'have'. Most contexts, ending with 'been', describe perfect tenses. The word 'had' (first row) has all 7 contexts in common with the word 'has' so this word is very similar. The phrase 'could have' (fourth row) has 6 contexts in common (all except the context (also, a)), so 'could have' is also similar but less similar than the word 'had'. The number of contexts that a word has in common with the most frequent contexts of another word can be used as a measure of distance to that word. Based on the table above, we find for 'has' the following similar word with distances:

Here we looked at the shared contexts with the seven most frequent ones of the word 'has', to visualize what happens, but normally a much higher number of most frequent contexts can be used. 

Of course, other distance measures can be used, for example also based on the number of occurrences, but this is the simplest form and works for our purpose fine. Note that the list contains 'had not' and 'has not'.

```python
# top phrase similarities of the word "larger"
g.most_similar("football", topn=10, topcontexts=15)
```

The contexts in which words occur convey a lot of information about these words. Take a look at similar words of 'larger'. If we find the words with the lowest distance of this word in the way described above then we get:

Like the word 'larger', these are all comparative adjectives. Why is that? These words are close because they share the most frequent contexts, as the following table shows.

So words that fit in these contexts are comparable adjectives. In general, you can derive (to some extent) the word class (the part of speech tag) from the contexts in which a word occurs. For example, if the previous word is 'the' and the next word is 'of' then the word between these words will probably be a noun. The word between 'have' and 'been' is almost always an adverb, the word between 'the' and 'book' is almost always an adjective. There are contexts that indicate the grammatical number, the verb tense, and so on.

You see that some contexts are close to each other in the sense that the same words occur in the same contexts, for example, the tuples (much, than) and (is, than) are close because both contexts allow the same words, in this case comparative adjectives. The contexts can therefore be combined and reduced in number. That is what happens when embeddings are calculated with the Word2Vec model. Similar contexts are summarized into one or a limited number of contexts. So it is no surprise that in a well-trained word2vec model adverbs are located near other adverbs, nouns near other nouns, etc. [It might be worthwhile to apply a bi-clustering algorithm here (clustering both rows and columns).]

```python
# top phrase similarities of the word "King"
g.most_similar("King", topn=10, topcontexts=15)
```

This results in

```console
[('King', 0.0),
 ('Emperor', 0.4666666666666667),
 ('Prince', 0.4666666666666667),
 ('President', 0.5333333333333333),
 ('Queen', 0.5333333333333333),
 ('State', 0.5333333333333333),
 ('king', 0.5333333333333333),
 ('Chancellor', 0.6),
 ('Church', 0.6),
 ('City', 0.6)]
```


### Simple 'masks'

```python
# simple 'masks'
context = ("King", "of England")
for r in g.context_words(context, topn=10).items():
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
context = ("the", "City")
for r in g.context_words(context, topn=10).items():
    print(r)
```

### Vector calculations

```python
# vector calculations
context = ("a", "woman")
woman = set(r for r in g.context_words(context, topn=10).keys())
context = ("a", "man")
man = set(r for r in g.context_words(context, topn=10).keys())
```

```python
print(woman - man)
```

```python
print(man - woman)
```

What closeness and similarity mean in relation to embeddings is not formalized. Closeness relates to syntactical closeness as well as semantic closeness without a distinction being made. Word and their exact opposite are close to each other because they can occur in the same contexts, i.e. the embeddings cannot distinguish the difference between larger and smaller. This is because embeddings are only based on the form of text, and not on meaning.

Even if we would use all original contexts, then we are the model would not be able to distinguish large and small. 

Word embeddings are necessarily derived from contexts and thereby only from the form of the text.

```python

```

```python
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from rdflib.graph import DATASET_DEFAULT_GRAPH_ID as default
from nifigator import NifGraph

# Connect to triplestore
store = SPARQLUpdateStore()
query_endpoint = 'http://localhost:3030/dbpedia_tokenized_en/sparql'
update_endpoint = 'http://localhost:3030/dbpedia_tokenized_en/update'
store.open((query_endpoint, update_endpoint))

# Create NifVectorGraph with this store
g = NifGraph(store=store, identifier=default)
```

```python
from rdflib.plugins.stores import sparqlstore, memory

q = """
    SELECT ?s ?begin ?end
    WHERE
    {
    """
if not isinstance(g.store, memory.Memory):
    q += "SERVICE <" + g.store.query_endpoint + "> "
q += """
        {
            ?s rdf:type nif:Sentence .
            ?s nif:beginIndex ?begin .
            ?s nif:endIndex ?end .
            ?s nif:referenceContext [ nif:isString ?string] .
        }
    }
    LIMIT 15
"""
for r in g.query(q):
    print(r)
#             BIND (SUBSTR(?string, ?begin, ?end - ?begin) as ?sentence_text)
```

```python
documents = ["The capital city of the United Kingdom is London.", "Paris is the capital of France."]
```

```python
from nifigator import tokenizer, to_iri, RDF, NIF, URIRef
import regex as re

sentences_phrases = []
for document in documents:
    sentence_lexicon = ContextVector()
    tokenized_text = tokenizer(document)
    for tok_sentence in tokenized_text:

        sentence = (
            ["SENTSTART"]
            + [
                word["text"]
                for word in tok_sentence
                if re.match("^[0-9]*[a-zA-Z]*$", word["text"])
            ]
            + ["SENTEND"]
        )
        for idx, word in enumerate(sentence):
            for phrase_length in range(1, 4 + 1):
                if (idx <= len(sentence) - phrase_length):
                    phrase = g.phrase_separator.join(
                        sentence[idx+i]
                        for i in range(0, phrase_length)
                    )
                    lexicon_uri = URIRef(
                            g.lexicon_ns
                            + phrase
                    )
                    sentence_lexicon += ContextVector(g.phrase_contexts(phrase=phrase, topn=5))
    sentences_phrases.append(sentence_lexicon)
```

```python
sentences_phrases
```

```python
class ContextVector(dict):
    
    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)
        self = {
            k: v for k, v in sorted(
                self.items(), 
                reverse=True, 
                key=lambda item: item[1]
            )
        }
    
    def __sub__(self, other):
        for item in other.keys():
            if item in self.keys():
                del self[item]
        self = ContextVector(self)
        return self
        
    def __add__(self, other):
        d = ContextVector()
        for item in self.keys():
            if item in other.keys():
                d[item] = other[item] + self[item]
        self = ContextVector()
        return self

    def __and__(self, other):
        return self + other
       
    def __or__(self, other):
        for item in other.keys():
            if item in self.keys():
                self[item] += other[item]
            else:
                self[item] = other[item]
        self = ContextVector(self)
        return self
    
    def topn(self, n: int = 5):
        return ContextDict(list(self.items())[0:n])
```

```python
d1 = ContextDict(g.phrase_contexts("rainfall", topn=None))
d2 = ContextDict(g.phrase_contexts("rain", topn=None))
(d1 & d2).topn(15)
```

```python
d1 = ContextDict(g.phrase_contexts("cat", topn=None))
d2 = ContextDict(g.phrase_contexts("dog", topn=None))
(d1 & d2).topn(15)
```

```python
d1 = ContextDict(g.phrase_contexts("Queen", topn=None))
d2 = ContextDict(g.phrase_contexts("King", topn=None))
(d1 - d2).topn(15)
```

```python
d1 = ContextDict(g.phrase_contexts("Anne", topn=None))
d2 = ContextDict(g.phrase_contexts("John", topn=None))
(d1 & d2).topn(15)
```

```python

```

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

# Vector representations


This shows an example how to use the vectors to find sentence similarities and to search in text given a text query.

The set of all contexts in which a phrase occurs can be seen as a vector representation of that phrase. Likewise, the set of all phrases that occur in a specific contexts can be seen as a vector representation of that context. These vector representations of phrases and contexts can be used in downstream NLP tasks like word and sentence similarities and search engines. 

The vector representation of a sentence is simply the union of the vectors of the phrases (and possibly contexts) in the sentence, similar to adding vector embeddings of the words in a sentence to calculate the sentence vector embeddings.

```python
import os, sys, logging
logging.basicConfig(stream=sys.stdout, 
                    format='%(asctime)s %(message)s',
                    level=logging.INFO)
```

### Connect to database and load vector representations

```python
from rdflib import URIRef

database_url = 'http://localhost:3030/dbpedia_en'
identifier = URIRef("https://mangosaurus.eu/dbpedia")
```

```python
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from nifigator import NifVectorGraph

# Connect to triplestore
store = SPARQLUpdateStore(
    query_endpoint = database_url+'/sparql',
    update_endpoint = database_url+'/update'
)
# Create NifVectorGraph with this store
g = NifVectorGraph(
    store=store, 
    identifier=identifier
)
```

```python
import pickle

with open('..//data//phrase_vectors.pickle', 'rb') as handle:
    v_phrases = pickle.load(handle)
with open('..//data//lemma_vectors.pickle', 'rb') as handle:
    v_lemmas = pickle.load(handle)
with open('..//data//context_phrases_vectors.pickle', 'rb') as handle:
    v_contexts = pickle.load(handle)
```

```python
# the vector of 'is' is a subset of the vector of 'be'
print(v_phrases['is'] <= v_lemmas['be'])

# the vector 'discovered' is a subset of the vector of 'discover'
print(v_phrases['discovered'] <= v_lemmas['discover'])

# the union of the vectors of 'king' and 'kings' is equal to the vector of 'king'
print(v_phrases['kings'] + v_phrases['king'] == v_lemmas['king'])
```

### Load and set up two DBpedia pages


We take two pages from DBpedia about two stars, Aldebaran and Antares. 

```python
# Read two documents in DBpedia about Aldebaran and Antares stars
doc1 = g.get(
    URIRef("http://dbpedia.org/resource/Aldebaran?dbpv=2020-07&nif=context")
)
doc2 = g.get(
    URIRef("http://dbpedia.org/resource/Antares?dbpv=2020-07&nif=context")
)
```

The first document reads:

```python
print(doc1)
```

```console
(nif:Context) uri = <http://dbpedia.org/resource/Aldebaran?dbpv=2020-07&nif=context>
  sourceUrl : <http://en.wikipedia.org/wiki/Aldebaran?oldid=964792900&ns=0>
  predLang : <http://lexvo.org/id/iso639-3/eng>
  isString : 'Aldebaran , designated α Tauri (Latinized to Alpha Tauri, abbreviated Alpha Tau, α Tau), is an orange giant star measured to be about 65 light-years from the Sun in the zodiac constellation Taurus. It is the brightest star in Taurus and generally the fourteenth-brightest star in the night sky, though it varies slowly in brightness between magnitude 0.75 and 0.95. Aldebaran is believed to host a planet several times the mass of Jupiter, named Aldebaran b. Aldebaran is a red giant, cooler than the sun with a surface temperature of 3,900 K, but its radius is about 44 times the sun\'s, so it is over 400 times as luminous. It spins slowly and takes 520 days to complete a rotation. The planetary exploration probe Pioneer 10 is heading in the general direction of the star and should make its closest approach in about two million years.\n\nNomenclature\nThe traditional name Aldebaran derives from the Arabic al Dabarān, meaning "the follower", because it seems to follow the Pleiades. In 2016, the I... '
  firstSentence : 'Aldebaran , designated α Tauri (Latinized to Alpha Tauri, abbreviated Alpha Tau, α Tau), is an orange giant star measured to be about 65 light-years from the Sun in the zodiac constellation Taurus.'
  lastSentence : '* Daytime occultation of Aldebaran by the Moon (Moscow, Russia) YouTube video'
```

THe second document reads:

```python
print(doc2)
```

```console
(nif:Context) uri = <http://dbpedia.org/resource/Antares?dbpv=2020-07&nif=context>
  sourceUrl : <http://en.wikipedia.org/wiki/Antares?oldid=964919229&ns=0>
  predLang : <http://lexvo.org/id/iso639-3/eng>
  isString : 'Antares , designated α Scorpii (Latinised to Alpha Scorpii, abbreviated Alpha Sco, α Sco), is on average the fifteenth-brightest star in the night sky, and the brightest object in the constellation of Scorpius. Distinctly reddish when viewed with the naked eye, Antares is a slow irregular variable star that ranges in brightness from apparent magnitude +0.6 to +1.6. Often referred to as "the heart of the scorpion", Antares is flanked by σ Scorpii and τ Scorpii near the center of the constellation. Classified as spectral type M1.5Iab-Ib, Antares is a red supergiant, a large evolved massive star and one of the largest stars visible to the naked eye. Its exact size remains uncertain, but if placed at the center of the Solar System, it would reach to somewhere between the orbits of Mars and Jupiter. Its mass is calculated to be around 12 times that of the Sun. Antares is the brightest, most massive, and most evolved stellar member of the nearest OB association, the Scorpius–Centaurus Associ... '
  firstSentence : 'Antares , designated α Scorpii (Latinised to Alpha Scorpii, abbreviated Alpha Sco, α Sco), is on average the fifteenth-brightest star in the night sky, and the brightest object in the constellation of Scorpius.'
  lastSentence : '* Best Ever Image of a Star’s Surface and Atmosphere - First map of motion of material on a star other than the Sun'
```


## Extract vectors from graph database


Then we need a function to extract from an arbitrary string the phrases and create a dictionary with the phrase in the sentence and their contexts.


## Find similar sentences

For sentences similarities we sum the contexts of the all the phrases in the sentences, thereby obtaining a multiset representation of the sentence. Then we calculate the Jaccard distance between the sentences and sort with increasing distance.

The Jaccard index is

```{math}
J(A, B) = \frac { | A \bigcap B |} { |A \bigcup B| }
```


Create a vector of every sentences of both documents.


```python
from nifigator.multisets import merge_multiset
from nifigator import document_vector

# setup dictionary with sentences and their vector representation
doc1_vector = {
    sent.anchorOf: document_vector(
        {sent.uri: sent.anchorOf}, 
        v_phrases,
        merge_dict=True
    )
    for sent in doc1.sentences
}
doc2_vector = {
    sent.anchorOf: document_vector(
        {sent.uri: sent.anchorOf}, 
        v_phrases,
        merge_dict=True,
    )
    for sent in doc2.sentences
}
```

Calculate the distances (based on Jaccard index) of all sentence combinations of first and second document.


```python
from nifigator.multisets import jaccard_index, merge_multiset

# Calculate the Jaccard distance for all sentence combinations
d = {
    (s1, s2): 1 - jaccard_index(c1, c2)
    for s1, c1 in doc1_vector.items()
    for s2, c2 in doc2_vector.items()
}
# Sort the results with lowest distance
similarities = sorted(d.items(), key=lambda item: item[1])
```

Print the results


```python
# print the results
for item in similarities[0:5]:
    print(repr(item[0][0]) + " \n<- distance = "+str(item[1])+' = {0:.4f}'.format(float(item[1]))+" ->\n"+repr(item[0][1])+"\n")
```


```console
'References' 
<- distance = 0 = 0.0000 ->
'References'

'External links' 
<- distance = 0 = 0.0000 ->
'External links'

'It is a variable star listed in the General Catalogue of Variable Stars, but it is listed using its Bayer designation and does not have a separate variable star designation.' 
<- distance = 25/96 = 0.2604 ->
'Antares is a variable star and is listed in the General Catalogue of Variable Stars but as a Bayer-designated star it does not have a separate variable star designation.'

'In 2016, the International Astronomical Union Working Group on Star Names (WGSN) approved the proper name Aldebaran for this star.' 
<- distance = 129/349 = 0.3696 ->
'In 2016, the International Astronomical Union organised a Working Group on Star Names (WGSN) to catalog and standardise proper names for stars.'

'Aldebaran is the brightest star in the constellation Taurus and so has the Bayer designation α Tauri, Latinised as Alpha Tauri.' 
<- distance = 116/201 = 0.5771 ->
"Nomenclature\nα Scorpii (Latinised to Alpha Scorpii) is the star's Bayer designation."

```


### Explainable text search


Now some text search examples.

For text search we need another distance function. Now we are interested in the extent to which a sentence contains the contexts of a text. For this we use the containment or support, defined by the cardinality of the intersection between A and B divided by the cardinality of A. 

```{math}
containment(A, B) = \frac { | A \bigcap B |} { |A| }
```

The sentence with the highest support has the most contexts in common and thus is the closest to the text.

```python
# setup dictionary with sentences and their contexts
v_doc_phrases = {
    sent.anchorOf: document_vector({sent.uri: sent.anchorOf}, v_phrases, topn=15)
    for sent in doc1.sentences+doc2.sentences
}
v_doc_lemmas = {
    sent.anchorOf: document_vector({sent.uri: sent.anchorOf}, v_lemmas, topn=15)
    for sent in doc1.sentences+doc2.sentences
}
```

Create a vector of every sentence in all documents.



```python
# d = vector_search(
#     query="The brightest star in the constellation of Taurus",
#     v_phrases=v_phrases,
#     v_lemmas=v_lemmas,
#     v_doc_phrases=v_doc_phrases,
#     v_doc_lemmas=v_doc_lemmas,
#     topn=15,
# )
# show_search_results(d)
```

```console
'Aldebaran is the brightest star in the constellation Taurus and so has the Bayer designation α Tauri, Latinised as Alpha Tauri.'
distance = 16/81 = 0.19753086419753085
exact similarities:
  ('brightest star in the constellation', 'brightest star in the constellation') = 0
  ('star in the constellation', 'star in the constellation') = 0
  ('Taurus', 'Taurus') = 0
other similarities:
  'brightest' -> 'brightest' (0.2667)
  'brightest star' -> 'brightest star' (0.2667), 'star' (0.9333), 'constellation' (0.9333)
  'constellation' -> 'constellation' (0.2000), 'star' (0.8667), 'designation' (0.8667)
  'star' -> 'star' (0.4000), 'Aldebaran' (0.8333), 'constellation' (0.8667)

"It is the brightest star in Taurus and generally the fourteenth-brightest star in the night sky, though it varies slowly in brightness between magnitude 0.75 and 0.95. Aldebaran is believed to host a planet several times the mass of Jupiter, named Aldebaran b. Aldebaran is a red giant, cooler than the sun with a surface temperature of 3,900 K, but its radius is about 44 times the sun's, so it is over 400 times as luminous."
distance = 25/81 = 0.30864197530864196
exact similarities:
  ('star in the constellation', 'star in the night sky') = 0
  ('Taurus', 'Taurus') = 0
other similarities:
  'brightest' -> 'brightest' (0.2667), 'luminous' (0.9333)
  'brightest star' -> 'brightest star' (0.2667), 'planet' (0.8667), 'star' (0.9333)
  'brightest star in the constellation' -> 'mass of Jupiter' (0.7143), 'night' (0.8000), 'planet' (0.8000)
  'constellation' -> 'sky' (0.7333), 'sun' (0.7333), 'planet' (0.8000)
  'star' -> 'star' (0.4000), 'mass of Jupiter' (0.7143), 'planet' (0.7333)

'As the brightest star in a Zodiac constellation, it is also given great significance within astrology.'
distance = 37/81 = 0.4567901234567901
exact similarities:
other similarities:
  'star' -> 'Zodiac' (0.3333), 'star' (0.4000), 'constellation' (0.8667)
  'brightest star in the constellation' -> 'Zodiac' (0.5000), 'star' (0.8667), 'constellation' (0.8667)
  'Taurus' -> 'astrology' (0.8667)
  'brightest' -> 'brightest' (0.2667), 'great' (0.9333)
  'brightest star' -> 'brightest star' (0.2667), 'Zodiac' (0.8333), 'star' (0.9333)
  'constellation' -> 'constellation' (0.2000), 'Zodiac' (0.6667), 'star' (0.8667)
```

```python
# # reformulation with cluster instead of constellation and Sun instead of brightest star
# d = vector_search(
#     query="the sun in the Taurus cluster",
#     v_phrases=v_phrases,
#     v_lemmas=v_lemmas,
#     v_doc_phrases=v_doc_phrases,
#     v_doc_lemmas=v_doc_lemmas,
#     topn=15,
# )
# show_search_results(d)
```
```console
"It is the brightest star in Taurus and generally the fourteenth-brightest star in the night sky, though it varies slowly in brightness between magnitude 0.75 and 0.95. Aldebaran is believed to host a planet several times the mass of Jupiter, named Aldebaran b. Aldebaran is a red giant, cooler than the sun with a surface temperature of 3,900 K, but its radius is about 44 times the sun's, so it is over 400 times as luminous."
distance = 11/43 = 0.2558139534883721
exact similarities:
  ('sun', 'sun') = 0
  ('Taurus', 'Taurus') = 0
other similarities:
  'cluster' -> 'star' (0.8000), 'planet' (0.8000), 'radius' (0.8000)

'Aldebaran , designated α Tauri (Latinized to Alpha Tauri, abbreviated Alpha Tau, α Tau), is an orange giant star measured to be about 65 light-years from the Sun in the zodiac constellation Taurus.'
distance = 14/43 = 0.32558139534883723
exact similarities:
  ('Taurus', 'Taurus') = 0
other similarities:
  'sun' -> 'Sun' (0.2667), 'zodiac' (0.7333), 'constellation' (0.7333)
  'cluster' -> 'star' (0.8000), 'constellation' (0.8000), 'Sun' (0.8667)

'Aldebaran is the brightest star in the constellation Taurus and so has the Bayer designation α Tauri, Latinised as Alpha Tauri.'
distance = 20/43 = 0.46511627906976744
exact similarities:
  ('Taurus', 'Taurus') = 0
other similarities:
  'cluster' -> 'brightest star in the constellation' (0.6667), 'Bayer designation' (0.7500), 'star' (0.8000)
  'sun' -> 'brightest star in the constellation' (0.6667), 'constellation' (0.7333), 'brightest star' (0.9333)
```

```python
# d = vector_search(
#     query="What did astronomer William Herschel discover to Aldebaran?",
#     v_phrases=v_phrases,
#     v_lemmas=v_lemmas,
#     v_doc_phrases=v_doc_phrases,
#     v_doc_lemmas=v_doc_lemmas,
#     topn=15,
# )
# show_search_results(d)
```

```console
'English astronomer William Herschel discovered a faint companion to Aldebaran in 1782; an 11th magnitude star at an angular separation of 117″.'
distance = 43/99 = 0.43434343434343436
exact similarities:
  ('astronomer', 'astronomer') = 0
  ('William', 'William') = 0
  ('William Herschel', 'William Herschel') = 0
  ('Herschel', 'Herschel') = 0
  ('Aldebaran', 'Aldebaran') = 0
other similarities:
  'discover' -> 'discovered' (0.1333)

'It was then observed by Scottish astronomer James William Grant FRSE while in India on 23 July 1844.'
distance = 53/99 = 0.5353535353535354
exact similarities:
  ('astronomer', 'astronomer') = 0
  ('William', 'William') = 0
other similarities:
  'What' -> 'It' (0.9333)
  'Aldebaran' -> 'It' (0.9333), 'India' (0.9333), '1844' (0.9333)
  'Herschel' -> 'It was' (0.9333)
  'What did' -> 'It was then' (0.9091), 'It was' (0.9333)
  'discover' -> 'observed' (0.7333)
  'did' -> 'was' (0.9333)

'English astronomer Edmund Halley studied the timing of this event, and in 1718 concluded that Aldebaran must have changed position since that time, moving several minutes of arc further to the north.'
distance = 7/11 = 0.6363636363636364
exact similarities:
  ('astronomer', 'astronomer') = 0
  ('Aldebaran', 'Aldebaran') = 0
other similarities:
  'What' -> '1718' (0.8571), 'this event' (0.8667), 'moving' (0.9333)
  'What did' -> 'concluded that' (0.9333), 'that' (0.9333)
  'discover' -> 'studied' (0.8667), 'concluded' (0.8667), 'have changed' (0.9231)
  'William' -> 'timing' (0.9333), 'several' (0.9333)
```


### Applying the minHash algorithm with LSH (Locality Sensitive Hashing)

```python
# from nifigator import MinHashSearch

# mhs = MinHashSearch(
#     vectors=v_lemmas,
#     documents=v_doc_lemmas
# )
```

```python
# import pickle 

# with open('..\\data\\minhash.pickle', 'wb') as fh:
#     pickle.dump(mhs.minhash_dict, fh)
```

```python
with open('..\\data\\minhash.pickle', 'rb') as fh:
    minhash_dict = pickle.load(fh)
```

```python
from nifigator import MinHashSearch

mhs = MinHashSearch(
    base_vectors=v_lemmas,
    minhash_dict=minhash_dict,
    documents=v_doc_lemmas,
)
```

```python
from nifigator import jaccard_index

s1 = 'large'
s2 = 'small'
print("estimated Jaccard index: "+str(mhs.minhash_dict[s2].jaccard(mhs.minhash_dict[s1])))
print("actual Jaccard index: "+str(float(jaccard_index(
    set(p[0] for p in v_phrases[s1].most_common(15)),
    set(p[0] for p in v_phrases[s2].most_common(15)),
))))
```

```console
estimated Jaccard index: 0.375
actual Jaccard index: 0.36363636363636365
```

```python
s1 = 'was'
s2 = 'be'
print("estimated Jaccard index: "+str(mhs.minhash_dict[s2].jaccard(mhs.minhash_dict[s1])))
print("actual Jaccard index: "+str(float(jaccard_index(
    set(p[0] for p in v_lemmas[s1].most_common(15)),
    set(p[0] for p in v_lemmas[s2].most_common(15)),
))))
```

```console
estimated Jaccard index: 1.0
actual Jaccard index: 1.0
```

```python
s1 = 'Antares is a variable star and is listed in the General Catalogue of Variable Stars but as a Bayer-designated star it does not have a separate variable star designation.'
s2 = 'It is a variable star listed in the General Catalogue of Variable Stars, but it is listed using its Bayer designation and does not have a separate variable star designation.'

print("estimated Jaccard index: "+str(mhs.minhash_documents[s2].jaccard(mhs.minhash_documents[s1])))
print("actual Jaccard index: "+str(float(jaccard_index(
    merge_multiset(v_doc_phrases[s1]).keys(),
    merge_multiset(v_doc_phrases[s2]).keys()
))))
```

```console
estimated Jaccard index: 0.2890625
actual Jaccard index: 0.26041666666666663
```

```python
query = "The brightest star in the constellation of Taurus"
scores = mhs.get_scores(query)
for item, distance in list(scores.items())[0:3]:
    print(repr(item) +': {0:.4f}'.format(float(distance)))
    print(len(scores))
```

```console
'Aldebaran is the brightest star in the constellation Taurus and so has the Bayer designation α Tauri, Latinised as Alpha Tauri.': 0.0000
38
"It is the brightest star in Taurus and generally the fourteenth-brightest star in the night sky, though it varies slowly in brightness between magnitude 0.75 and 0.95. Aldebaran is believed to host a planet several times the mass of Jupiter, named Aldebaran b. Aldebaran is a red giant, cooler than the sun with a surface temperature of 3,900 K, but its radius is about 44 times the sun's, so it is over 400 times as luminous.": 0.1728
38
'As the brightest star in a Zodiac constellation, it is also given great significance within astrology.': 0.2593
```

```python
query = "the sun in the Taurus cluster"
scores = mhs.get_scores(query)
for item, distance in list(scores.items())[0:3]:
    print(repr(item) +': {0:.4f}'.format(float(distance)))
```

```console
"It is the brightest star in Taurus and generally the fourteenth-brightest star in the night sky, though it varies slowly in brightness between magnitude 0.75 and 0.95. Aldebaran is believed to host a planet several times the mass of Jupiter, named Aldebaran b. Aldebaran is a red giant, cooler than the sun with a surface temperature of 3,900 K, but its radius is about 44 times the sun's, so it is over 400 times as luminous.": 0.2381
'Aldebaran , designated α Tauri (Latinized to Alpha Tauri, abbreviated Alpha Tau, α Tau), is an orange giant star measured to be about 65 light-years from the Sun in the zodiac constellation Taurus.': 0.3095
'Aldebaran is the brightest star in the constellation Taurus and so has the Bayer designation α Tauri, Latinised as Alpha Tauri.': 0.4286
```

```python
query = "astronomer reveal to Aldebaran?"
scores = mhs.get_scores(query)
for item, distance in list(scores.items())[0:3]:
    print(repr(item) +': {0:.4f}'.format(float(distance)))
```

```console
'English astronomer William Herschel discovered a faint companion to Aldebaran in 1782; an 11th magnitude star at an angular separation of 117″.': 0.4228
"Follow on measurements of proper motion showed that Herschel's companion was diverging from Aldebaran, and hence they were not physically connected.": 0.7236
'English astronomer Edmund Halley studied the timing of this event, and in 1718 concluded that Aldebaran must have changed position since that time, moving several minutes of arc further to the north.': 0.7236

```

```python
from nifigator import MinHashSearchResult

i = mhs.matches(
   "astronomer William Herschel reveal to Aldebaran",
   'English astronomer William Herschel discovered a faint companion to Aldebaran in 1782; an 11th magnitude star at an angular separation of 117″.'
)
print("Score: "+str(i.score))
print("Full matches:")
for key, values in i.full_matches.items():
    for value in values:
        print((key, value[0], "{0:.4f}".format(float(value[1]))))
print("Close matches:")
for key, values in i.close_matches.items():
    for value in values:
        print((key, value[0], "{0:.4f}".format(float(value[1]))))

```

```python
i
```

```python
# contexts = g.contexts
```

```python
# from nifigator import document_vector

# v_doc_phrases = dict()
# v_doc_lemmas = dict()
# for context in contexts[0:2]:
#     # setup dictionary with sentences and their contexts
#     v_doc_phrases.update({
#         sent.anchorOf: document_vector({sent.uri: sent.anchorOf}, v_phrases, topn=15)
#         for sent in context.sentences
#     })
#     v_doc_lemmas.update({
#         sent.anchorOf: document_vector({sent.uri: sent.anchorOf}, v_lemmas, topn=15)
#         for sent in context.sentences
#     })
```

```python

```

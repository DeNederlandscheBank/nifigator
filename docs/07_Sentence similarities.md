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


## Setup database and load DBpedia data


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


Import the vector representations of the phrases, lemmas and contexts


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


## Explainable text search


For text search we need another distance function. Now we are interested in the extent to which the vector of a sentence contains the vector representation of a query. For this we use the containment or support, defined by the cardinality of the intersection between A and B divided by the cardinality of A.

```{math}
containment(A, B) = \frac { | A \bigcap B |} { |A| }
```

The sentence with the highest containment has the most contexts in common and thus is the closest to the text.

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


### Using the MinHashSearch 


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
estimated Jaccard index: 0.6953125
actual Jaccard index: 0.7395833333333334
```

```python
query = "The brightest star in the constellation of Taurus"
scores = mhs.get_scores(query)
for item, distance in list(scores.items())[0:3]:
    print(repr(item) +': {0:.4f}'.format(float(distance)))
```

```console
'Aldebaran is the brightest star in the constellation Taurus and so has the Bayer designation α Tauri, Latinised as Alpha Tauri.': 0.0000
"It is the brightest star in Taurus and generally the fourteenth-brightest star in the night sky, though it varies slowly in brightness between magnitude 0.75 and 0.95. Aldebaran is believed to host a planet several times the mass of Jupiter, named Aldebaran b. Aldebaran is a red giant, cooler than the sun with a surface temperature of 3,900 K, but its radius is about 44 times the sun's, so it is over 400 times as luminous.": 0.1728
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
query = "astronomer William Herschel reveal to Aldebaran"
scores = mhs.get_scores(query)
for item, distance in list(scores.items())[0:3]:
    print(repr(item) +': {0:.4f}'.format(float(distance)))
```

```console
'English astronomer William Herschel discovered a faint companion to Aldebaran in 1782; an 11th magnitude star at an angular separation of 117″.': 0.1594
'It was then observed by Scottish astronomer James William Grant FRSE while in India on 23 July 1844.': 0.4348
'English astronomer Edmund Halley studied the timing of this event, and in 1718 concluded that Aldebaran must have changed position since that time, moving several minutes of arc further to the north.': 0.5797
```

```python
i = mhs.matches(
   "astronomer William Herschel reveal to Aldebaran",
   'English astronomer William Herschel discovered a faint companion to Aldebaran in 1782; an 11th magnitude star at an angular separation of 117″.'
)
print("Score: "+str(i.score))
print("Full matches:")
for key, values in i.full_matches.items():
    for value in values:
        print((key, value[0]))
print("Close matches:")
for key, values in i.close_matches.items():
    for value in values:
        print((key, value[0], "{0:.4f}".format(float(value[1]))))

```

```console
Score: 11/69
Full matches:
('astronomer', 'astronomer')
('William', 'William')
('William Herschel', 'William Herschel')
('Herschel', 'Herschel')
('Aldebaran', 'Aldebaran')
Close matches:
('reveal', 'discovered', '0.7333')
```

```python

```

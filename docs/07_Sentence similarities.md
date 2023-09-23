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

# Sentence similarities and text search


This shows an example how to use the vectors to find sentence similarities and to search in text given a text query.

The vector representation of a sentence is simply the union of the vectors of the phrases (and possibly contexts) in the sentence, similar to adding vector embeddings of the words in a sentence to calculate the sentence vector embeddings.


## Load and set up two DBpedia pages

First we connect to the database

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
g = NifVectorGraph(
    store=store,
    identifier=URIRef("https://mangosaurus.eu/dbpedia")
)
```

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


To speed up the process we construct a dictionary with the vectors of phrases and contexts.

```python
from nifigator import preprocess
# setup a dictionary with phrases and their contexts to speed up
phrase_vectors = g.load_vectors(
    documents={'doc1': doc1.isString, 'doc2': doc2.isString},
    includeOtherForms=False
)
```

Then we need a function to extract from an arbitrary string the phrases and create a dictionary with the phrase in the sentence and their contexts.


## Find similar sentences

For sentences similarities we sum the contexts of the all the phrases in the sentences, thereby obtaining a multiset representation of the sentence. Then we calculate the Jaccard distance between the sentences and sort with increasing distance.

The Jaccard index is

```{math}
J(A, B) = \frac { | A \bigcap B |} { |A \bigcup B| }
```


Create a vector of every sentences of both documents.


```python
from nifigator.set_math import merge_multiset
from nifigator import document_vector

# setup dictionary with sentences and their contexts
doc1_vector = {
    sent.anchorOf: document_vector({sent.uri: sent.anchorOf}, phrase_vectors, merge_dict=True)
    for sent in doc1.sentences
}
doc2_vector = {
    sent.anchorOf: document_vector({sent.uri: sent.anchorOf}, phrase_vectors, merge_dict=True)
    for sent in doc2.sentences
}
```

Calculate the distances (based on Jaccard index) of all sentence combinations of first and second document.


```python
from nifigator.set_math import jaccard_index, merge_multiset

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
for item in similarities[0:6]:
    print(repr(item[0][0]) + " \n<- distance = "+str(item[1])+' = {0:.4f}'.format(float(item[1]))+" ->\n"+repr(item[0][1])+"\n")
```


```console
'External links' 
<- distance = 0 = 0.0000 ->
'External links'

'It is a variable star listed in the General Catalogue of Variable Stars, but it is listed using its Bayer designation and does not have a separate variable star designation.' 
<- distance = 103/432 = 0.2384 ->
'Antares is a variable star and is listed in the General Catalogue of Variable Stars but as a Bayer-designated star it does not have a separate variable star designation.'

'In 2016, the International Astronomical Union Working Group on Star Names (WGSN) approved the proper name Aldebaran for this star.' 
<- distance = 131/380 = 0.3447 ->
'In 2016, the International Astronomical Union organised a Working Group on Star Names (WGSN) to catalog and standardise proper names for stars.'

'Aldebaran is 5.47 degrees south of the ecliptic and so can be occulted by the Moon.' 
<- distance = 34/59 = 0.5763 ->
'Occultations and conjunctions\nAntares is 4.57 degrees south of the ecliptic, one of four first magnitude stars within 6° of the ecliptic (the others are Spica, Regulus and Aldebaran), so it can be occulted by the Moon.'

'Aldebaran is the brightest star in the constellation Taurus and so has the Bayer designation α Tauri, Latinised as Alpha Tauri.' 
<- distance = 7/12 = 0.5833 ->
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
lemma_vectors = g.load_vectors( 
    documents={'doc1': doc1.isString, 'doc2': doc2.isString},
    includeOtherForms=True,
)
```
```python
phrase_vectors['is'] <= lemma_vectors['is']
```

```python
lemma_vectors['larger'] <= lemma_vectors['large']
```

```python
c = [c[0] for c in (lemma_vectors['star'] - (phrase_vectors['stars'])).most_common(15)]
```

```python
g.most_similar(contexts=c)
```

```python
phrase_vectors['is']
```

```python
# containment_index(lemma_vectors['is'], phrase_vectors['is'])
```

```python
# setup dictionary with sentences and their contexts
doc_vectors = {
    sent.anchorOf: document_vector({sent.uri: sent.anchorOf}, phrase_vectors)
    for sent in doc1.sentences+doc2.sentences
}
```

```python
from nifigator import containment_index
from collections import Counter

def search(query: str=None, 
           doc_vectors: dict=None, 
           lemma_vectors: dict={}
    ):
    """
    """
    # make sure that all phrases in the text have contexts available
    lemma_vectors = g.load_vectors(
        documents={'query': query},
        vectors=lemma_vectors,
        includeOtherForms=True
    )
    # generate contexts of the text
    phrases_1 = document_vector({'query': query}, lemma_vectors)
    d = {}
    for sent, phrases_2 in doc_vectors.items():

        # find the full phrase matches of the text and the sentence
        full_matches = [
            (p1, p2)
            for p1, c1 in phrases_1.items()
            for p2, c2 in phrases_2.items()
            if c2 <= c1 and c2 != Counter()
        ]
        # find the close phrase matches of the text and the sentence
        close_matches = {
                    p1: [(p2, 1 - containment_index(c2, c1))
                    for p2, c2 in phrases_2.items()
                    if 1 - containment_index(c2, c1) < 1 and 
                       p1 not in [p[0] for p in full_matches] and 
                       p2 not in [p[1] for p in full_matches]]
                    for p1, c1 in phrases_1.items()
        }
        close_matches = {key: sorted(value, key=lambda item: item[1]) for key, value in close_matches.items() if value!=[]}
        close_matches = dict(sorted(close_matches.items(), key=lambda item: item[1]))
        
        # calculate the containment index
        c1 = merge_multiset(phrases_1)
        c2 = merge_multiset(phrases_2)
        containment = containment_index(c1, c2)
        d[sent] = (1 - containment, (full_matches, close_matches))
            
    d = dict(sorted(d.items(), key=lambda item: item[1][0]))
    return d
```


Create a vector of every sentence in all documents.



```python
query = "The brightest star in the constellation of Taurus"
d = search(
    query=query,
    doc_vectors=doc_vectors,
    lemma_vectors=lemma_vectors,
)
for i in list(d.items())[0:3]:
    print(repr(i[0]))
    print("distance = " +str(i[1][0]) + " = "+str(float(i[1][0])))
    print("exact similarities:")
    for j in i[1][1][0]:
        print("  " +str(j)+' = 0')
    print("other similarities:")
    for j in i[1][1][1:]:
        for key, value in j.items():
            for row in value:
                print(key+": "+str(row))
    print("")
```

```console
'Aldebaran is the brightest star in the constellation Taurus and so has the Bayer designation α Tauri, Latinised as Alpha Tauri.'
distance = 0 = 0.0
exact similarities:
  ('brightest', 'brightest') = 0
  ('brightest+star', 'brightest+star') = 0
  ('star', 'star') = 0
  ('constellation', 'constellation') = 0
  ('Taurus', 'Taurus') = 0
other similarities:

"It is the brightest star in Taurus and generally the fourteenth-brightest star in the night sky, though it varies slowly in brightness between magnitude 0.75 and 0.95. Aldebaran is believed to host a planet several times the mass of Jupiter, named Aldebaran b. Aldebaran is a red giant, cooler than the sun with a surface temperature of 3,900 K, but its radius is about 44 times the sun's, so it is over 400 times as luminous."
distance = 1/6 = 0.16666666666666666
exact similarities:
  ('brightest', 'brightest') = 0
  ('brightest+star', 'brightest+star') = 0
  ('star', 'star') = 0
  ('Taurus', 'Taurus') = 0
other similarities:
  ('constellation', 'night') = 0.9286
  ('constellation', 'night+sky') = 0.9286
  ('constellation', 'sky') = 0.9286
  ('constellation', 'surface') = 0.9286
  ('constellation', 'radius') = 0.9286
  ('constellation', 'brightness') = 0.9655
  ('constellation', 'magnitude') = 0.9655
  ('constellation', 'host') = 0.9655
  ('constellation', 'planet') = 0.9655
  ('constellation', 'mass') = 0.9655
  ('constellation', 'sun') = 0.9655
  ('constellation', 'temperature') = 0.9655

'As the brightest star in a Zodiac constellation, it is also given great significance within astrology.'
distance = 13/72 = 0.18055555555555555
exact similarities:
  ('brightest', 'brightest') = 0
  ('brightest+star', 'brightest+star') = 0
  ('star', 'star') = 0
  ('constellation', 'constellation') = 0
other similarities:
  ('Taurus', 'astrology') = 0.9643
```

```python
# reformulation with cluster instead of constellation and Sun instead of brightest star
query = "the sun in the Taurus cluster"
d = search(
    query=query,
    doc_vectors=doc_vectors,
    lemma_vectors=lemma_vectors,
)
for i in list(d.items())[0:4]:
    print(repr(i[0]))
    print("distance = " +str(i[1][0]) + " = "+str(float(i[1][0])))
    print("exact similarities:")
    for j in i[1][1][0]:
        print("  " +str(j)+' = 0')
    print("other similarities:")
    for j in i[1][1][1:]:
        for key, value in j.items():
            for row in value:
                print(key+": "+str(row))
    print("")
```
```console
"It is the brightest star in Taurus and generally the fourteenth-brightest star in the night sky, though it varies slowly in brightness between magnitude 0.75 and 0.95. Aldebaran is believed to host a planet several times the mass of Jupiter, named Aldebaran b. Aldebaran is a red giant, cooler than the sun with a surface temperature of 3,900 K, but its radius is about 44 times the sun's, so it is over 400 times as luminous."
distance = 11/42 = 0.2619
exact similarities:
  ('sun', 'sun') = 0
  ('Taurus', 'Taurus') = 0
other similarities:
  ('cluster', 'star') = 0.9286
  ('cluster', 'sky') = 0.9286
  ('cluster', 'planet') = 0.9286
  ('cluster', 'radius') = 0.9286
  ('cluster', 'red+giant') = 0.9524
  ('cluster', 'surface+temperature') = 0.9615
  ('cluster', 'night') = 0.9655
  ('cluster', 'night+sky') = 0.9655
  ('cluster', 'magnitude') = 0.9655
  ('cluster', 'host') = 0.9655
  ('cluster', 'mass') = 0.9655
  ('cluster', 'surface') = 0.9655
  ('cluster', 'temperature') = 0.9655
  ('cluster', 'luminous') = 0.9655

'Aldebaran , designated α Tauri (Latinized to Alpha Tauri, abbreviated Alpha Tau, α Tau), is an orange giant star measured to be about 65 light-years from the Sun in the zodiac constellation Taurus.'
distance = 10/21 = 0.4762
exact similarities:
  ('Taurus', 'Taurus') = 0
other similarities:
  ('sun', 'Sun') = 0.6957
  ('sun', 'zodiac') = 0.8095
  ('cluster', 'zodiac') = 0.9130
  ('cluster', 'star') = 0.9286
  ('cluster', 'Sun') = 0.9286
  ('sun', 'star') = 0.9655
  ('sun', 'light') = 0.9655
  ('sun', 'years') = 0.9655
  ('sun', 'constellation') = 0.9655
  ('cluster', 'years') = 0.9655
  ('cluster', 'constellation') = 0.9655

"The star is, by chance, in the line of sight between the Earth and the Hyades, so it has the appearance of being the brightest member of the open cluster, but the cluster that forms the bull's-head-shaped asterism is more than twice as far away, at about 150 light years."
distance = 23/42 = 0.5476
exact similarities:
  ('cluster', 'cluster') = 0
other similarities:
  ('sun', 'Earth') = 0.8462
  ('sun', 'line') = 0.8889
  ('sun', 'head') = 0.9286
  ('Taurus', 'light') = 0.9643
  ('sun', 'star') = 0.9655
  ('sun', 'chance') = 0.9655
  ('sun', 'bull') = 0.9655
  ('sun', 'light') = 0.9655
  ('sun', 'years') = 0.9655
```

```python
query = "What did astronomer Herschel discover to Aldebaran?"
d = search(
    query=query,
    doc_vectors=doc_vectors,
    lemma_vectors=lemma_vectors,
)
for i in list(d.items())[0:4]:
    print(repr(i[0]))
    print("distance = " +str(i[1][0]) + " = "+str(float(i[1][0])))
    print("exact similarities:")
    for j in i[1][1][0]:
        print("  " +str(j)+' = 0')
    print("other similarities:")
    for j in i[1][1][1:]:
        for key, value in j.items():
            for row in value:
                print(key+": "+str(row))
    print("")
```

```console
'English astronomer William Herschel discovered a faint companion to Aldebaran in 1782; an 11th magnitude star at an angular separation of 117″.'
distance = 229/297 = 0.7710
exact similarities:
  ('astronomer', 'astronomer') = 0
  ('William', 'William') = 0
  ('Herschel', 'Herschel') = 0
  ('Aldebaran', 'Aldebaran') = 0
other similarities:
  ('discover', 'discovered') = 0.8214
  ('did', 'discovered') = 0.9863

'Working at his private observatory in Tulse Hill, England, in 1864 William Huggins performed the first studies of the spectrum of Aldebaran, where he was able to identify the lines of nine elements, including iron, sodium, calcium, and magnesium.'
distance = 9/11 = 0.8182
exact similarities:
  ('William', 'William') = 0
  ('Aldebaran', 'Aldebaran') = 0
other similarities:
  ('did', 'performed') = 0.9504
  ('discover', 'performed') = 0.9579
  ('discover', 'identify') = 0.9688
  ('What', 'where+he') = 0.9773
  ('What', 'iron') = 0.9773
  ('What', 'calcium') = 0.9773
  ('did', 'identify') = 0.9793
  ('did', 'he+was') = 0.9863
  ('did', 'able') = 0.9863
  ('discover', 'Working') = 0.9898
  ('discover', 'where') = 0.9898
  ('discover', 'he+was') = 0.9898
  ('discover', 'lines') = 0.9898
  ('discover', 'including') = 0.9898
  ('did', 'England') = 0.9932
  ('did', 'was') = 0.9932

'It was then observed by Scottish astronomer James William Grant FRSE while in India on 23 July 1844.'
distance = 245/297 = 0.8249
exact similarities:
  ('astronomer', 'astronomer') = 0
  ('William', 'William') = 0
other similarities:
  ('What', 'It') = 0.9024
  ('discover', 'observed') = 0.9468
  ('What', 'It+was') = 0.9535
  ('What+did', 'It+was') = 0.9545
  ('did', 'observed') = 0.9577
  ('Aldebaran', 'It') = 0.9655
  ('Aldebaran', 'India') = 0.9655
  ('discover', 'It+was') = 0.9794
  ('did', 'It+was') = 0.9863
  ('discover', 'was+then') = 0.9898
  ('discover', 'then') = 0.9898
  ('did', 'was') = 0.9932
  ('did', 'India') = 0.9932
```


### Applying the minHash algorithm with LSH (Locality Sensitive Hashing)

```python
from datasketch import MinHashLSHEnsemble, MinHash

num_perm = 2**8

def create_phrases_minhash_dict(
    d: dict=None,
    minhash_dict: dict={}
):
    for key, value in d.items():
        if key not in minhash_dict.keys():
            minhash_dict[key] = MinHash(
                num_perm=num_perm
            )
            for context in value.keys():
                v = str(context).encode('utf8')
                minhash_dict[key].update(v)
    return minhash_dict

def create_document_minhash_dict(
    d: dict=None, 
    phrases_minhash: dict=None,
):
    minhash_dict = dict()
    for key, value in d.items():
        minhash_dict[key] = MinHash(
            num_perm=num_perm
        )
        for phrase in value.keys():
            minhash_dict[key].merge(phrases_minhash[phrase])
    return minhash_dict

minhash_phrases = create_phrases_minhash_dict(phrase_vectors, {})
minhash_lemmas = create_phrases_minhash_dict(lemma_vectors, {})
minhash_docs = create_document_minhash_dict(doc_vector, minhash_phrases)
```

```python
s1 = 'Antares is a variable star and is listed in the General Catalogue of Variable Stars but as a Bayer-designated star it does not have a separate variable star designation.'
s2 = 'It is a variable star listed in the General Catalogue of Variable Stars, but it is listed using its Bayer designation and does not have a separate variable star designation.'
print(1 - minhash_docs[s2].jaccard(minhash_docs[s1]))
```

```python
# calculate the real Jaccard index
1 - float(jaccard_index(
    merge_multiset(doc_vector[s1]).keys(),
    merge_multiset(doc_vector[s2]).keys()
))
```

```python
num_part = 2**4

# Create an LSH Ensemble index with threshold and number of partition
lshensemble = MinHashLSHEnsemble(
    threshold=0.5, 
    num_perm=num_perm,
    num_part=num_part
)
lshensemble.index(
    [
        (key, minhash_docs[key], len(value.keys()))
        for key, value in doc_vector.items()
    ]
)
```

```python
text = "What did astronomer William Herschel discover in relation to Aldebaran?"

# make sure that all phrases in the text have contexts available
lemma_vectors = g.load_vectors(
    documents=[text], 
    vectors=lemma_vectors,
    includeOtherForms=True
)

# generate contexts of the text
phrases_1 = extract_contexts(text, lemma_vectors)

minhash_lemmas = create_phrases_minhash_dict(phrases_1, minhash_lemmas)

minhash_text = MinHash(
        num_perm=num_perm
)
for phrase in phrases_1.keys():
    minhash_text.merge(minhash_lemmas[phrase])

d = dict()
for sent in lshensemble.query(minhash_text, len(phrases_1.keys())):
    c1 = merge_multiset(phrases_1).keys()
    c2 = merge_multiset(doc_vector[sent]).keys()
    containment = containment_index(c1, c2)
    d[sent] = 1 - containment
d = dict(sorted(d.items(), key=lambda item: item[1]))

for item, distance in list(d.items())[0:50]:
    print(repr(item) +': {0:.4f}'.format(float(distance)))
```

```python

```

```python

```

```python

```

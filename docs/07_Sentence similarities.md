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



For a sentence we can take the union of the contexts of the phrases in the sentence, similar to adding the vector embeddings of the words in a sentence to calculate the sentence vector embeddings.


### Set up the graph database

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


### Extracting contexts in sentences


We take two pages from DBpedia about two stars. 

```python
# Read two documents in DBpedia about Aldebaran and Antares stars
doc_1 = g.get(
    URIRef("http://dbpedia.org/resource/Aldebaran?dbpv=2020-07&nif=context")
)
doc_2 = g.get(
    URIRef("http://dbpedia.org/resource/Antares?dbpv=2020-07&nif=context")
)
```

The first document reads:

```python
print(doc_1)
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
print(doc_2)
```

```console
(nif:Context) uri = <http://dbpedia.org/resource/Antares?dbpv=2020-07&nif=context>
  sourceUrl : <http://en.wikipedia.org/wiki/Antares?oldid=964919229&ns=0>
  predLang : <http://lexvo.org/id/iso639-3/eng>
  isString : 'Antares , designated α Scorpii (Latinised to Alpha Scorpii, abbreviated Alpha Sco, α Sco), is on average the fifteenth-brightest star in the night sky, and the brightest object in the constellation of Scorpius. Distinctly reddish when viewed with the naked eye, Antares is a slow irregular variable star that ranges in brightness from apparent magnitude +0.6 to +1.6. Often referred to as "the heart of the scorpion", Antares is flanked by σ Scorpii and τ Scorpii near the center of the constellation. Classified as spectral type M1.5Iab-Ib, Antares is a red supergiant, a large evolved massive star and one of the largest stars visible to the naked eye. Its exact size remains uncertain, but if placed at the center of the Solar System, it would reach to somewhere between the orbits of Mars and Jupiter. Its mass is calculated to be around 12 times that of the Sun. Antares is the brightest, most massive, and most evolved stellar member of the nearest OB association, the Scorpius–Centaurus Associ... '
  firstSentence : 'Antares , designated α Scorpii (Latinised to Alpha Scorpii, abbreviated Alpha Sco, α Sco), is on average the fifteenth-brightest star in the night sky, and the brightest object in the constellation of Scorpius.'
  lastSentence : '* Best Ever Image of a Star’s Surface and Atmosphere - First map of motion of material on a star other than the Sun'
```


### Extract phrase contexts from graph database


To speed up the process we construct a dictionary with phrases and their contexts.

```python
from nifigator import STOPWORDS, generate_windows

# setup a dictionary with phrases and their contexts to speed up
def load_phrase_contexts(documents: list=None, d: dict={}, topn: int=15):

    params = {"words_filter": {'data': {phrase: True for phrase in STOPWORDS}}}

    for doc in documents:

        phrases = generate_windows(
            documents={"id": doc}, 
            params=params
        ).keys()

        for phrase in phrases:
            phrase_contexts = d.get(phrase, None)
            if phrase_contexts is None:
                phrase_contexts = g.phrase_contexts(phrase, topn=topn)
                d[phrase] = phrase_contexts
    
    return d

phrase_contexts = load_phrase_contexts([doc_1.isString, doc_2.isString])
```

Then we need a function to extract from an arbitrary string the phrases and create a dictionary with the phrase in the sentence and their contexts.


```python
from collections import Counter

def sentence_contexts(s: str=None, d: dict=None):
    """
    extract the phrases of a string and create dict of phrases with their contexts
    """
    params = {"words_filter": {'data': {phrase: True for phrase in STOPWORDS}}}

    phrases = generate_windows(
        documents={"id": s}, 
        params=params
    ).keys()

    c = set()
    for phrase in phrases:
        c.update(d.get(phrase, None))
        
    return c
```


### Find similar sentences

For sentences similarities we sum the contexts of the all the phrases in the sentences, thereby obtaining a multiset representation of the sentence. Then we calculate the Jaccard distance between the sentences and sort with increasing distance.

The Jaccard index is

$J(A, B) = $ $| A \cap B | \over |A \cup B| $


```python
# setup dictionary with sentences and their contexts
doc_1_contexts = {
    sent.anchorOf: sentence_contexts(sent.anchorOf, phrase_contexts)
    for sent in doc_1.sentences
}
doc_2_contexts = {
    sent.anchorOf: sentence_contexts(sent.anchorOf, phrase_contexts)
    for sent in doc_2.sentences
}
```

```python
def jaccard_index(
    c1: set=None, 
    c2: set=None
):
    """
    Function to calculate the Jaccard index of two sets
    """
    denom = len(c1 | c2)
    if denom != 0:
        return len(c1 & c2) / denom
    else:
        return 0
```

```python
# Calculate the Jaccard distance for all sentence combinations
d = {
    (s1, s2): 1 - jaccard_index(c1, c2)
    for s1, c1 in doc_1_contexts.items()
    for s2, c2 in doc_2_contexts.items()
}
# Sort the results with lowest distance
similarities = sorted(d.items(), key=lambda item: item[1])
```

```python
for item in similarities[0:5]:
    print(repr(item[0][0]) + " \n<- distance = "+str(item[1])+" ->\n"+repr(item[0][1])+"\n")
```


```console
'External links' 
<- distance = 0.0 ->
'External links'

'It is a variable star listed in the General Catalogue of Variable Stars, but it is listed using its Bayer designation and does not have a separate variable star designation.' 
<- distance = 0.2591687041564792 ->
'Antares is a variable star and is listed in the General Catalogue of Variable Stars but as a Bayer-designated star it does not have a separate variable star designation.'

'In 2016, the International Astronomical Union Working Group on Star Names (WGSN) approved the proper name Aldebaran for this star.' 
<- distance = 0.35185185185185186 ->
'In 2016, the International Astronomical Union organised a Working Group on Star Names (WGSN) to catalog and standardise proper names for stars.'

'Aldebaran is the brightest star in the constellation Taurus and so has the Bayer designation α Tauri, Latinised as Alpha Tauri.' 
<- distance = 0.585 ->
"Nomenclature\nα Scorpii (Latinised to Alpha Scorpii) is the star's Bayer designation."

'Aldebaran is 5.47 degrees south of the ecliptic and so can be occulted by the Moon.' 
<- distance = 0.5942028985507246 ->
'Occultations and conjunctions\nAntares is 4.57 degrees south of the ecliptic, one of four first magnitude stars within 6° of the ecliptic (the others are Spica, Regulus and Aldebaran), so it can be occulted by the Moon.'

```


### Explainable text search


Now some text search examples.

For text search we need another distance function. Now we are interested in the extent to which a sentence contains the contexts of a text. For this we use the support, defined by the cardinality of the intersection between A and B divided by the cardinality of A. 

$support = $ $| A \cap B | \over |A| $
 
The sentence with the highest support has the most contexts in common and thus is the closest to the text.

```python
def extract_contexts(s: str=None, d: dict=None):
    """
    extract the phrases of a string and create dict of phrases with their contexts
    """
    params = {"words_filter": {'data': {phrase: True for phrase in STOPWORDS}}}

    phrases = generate_windows(
        documents={"id": s}, 
        params=params
    ).keys()
    
    c = dict()
    for phrase in phrases:
        c[phrase] = d.get(phrase, None)
            
    return c
```

```python
def combine(d: dict=None):
    """
    Function to calculate the multiset from a dict of phrases
    """
    x = Counter()
    for item in d.values():
        x += item
    return x
```

```python
def support_index(
    c1: set=None, 
    c2: set=None
):
    """
    Function to calculate the support of set B in set A
    """
    denom = len(c1)
    if denom != 0:
        return len(c1 & c2) / denom
    else:
        return 0
```

```python
def search(text: str=None, contexts: dict=None, phrase_contexts: dict=None):
    """
    """
    # make sure that all phrases in the text have contexts available
    phrase_contexts = load_phrase_contexts([text], phrase_contexts)

    # generate contexts of the text
    phrases_1 = extract_contexts(text, phrase_contexts)
    
    d = {}
    for sent, phrases_2 in contexts.items():
        
        # find the full phrase matches of the text and the sentence
        full_matches = [
            (p1, p2)
            for p1, c1 in phrases_1.items()
            for p2, c2 in phrases_2.items()
            if 1 - jaccard_index(c1, c2) == 0
        ]
        # find the close phrase matches of the text and the sentence
        close_matches = {
                    (p1, p2): 1 - jaccard_index(c1, c2)
                    for p1, c1 in phrases_1.items()
                    for p2, c2 in phrases_2.items()
                    if 1 - jaccard_index(c1, c2) < 1 and 
                       p1 not in [p[0] for p in full_matches] and 
                       p2 not in [p[1] for p in full_matches]
        }
        close_matches = dict(sorted(close_matches.items(), key=lambda item: item[1]))
        
        # calculate the support
        c1 = combine(phrases_1)
        c2 = combine(phrases_2)
        supp = support_index(c1, c2)
        d[sent] = (1 - supp, (full_matches, close_matches))
            
    d = dict(sorted(d.items(), key=lambda item: item[1][0]))
    return d
```

```python
# setup dictionary with sentences and their contexts
doc_contexts = {
    sent.anchorOf: extract_contexts(sent.anchorOf, phrase_contexts)
    for sent in doc_1.sentences+doc_2.sentences
}
```

```python
text = "The brightest star in the constellation of Taurus"
d = search(text, doc_contexts, phrase_contexts)
list(d.items())[0:3]
```

```console
[('Aldebaran is the brightest star in the constellation Taurus and so has the Bayer designation α Tauri, Latinised as Alpha Tauri.',
  (0.0,
   ([('brightest', 'brightest'),
     ('brightest+star', 'brightest+star'),
     ('star', 'star'),
     ('constellation', 'constellation'),
     ('Taurus', 'Taurus')],
    {}))),
 ("It is the brightest star in Taurus and generally the fourteenth-brightest star in the night sky, though it varies slowly in brightness between magnitude 0.75 and 0.95. Aldebaran is believed to host a planet several times the mass of Jupiter, named Aldebaran b. Aldebaran is a red giant, cooler than the sun with a surface temperature of 3,900 K, but its radius is about 44 times the sun's, so it is over 400 times as luminous.",
  (0.1428571428571429,
   ([('brightest', 'brightest'),
     ('brightest+star', 'brightest+star'),
     ('star', 'star'),
     ('Taurus', 'Taurus')],
    {('constellation', 'sky'): 0.8461538461538461,
     ('constellation', 'night+sky'): 0.8888888888888888,
     ('constellation', 'night'): 0.9285714285714286,
     ('constellation', 'planet'): 0.9285714285714286,
     ('constellation', 'sun'): 0.9285714285714286,
     ('constellation', 'surface'): 0.9285714285714286,
     ('constellation', 'temperature'): 0.9285714285714286,
     ('constellation', 'brightness'): 0.9655172413793104,
     ('constellation', 'magnitude'): 0.9655172413793104,
     ('constellation', 'host'): 0.9655172413793104,
     ('constellation', 'times'): 0.9655172413793104,
     ('constellation', 'mass'): 0.9655172413793104,
     ('constellation', 'radius'): 0.9655172413793104}))),
 ('As the brightest star in a Zodiac constellation, it is also given great significance within astrology.',
  (0.17142857142857137,
   ([('brightest', 'brightest'),
     ('brightest+star', 'brightest+star'),
     ('star', 'star'),
     ('constellation', 'constellation')],
    {})))]
```

```python
# reformulation with cluster instead of constellation and Sun instead of brightest star
text = "the sun in the Taurus cluster"
d = search(text, doc_contexts, phrase_contexts)
list(d.items())[0:3]
```
```console
[("It is the brightest star in Taurus and generally the fourteenth-brightest star in the night sky, though it varies slowly in brightness between magnitude 0.75 and 0.95. Aldebaran is believed to host a planet several times the mass of Jupiter, named Aldebaran b. Aldebaran is a red giant, cooler than the sun with a surface temperature of 3,900 K, but its radius is about 44 times the sun's, so it is over 400 times as luminous.",
  (0.30000000000000004,
   ([('sun', 'sun'), ('Taurus', 'Taurus')],
    {('cluster', 'star'): 0.9285714285714286,
     ('cluster', 'night+sky'): 0.9285714285714286,
     ('cluster', 'sky'): 0.9285714285714286,
     ('cluster', 'planet'): 0.9285714285714286,
     ('cluster', 'red+giant'): 0.9444444444444444,
     ('cluster', 'surface+temperature'): 0.9615384615384616,
     ('cluster', 'night'): 0.9655172413793104,
     ('cluster', 'magnitude'): 0.9655172413793104,
     ('cluster', 'host'): 0.9655172413793104,
     ('cluster', 'mass'): 0.9655172413793104,
     ('cluster', 'surface'): 0.9655172413793104,
     ('cluster', 'temperature'): 0.9655172413793104,
     ('cluster', 'radius'): 0.9655172413793104}))),
 ('Aldebaran , designated α Tauri (Latinized to Alpha Tauri, abbreviated Alpha Tau, α Tau), is an orange giant star measured to be about 65 light-years from the Sun in the zodiac constellation Taurus.',
  (0.5,
   ([('Taurus', 'Taurus')],
    {('sun', 'Sun'): 0.6956521739130435,
     ('sun', 'zodiac'): 0.8095238095238095,
     ('cluster', 'zodiac'): 0.9130434782608696,
     ('sun', 'constellation'): 0.9285714285714286,
     ('cluster', 'star'): 0.9285714285714286,
     ('cluster', 'Sun'): 0.9285714285714286,
     ('sun', 'star'): 0.9655172413793104,
     ('sun', 'years'): 0.9655172413793104,
     ('cluster', 'years'): 0.9655172413793104,
     ('cluster', 'constellation'): 0.9655172413793104}))),
 ("The star is, by chance, in the line of sight between the Earth and the Hyades, so it has the appearance of being the brightest member of the open cluster, but the cluster that forms the bull's-head-shaped asterism is more than twice as far away, at about 150 light years.",
  (0.525,
   ([('cluster', 'cluster')],
    {('sun', 'Earth'): 0.8,
     ('sun', 'line'): 0.8888888888888888,
     ('sun', 'head'): 0.9285714285714286,
     ('Taurus', 'light'): 0.9615384615384616,
     ('sun', 'star'): 0.9655172413793104,
     ('sun', 'chance'): 0.9655172413793104,
     ('sun', 'bull'): 0.9655172413793104,
     ('sun', 'years'): 0.9655172413793104})))]
```

```python
text = "What did astronomer William Herschel discover to Aldebaran?"
d = search(text, doc_contexts, phrase_contexts)
list(d.items())[0:3]
```

```console
[('English astronomer William Herschel discovered a faint companion to Aldebaran in 1782; an 11th magnitude star at an angular separation of 117″.',
  (0.48453608247422686,
   ([('astronomer', 'astronomer'),
     ('William', 'William'),
     ('Herschel', 'Herschel'),
     ('Aldebaran', 'Aldebaran')],
    {('What', 'English'): 0.9655172413793104}))),
 ('It was then observed by Scottish astronomer James William Grant FRSE while in India on 23 July 1844.',
  (0.6082474226804124,
   ([('astronomer', 'astronomer'), ('William', 'William')],
    {('What', 'It'): 0.8461538461538461,
     ('What', 'It+was'): 0.9285714285714286,
     ('did', 'was'): 0.9655172413793104,
     ('Aldebaran', 'It'): 0.9655172413793104,
     ('Aldebaran', 'India'): 0.9655172413793104}))),
 ('Working at his private observatory in Tulse Hill, England, in 1864 William Huggins performed the first studies of the spectrum of Aldebaran, where he was able to identify the lines of nine elements, including iron, sodium, calcium, and magnesium.',
  (0.6288659793814433,
   ([('William', 'William'), ('Aldebaran', 'Aldebaran')],
    {('discover', 'identify'): 0.8888888888888888,
     ('did', 'he+was'): 0.9285714285714286,
     ('did', 'was'): 0.9655172413793104})))]
```

```python

```

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

## Sentence similarities and text search


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
from nifigator import STOPWORDS, generate_phrase_context

# setup a dictionary with phrases and their contexts to speed up
def load_vectors(
    documents: list=None, 
    d: dict={}, 
    topn: int=15):

    params = {"words_filter": {'data': {phrase: True for phrase in STOPWORDS}}}

    for doc in documents:
        r = generate_phrase_context(
            document=doc, 
            params=params
        )
        for phrase, context, _ in r:
            if d.get(phrase, None) is None:
                d[phrase] = g.phrase_contexts(phrase, topn=topn)
            if d.get(context, None) is None:
                d[context] = g.context_phrases(context, topn=topn)
    return d

phrase_contexts = load_vectors([doc_1.isString, doc_2.isString])
```

Then we need a function to extract from an arbitrary string the phrases and create a dictionary with the phrase in the sentence and their contexts.


```python
from collections import Counter

def sentence_contexts(doc: str=None, d: dict=None):
    """
    extract the phrases of a string and create dict of phrases with their contexts
    """
    params = {"words_filter": {'data': {phrase: True for phrase in STOPWORDS}}}

    r = generate_phrase_context(
        document=doc, 
        params=params
    )

    c = set()
    for phrase, context, _ in r:
        c.update(d.get(phrase, set()))
#         c.update(d.get(context, set()))
        
    return c
```


### Find similar sentences

For sentences similarities we sum the contexts of the all the phrases in the sentences, thereby obtaining a multiset representation of the sentence. Then we calculate the Jaccard distance between the sentences and sort with increasing distance.

The Jaccard index is

$J(A, B) = $ $| A \bigcap B | \over |A \bigcup B| $


```python
from fractions import Fraction

def jaccard_index(
    c1: set=None, 
    c2: set=None
):
    """
    Function to calculate the Jaccard index of two sets
    """
    denom = len(c1 | c2)
    if denom != 0:
        return Fraction(len(c1 & c2), denom)
    else:
        return 0
```

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
# print the results
for item in similarities[0:5]:
    print(repr(item[0][0]) + " \n<- distance = "+str(item[1])+" = "+str(float(item[1]))+" ->\n"+repr(item[0][1])+"\n")
```


```console
'External links' 
<- distance = 0 = 0.0 ->
'External links'

'It is a variable star listed in the General Catalogue of Variable Stars, but it is listed using its Bayer designation and does not have a separate variable star designation.' 
<- distance = 106/409 = 0.2591687041564792 ->
'Antares is a variable star and is listed in the General Catalogue of Variable Stars but as a Bayer-designated star it does not have a separate variable star designation.'

'In 2016, the International Astronomical Union Working Group on Star Names (WGSN) approved the proper name Aldebaran for this star.' 
<- distance = 19/54 = 0.35185185185185186 ->
'In 2016, the International Astronomical Union organised a Working Group on Star Names (WGSN) to catalog and standardise proper names for stars.'

'Aldebaran is the brightest star in the constellation Taurus and so has the Bayer designation α Tauri, Latinised as Alpha Tauri.' 
<- distance = 117/200 = 0.585 ->
"Nomenclature\nα Scorpii (Latinised to Alpha Scorpii) is the star's Bayer designation."

'Aldebaran is 5.47 degrees south of the ecliptic and so can be occulted by the Moon.' 
<- distance = 41/69 = 0.5942028985507246 ->
'Occultations and conjunctions\nAntares is 4.57 degrees south of the ecliptic, one of four first magnitude stars within 6° of the ecliptic (the others are Spica, Regulus and Aldebaran), so it can be occulted by the Moon.'
```


### Explainable text search


Now some text search examples.

For text search we need another distance function. Now we are interested in the extent to which a sentence contains the contexts of a text. For this we use the support, defined by the cardinality of the intersection between A and B divided by the cardinality of A. 

$support = $ $| A \bigcap B | \over |A| $
 
The sentence with the highest support has the most contexts in common and thus is the closest to the text.

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
        return Fraction(len(c1 & c2), denom)
    else:
        return 0
```

```python
def extract_contexts(doc: str=None, d: dict=None):
    """
    extract the phrases of a string and create dict of phrases with their contexts
    """
    params = {"words_filter": {'data': {phrase: True for phrase in STOPWORDS}}}

    r = generate_phrase_context(
        document=doc, 
        params=params
    )

    c = dict()
    for phrase, context, _ in r:
        c[phrase] = d.get(phrase, Counter())
#         c[context] = d.get(context, Counter())
            
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
def search(text: str=None, contexts: dict=None, phrase_contexts: dict=None):
    """
    """
    # make sure that all phrases in the text have contexts available
    phrase_contexts = load_vectors([text], phrase_contexts)

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
                    if 1 - support_index(c1, c2) < 1 and 
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
for i in list(d.items())[0:3]:
    print(repr(i[0]))
    print("  distance = " +str(i[1][0]) + " = "+str(float(i[1][0])))
    for j in i[1][1][0]:
        print("  " + str(j))
    for j in i[1][1][1]:
        print("  " +str(j))        
```

```console
'Aldebaran is the brightest star in the constellation Taurus and so has the Bayer designation α Tauri, Latinised as Alpha Tauri.'
  distance = 0 = 0.0
  ('brightest', 'brightest')
  ('brightest+star', 'brightest+star')
  ('star', 'star')
  ('constellation', 'constellation')
  ('Taurus', 'Taurus')
"It is the brightest star in Taurus and generally the fourteenth-brightest star in the night sky, though it varies slowly in brightness between magnitude 0.75 and 0.95. Aldebaran is believed to host a planet several times the mass of Jupiter, named Aldebaran b. Aldebaran is a red giant, cooler than the sun with a surface temperature of 3,900 K, but its radius is about 44 times the sun's, so it is over 400 times as luminous."
  distance = 1/7 = 0.14285714285714285
  ('brightest', 'brightest')
  ('brightest+star', 'brightest+star')
  ('star', 'star')
  ('Taurus', 'Taurus')
  ('constellation', 'sky')
  ('constellation', 'night+sky')
  ('constellation', 'night')
  ('constellation', 'planet')
  ('constellation', 'sun')
  ('constellation', 'surface')
  ('constellation', 'temperature')
  ('constellation', 'brightness')
  ('constellation', 'magnitude')
  ('constellation', 'host')
  ('constellation', 'times')
  ('constellation', 'mass')
  ('constellation', 'radius')
'As the brightest star in a Zodiac constellation, it is also given great significance within astrology.'
  distance = 6/35 = 0.17142857142857143
  ('brightest', 'brightest')
  ('brightest+star', 'brightest+star')
  ('star', 'star')
  ('constellation', 'constellation')
```

```python
# reformulation with cluster instead of constellation and Sun instead of brightest star
text = "the sun in the Taurus cluster"
d = search(text, doc_contexts, phrase_contexts)
for i in list(d.items())[0:3]:
    print(repr(i[0]))
    print("distance = " +str(i[1][0]) + " = "+str(float(i[1][0])))
    for j in i[1][1][0]:
        print("  " + str(j))
    for j in i[1][1][1]:
        print("  " +str(j))    
```
```console
"It is the brightest star in Taurus and generally the fourteenth-brightest star in the night sky, though it varies slowly in brightness between magnitude 0.75 and 0.95. Aldebaran is believed to host a planet several times the mass of Jupiter, named Aldebaran b. Aldebaran is a red giant, cooler than the sun with a surface temperature of 3,900 K, but its radius is about 44 times the sun's, so it is over 400 times as luminous."
  distance = 3/10 = 0.3
  ('sun', 'sun')
  ('Taurus', 'Taurus')
  ('cluster', 'star')
  ('cluster', 'night+sky')
  ('cluster', 'sky')
  ('cluster', 'planet')
  ('cluster', 'red+giant')
  ('cluster', 'surface+temperature')
  ('cluster', 'night')
  ('cluster', 'magnitude')
  ('cluster', 'host')
  ('cluster', 'mass')
  ('cluster', 'surface')
  ('cluster', 'temperature')
  ('cluster', 'radius')
'Aldebaran , designated α Tauri (Latinized to Alpha Tauri, abbreviated Alpha Tau, α Tau), is an orange giant star measured to be about 65 light-years from the Sun in the zodiac constellation Taurus.'
  distance = 1/2 = 0.5
  ('Taurus', 'Taurus')
  ('sun', 'Sun')
  ('sun', 'zodiac')
  ('cluster', 'zodiac')
  ('sun', 'constellation')
  ('cluster', 'star')
  ('cluster', 'Sun')
  ('sun', 'star')
  ('sun', 'years')
  ('cluster', 'years')
  ('cluster', 'constellation')
"The star is, by chance, in the line of sight between the Earth and the Hyades, so it has the appearance of being the brightest member of the open cluster, but the cluster that forms the bull's-head-shaped asterism is more than twice as far away, at about 150 light years."
  distance = 21/40 = 0.525
  ('cluster', 'cluster')
  ('sun', 'Earth')
  ('sun', 'line')
  ('sun', 'head')
  ('Taurus', 'light')
  ('sun', 'star')
  ('sun', 'chance')
  ('sun', 'bull')
  ('sun', 'years')
```

```python
text = "What did astronomer William Herschel discover to Aldebaran?"
d = search(text, doc_contexts, phrase_contexts)
for i in list(d.items())[0:3]:
    print(repr(i[0]))
    print("distance = " +str(i[1][0]) + " = "+str(float(i[1][0])))
    for j in i[1][1][0]:
        print("  " + str(j))
    for j in i[1][1][1]:
        print("  " +str(j))    
```

```console
'English astronomer William Herschel discovered a faint companion to Aldebaran in 1782; an 11th magnitude star at an angular separation of 117″.'
  distance = 47/97 = 0.4845360824742268
  ('astronomer', 'astronomer')
  ('William', 'William')
  ('Herschel', 'Herschel')
  ('Aldebaran', 'Aldebaran')
  ('What', 'English')
'It was then observed by Scottish astronomer James William Grant FRSE while in India on 23 July 1844.'
  distance = 59/97 = 0.6082474226804123
  ('astronomer', 'astronomer')
  ('William', 'William')
  ('What', 'It')
  ('What', 'It+was')
  ('did', 'was')
  ('Aldebaran', 'It')
  ('Aldebaran', 'India')
'Working at his private observatory in Tulse Hill, England, in 1864 William Huggins performed the first studies of the spectrum of Aldebaran, where he was able to identify the lines of nine elements, including iron, sodium, calcium, and magnesium.'
  distance = 61/97 = 0.6288659793814433
  ('William', 'William')
  ('Aldebaran', 'Aldebaran')
  ('discover', 'identify')
  ('did', 'he+was')
  ('did', 'was')
```

```python

```

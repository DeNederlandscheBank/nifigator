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


```python
# Read two documents in DBpedia about Aldebaran and Antares stars
doc_1 = g.get(
    URIRef("http://dbpedia.org/resource/Aldebaran?dbpv=2020-07&nif=context")
)
doc_2 = g.get(
    URIRef("http://dbpedia.org/resource/Antares?dbpv=2020-07&nif=context")
)
```

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

```python
from nifigator import STOPWORDS, generate_windows

# setup a dictionary with phrases and their contexts to speed up
def setup_phrase_contexts(documents: list=None, d: dict={}, topn: int=15):

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

phrase_contexts = setup_phrase_contexts([doc_1.isString, doc_2.isString], {})
```

```python

```

```python
from collections import Counter

def extract_contexts(s: str=None, d: dict=None):
    """
    extract the contexts of a string and calculate the vector
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

### Find similar sentences

```python
def jaccard_index(c1: set=None, c2: set=None):
    if len(c1 | c2 ) > 0:
        return len(c1 & c2)/len(c1 | c2)
    else:
        return 0
```

```python
# setup dictionary with sentences and their contexts
contexts = {
    sent.anchorOf: extract_contexts(sent.anchorOf, phrase_contexts)
    for sent in doc_1.sentences+doc_2.sentences    
}
```

```python
from itertools import combinations
        
# Calculate the Jaccard distance for all sentence combinations
d = dict()
for sent_1, sent_2 in combinations(contexts.keys(), 2):
    c1 = contexts[sent_1].keys()
    c2 = contexts[sent_2].keys()
    d[(sent_1, sent_2)] = 1 - jaccard_index(c1, c2)

# Sort the results with lowest distance
similarities = sorted(d.items(), key=lambda item: item[1])
```

```python
similarities[0:5]
```

```console
[(('It is a variable star listed in the General Catalogue of Variable Stars, but it is listed using its Bayer designation and does not have a separate variable star designation.',
   'Antares is a variable star and is listed in the General Catalogue of Variable Stars but as a Bayer-designated star it does not have a separate variable star designation.'),
  0.2591687041564792),
 (('In 2016, the International Astronomical Union Working Group on Star Names (WGSN) approved the proper name Aldebaran for this star.',
   'In 2016, the International Astronomical Union organised a Working Group on Star Names (WGSN) to catalog and standardise proper names for stars.'),
  0.35185185185185186),
 (('Aldebaran is the brightest star in the constellation Taurus and so has the Bayer designation α Tauri, Latinised as Alpha Tauri.',
   "Nomenclature\nα Scorpii (Latinised to Alpha Scorpii) is the star's Bayer designation."),
  0.585),
 (('Aldebaran is 5.47 degrees south of the ecliptic and so can be occulted by the Moon.',
   'Occultations and conjunctions\nAntares is 4.57 degrees south of the ecliptic, one of four first magnitude stars within 6° of the ecliptic (the others are Spica, Regulus and Aldebaran), so it can be occulted by the Moon.'),
  0.5942028985507246),
 (('The planetary exploration probe Pioneer 10 is heading in the general direction of the star and should make its closest approach in about two million years.',
   'It is expected to make its closest approach in about two million years.'),
  0.5957943925233644)]





### Explainable text search

Now some text search examples.


```python
def tversky_index(c1: set=None, c2: set=None, alfa: float=0, beta: float=0):
    denom = len(c1 & c2)+alfa*len(c1 - c2)+beta*len(c2 - c1)
    if denom != 0:
        return len(c1 & c2) / denom
    else:
        return 0

```

```python
def search(question: str=None, phrase_contexts: dict=None):
    
    # make sure that all words in the question have contexts available
    phrase_contexts = setup_phrase_contexts([question], phrase_contexts)

    # generate contexts of the question
    question_contexts = extract_contexts_2(question, phrase_contexts)
    phrases_1 = question_contexts.keys()
    
    d = {}
    for sent in list(contexts.keys()):
        phrases_2 = contexts[sent].keys()
        
        r = dict()
        for p1 in phrases_1:
            for p2 in phrases_2:
                jaccard_distance = 1 - jaccard_index(question_contexts[p1], contexts[sent][p2])
                if jaccard_distance < 1:
                    r[(p1, p2)] = jaccard_distance
        to_delete = set()
        for key, value in r.items():
            if value == 0:
                p1, p2 = key
                for key2, _ in r.items():
                    p1_2, p2_2 = key2
                    if (p1!=p1_2 or p2!=p2_2) and (p1 == p1_2 or p2 == p2_2):
                        to_delete.add(key2)
        for item in to_delete:
            del r[item]
            
        r = dict(sorted(r.items(), key=lambda item: item[1]))
        
        c1 = Counter()
        for p1 in phrases_1:
            c1 += question_contexts[p1]
            
        c2 = Counter()
        for p2 in phrases_2:
            c2 += contexts[sent][p2]

        d[sent] = (1 - tversky_index(c1, c2, 1, 0), r)
            
    d = dict(sorted(d.items(), key=lambda item: item[1][0]))
    return d
```

```python
question = "the brightest star in the constellation of Taurus"
d = search(question, phrase_contexts)
list(d.items())[0:5]
```

```python
# reformulation with cluster instead of constellation and Sun instead of brightest star
question = "the sun in the Taurus cluster"
d = search(question, phrase_contexts)
list(d.items())[0:5]
```



```python
question = "What did astronomer William Herschel discover to Aldebaran?"
d = search(question, phrase_contexts)
list(d.items())[0:5]
```

```console

```

```python
question = "stars that are visible to the naked eye"
d = search(question, phrase_contexts)
list(d.items())[0:5]
```

```console

```

```python
# setup dictionary with sentences and their contexts
contexts = {
    sent.anchorOf: extract_contexts_2(sent.anchorOf, phrase_contexts)
    for sent in doc_1.sentences+doc_2.sentences    
}
```

```python
from collections import Counter

def extract_contexts_2(s: str=None, d: dict=None):
    """
    extract the contexts of a string and calculate the vector
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
def search_2(question: str=None, phrase_contexts: dict=None):
    
    # make sure that all words in the question have contexts available
    phrase_contexts = setup_phrase_contexts([question], phrase_contexts)

    # generate contexts of the question
    question_contexts = extract_contexts_2(question, phrase_contexts)
    phrases_1 = question_contexts.keys()
    
    d = {}
    for sent in list(contexts.keys()):
        phrases_2 = contexts[sent].keys()
        
        r = dict()
        for p1 in phrases_1:
            for p2 in phrases_2:
                jaccard_distance = 1 - jaccard_index(question_contexts[p1], contexts[sent][p2])
                if jaccard_distance < 1:
                    r[(p1, p2)] = jaccard_distance
        r = dict(sorted(r.items(), key=lambda item: item[1]))
        
        c1 = Counter()
        for p1 in phrases_1:
            c1 += question_contexts[p1]
            
        c2 = Counter()
        for p2 in phrases_2:
            c2 += contexts[sent][p2]

        d[sent] = (1 - tversky_index(c1, c2, 1, 0), r)
            
    d = dict(sorted(d.items(), key=lambda item: item[1][0]))
    return d
```

```python
question = "What discovered astronomer William Herschel to Aldebaran?"
d = search_2(question, phrase_contexts)
list(d.items())[0:5]
```

```python

```

```python
c = g.contexts
phrase_contexts = setup_phrase_contexts(
    [context.isString for context in c[0:40]], phrase_contexts
)
```

```python
contexts = {
    sent.anchorOf: extract_contexts(sent.anchorOf, phrase_contexts)
    for sents in [context.sentences for context in c[0:40]] for sent in sents
}
```

```python
question = "What river crossed Caesar?"
d = search(question, phrase_contexts)
list(d.items())[0:5]
```

```python
question = "the brightest star in the constellation of Taurus"
d = search(question, phrase_contexts)
list(d.items())[0:5]
```

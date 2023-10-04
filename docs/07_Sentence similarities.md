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


## Load and set up two DBpedia pages

First we connect to the database

```python
import os, sys, logging
logging.basicConfig(stream=sys.stdout, 
                    format='%(asctime)s %(message)s',
                    level=logging.INFO)
```

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
from collections import defaultdict
import pickle
```

```python
# from collections import Counter

# # phrases
# q = """
# SELECT distinct ?v ?l ?r (sum(?count) as ?num)
# WHERE
# {
#     ?p rdf:type nif:Phrase .
#     ?p nifvec:isPhraseOf ?w .
#     ?w rdf:type nifvec:Window .
#     ?w nifvec:hasContext ?c .
#     ?w nifvec:hasCount ?count .
#     ?p rdf:value ?v .
#     ?c nifvec:hasLeftValue ?l .
#     ?c nifvec:hasRightValue ?r .
# }
# GROUP BY ?v ?l ?r
# ORDER BY DESC (?num)
# """
# results_phrases = list(g.query(q))

# d_phrases = defaultdict(Counter)
# for r in results_phrases:
#     d_phrases[r[0].value][(r[1].value, r[2].value)] = r[3].value

# with open('..//data//phrase_contexts_vectors.pickle', 'wb') as handle:
#     pickle.dump(d_phrases, handle, protocol=pickle.HIGHEST_PROTOCOL)
```

```python
# from collections import Counter

# # contexts
# q = """
# SELECT distinct ?l ?r ?v (sum(?count) as ?num)
# WHERE
# {
#     ?c nifvec:hasLeftValue ?l .
#     ?c nifvec:hasRightValue ?r .
#     ?w nifvec:hasContext ?c .
#     ?w nifvec:hasPhrase ?p .
#     ?w rdf:type nifvec:Window .
#     ?w nifvec:hasCount ?count .
#     ?p rdf:value ?v .
# }
# GROUP BY ?l ?r ?v 
# ORDER BY DESC (?num)
# """
# results_context_phrases = list(g.query(q))

# d_context_phrases = defaultdict(Counter)
# for r in results_context_phrases:
#     d_context_phrases[(r[0].value, r[1].value)][r[2].value] = r[3].value
    
# with open('..//data//context_phrases_vectors.pickle', 'wb') as handle:
#     pickle.dump(d_context_phrases, handle, protocol=pickle.HIGHEST_PROTOCOL)
```

```python
# # lemmas
# q = """
# SELECT distinct ?v ?l ?r (sum(?count) as ?num)
# WHERE
# {
#     {
#         ?p rdf:value ?v .
#         {
#             ?e ontolex:canonicalForm [ ontolex:writtenRep ?v ] .
#         }
#         UNION
#         {
#             ?e ontolex:otherForm [ ontolex:writtenRep ?v ] .
#         }
#         ?e ontolex:otherForm|ontolex:canonicalForm [ ontolex:writtenRep ?f ] .
#         ?lemma rdf:value ?f .
#         ?lemma nifvec:isPhraseOf ?w .
#         ?w rdf:type nifvec:Window .
#         ?w nifvec:hasContext ?c .
#         ?w nifvec:hasCount ?count .
#         ?c nifvec:hasLeftValue ?l .
#         ?c nifvec:hasRightValue ?r .
#     }
# }
# GROUP BY ?v ?l ?r
# ORDER BY DESC (?num)
# """
# results_lemmas = list(g.query(q))

# d_lemmas = defaultdict(Counter)
# for r in results_lemmas:
#     d_lemmas[r[0].value][(r[1].value, r[2].value)] = r[3].value 

# with open('..//data//lemma_contexts_vectors.pickle', 'wb') as handle:
#     pickle.dump(d_lemmas, handle, protocol=pickle.HIGHEST_PROTOCOL) 
```

```python
# # contexts lemmas
# q = """
# SELECT distinct ?l ?r ?v (sum(?count) as ?num)
# WHERE
# {
#     {
#         ?c nifvec:hasLeftValue ?l .
#         ?c nifvec:hasRightValue ?r .
#         ?w rdf:type nifvec:Window .
#         ?w nifvec:hasContext ?c .
#         ?w nifvec:hasCount ?count .
#         ?w nifvec:hasPhrase ?p .
#         ?p rdf:value ?f .
#         {
#             ?e ontolex:canonicalForm [ ontolex:writtenRep ?f ] .
#         }
#         UNION
#         {
#             ?e ontolex:otherForm [ ontolex:writtenRep ?f ] .
#         }
#         ?e ontolex:otherForm|ontolex:canonicalForm [ ontolex:writtenRep ?v ] .
#         ?lemma rdf:value ?v .
#     }
# }
# GROUP BY ?l ?r ?v 
# ORDER BY DESC (?num)
# """
# results_context_lemmas = list(g.query(q))

# d_context_lemmas = defaultdict(Counter)
# for r in results_context_lemmas:
#     d_context_lemmas[(r[0].value, r[1].value)][r[2].value] = r[3].value 
    
# with open('..//data//context_lemmas_vectors.pickle', 'wb') as handle:
#     pickle.dump(d_context_lemmas, handle, protocol=pickle.HIGHEST_PROTOCOL)   
```

```python

```

```python
import pickle

with open('..//data//phrase_vectors.pickle', 'rb') as handle:
    d_phrases = pickle.load(handle)
with open('..//data//lemma_vectors.pickle', 'rb') as handle:
    d_lemmas = pickle.load(handle)
with open('..//data//context_phrases_vectors.pickle', 'rb') as handle:
    d_context_phrases = pickle.load(handle)
# with open('..//data//context_lemma_vectors.pickle', 'rb') as handle:
#     d_lemmas = pickle.load(handle)
```

```python

```

```python
d_phrases['is'] <= d_lemmas['is']
```

```python
d_phrases['discovered'] <= d_lemmas['discover']
```

```python
d_phrases['kings'] + d_phrases['king'] == d_lemmas['kings']
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
    sent.anchorOf: document_vector(
        {sent.uri: sent.anchorOf}, 
        d_phrases,
        merge_dict=True
    )
    for sent in doc1.sentences
}
doc2_vector = {
    sent.anchorOf: document_vector(
        {sent.uri: sent.anchorOf}, 
        d_phrases,
        merge_dict=True,
    )
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
for item in similarities[0:35]:
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
# setup dictionary with sentences and their contexts
doc_phrases = {
    sent.anchorOf: document_vector({sent.uri: sent.anchorOf}, d_phrases, topn=15)
    for sent in doc1.sentences+doc2.sentences
}
doc_lemmas = {
    sent.anchorOf: document_vector({sent.uri: sent.anchorOf}, d_lemmas, topn=15)
    for sent in doc1.sentences+doc2.sentences
}
```

```python
from nifigator import containment_index
from collections import Counter

def search(query: str=None):
    """
    """
    # generate contexts of the text
    query_phrases = document_vector({'query': query}, d_phrases, topn=15)
    query_lemmas = document_vector({'query': query}, d_lemmas, topn=15)
    d = dict()
    for sent, sent_lemmas in doc_lemmas.items():
        sent_phrases = doc_phrases[sent]
        # find the full phrase matches of the text and the sentence
        full_matches = [
            (p1, p2)
            for p1, c1 in query_lemmas.items()
            for p2, c2 in sent_phrases.items()
            if 1 - containment_index(c2, c1) == 0
        ]
        # find the close phrase matches of the text and the sentence
        close_matches = {
            p1: [(p2, 1 - containment_index(c2, c1))
            for p2, c2 in sent_phrases.items()
            if 1 - containment_index(c2, c1) < 1 and 
               p1 not in [p[0] for p in full_matches] and 
               p2 not in [p[1] for p in full_matches]]
            for p1, c1 in query_lemmas.items()
        }
        close_matches = {key: sorted(value, key=lambda item: item[1]) for key, value in close_matches.items() if value!=[]}
        close_matches = dict(sorted(close_matches.items(), key=lambda item: item[1]))
        # calculate the containment index
        c1 = merge_multiset(query_phrases)
        c2 = merge_multiset(sent_lemmas)
        containment = containment_index(c1, c2)
        d[sent] = (1 - containment, (full_matches, close_matches))
    d = dict(sorted(d.items(), key=lambda item: item[1][0]))
    return d
```


Create a vector of every sentence in all documents.



```python
query = "The brightest star in the constellation of Taurus"
d = search(query=query)
for i in list(d.items())[0:3]:
    print(repr(i[0]))
    print("distance = " +str(i[1][0]) + " = "+str(float(i[1][0])))
    print("exact similarities:")
    for j in i[1][1][0]:
        print("  " +str(j)+' = 0')
    print("other similarities:")
    for j in i[1][1][1:]:
        for key, value in j.items():
            print("  "+repr(key)+" -> ", end='')
            print(", ".join([repr(row[0])+' ({0:.4f})'.format(float(row[1])) for row in value[0:3]]))
    print("")
```

```console
'Aldebaran is the brightest star in the constellation Taurus and so has the Bayer designation α Tauri, Latinised as Alpha Tauri.'
distance = 0 = 0.0
exact similarities:
  ('brightest', 'brightest') = 0
  ('brightest star', 'brightest star') = 0
  ('brightest star in the constellation', 'brightest star in the constellation') = 0
  ('star in the constellation', 'star in the constellation') = 0
  ('constellation', 'constellation') = 0
  ('Taurus', 'Taurus') = 0
other similarities:
  'star' -> 'star' (0.0667), 'Aldebaran' (0.6667), 'designation' (0.8667)

"It is the brightest star in Taurus and generally the fourteenth-brightest star in the night sky, though it varies slowly in brightness between magnitude 0.75 and 0.95. Aldebaran is believed to host a planet several times the mass of Jupiter, named Aldebaran b. Aldebaran is a red giant, cooler than the sun with a surface temperature of 3,900 K, but its radius is about 44 times the sun's, so it is over 400 times as luminous."
distance = 13/81 = 0.16049382716049382
exact similarities:
  ('brightest', 'brightest') = 0
  ('brightest star', 'brightest star') = 0
  ('star in the constellation', 'star in the night sky') = 0
  ('Taurus', 'Taurus') = 0
other similarities:
  'brightest star in the constellation' -> 'mass of Jupiter' (0.7143), 'night' (0.8000), 'planet' (0.8000)
  'constellation' -> 'sky' (0.6667), 'sun' (0.6667), 'mass of Jupiter' (0.7143)
  'star' -> 'star' (0.0667), 'planet' (0.6000), 'Aldebaran' (0.6667)

'As the brightest star in a Zodiac constellation, it is also given great significance within astrology.'
distance = 7/27 = 0.25925925925925924
exact similarities:
  ('brightest', 'brightest') = 0
  ('brightest star', 'brightest star') = 0
  ('constellation', 'constellation') = 0
other similarities:
  'brightest star in the constellation' -> 'Zodiac' (0.5000), 'star' (0.8667), 'significance' (0.9333)
  'Taurus' -> 'astrology' (0.8667)
  'star' -> 'star' (0.0667), 'Zodiac' (0.3333), 'significance' (0.8667)
```

```python
# reformulation with cluster instead of constellation and Sun instead of brightest star
query = "the sun in the Taurus cluster"
d = search(query=query)
for i in list(d.items())[0:3]:
    print(repr(i[0]))
    print("distance = " +str(i[1][0]) + " = "+str(float(i[1][0])))
    print("exact similarities:")
    for j in i[1][1][0]:
        print("  " +str(j)+' = 0')
    print("other similarities:")
    for j in i[1][1][1:]:
        for key, value in j.items():
            print("  "+repr(key)+": ", end='')
            print(", ".join([repr(row[0])+' ({0:.4f})'.format(float(row[1])) for row in value[0:3]]))
    print("")
```
```console
"It is the brightest star in Taurus and generally the fourteenth-brightest star in the night sky, though it varies slowly in brightness between magnitude 0.75 and 0.95. Aldebaran is believed to host a planet several times the mass of Jupiter, named Aldebaran b. Aldebaran is a red giant, cooler than the sun with a surface temperature of 3,900 K, but its radius is about 44 times the sun's, so it is over 400 times as luminous."
distance = 11/43 = 0.2558139534883721
exact similarities:
  ('sun', 'sun') = 0
  ('Taurus', 'Taurus') = 0
other similarities:
  'cluster': 'star' (0.8000), 'brightness' (0.8000), 'planet' (0.8000)

'Aldebaran , designated α Tauri (Latinized to Alpha Tauri, abbreviated Alpha Tau, α Tau), is an orange giant star measured to be about 65 light-years from the Sun in the zodiac constellation Taurus.'
distance = 13/43 = 0.3023255813953488
exact similarities:
  ('Taurus', 'Taurus') = 0
other similarities:
  'sun': 'Sun' (0.1333), 'zodiac' (0.7333), 'constellation' (0.7333)
  'cluster': 'star' (0.8000), 'constellation' (0.8000), 'light' (0.8667)

"The star is, by chance, in the line of sight between the Earth and the Hyades, so it has the appearance of being the brightest member of the open cluster, but the cluster that forms the bull's-head-shaped asterism is more than twice as far away, at about 150 light years."
distance = 18/43 = 0.4186046511627907
exact similarities:
  ('sun', 'Hyades') = 0
other similarities:
  'cluster': 'cluster' (0.0667), 'line' (0.7333), 'star' (0.8000)
  'Taurus': 'sight' (0.8667), '150' (0.9333), 'light' (0.9333)
```

```python
query = "What did astronomer William Herschel discover to Aldebaran?"
d = search(query=query)
for i in list(d.items())[0:6]:
    print(repr(i[0]))
    print("distance = " +str(i[1][0]) + " = "+str(float(i[1][0])))
    print("exact similarities:")
    for j in i[1][1][0]:
        print("  " +str(j)+' = 0')
    print("other similarities:")
    for j in i[1][1][1:]:
        for key, value in j.items():
            print("  "+repr(key)+" -> ", end='')
            print(", ".join([repr(row[0])+' ({0:.4f})'.format(float(row[1])) for row in value[0:3]]))
    print("")
```

```console
'English astronomer William Herschel discovered a faint companion to Aldebaran in 1782; an 11th magnitude star at an angular separation of 117″.'
distance = 14/33 = 0.42424242424242425
exact similarities:
  ('astronomer', 'astronomer') = 0
  ('William', 'William') = 0
  ('William Herschel', 'William Herschel') = 0
  ('Herschel', 'Herschel') = 0
  ('discover', 'discovered') = 0
  ('Aldebaran', 'Aldebaran') = 0
other similarities:

'It was then observed by Scottish astronomer James William Grant FRSE while in India on 23 July 1844.'
distance = 50/99 = 0.5050505050505051
exact similarities:
  ('astronomer', 'astronomer') = 0
  ('William', 'William') = 0
other similarities:
  'What' -> 'It' (0.9333)
  'Aldebaran' -> 'It' (0.9333), 'India' (0.9333), '1844' (0.9333)
  'Herschel' -> 'It was' (0.9333)
  'What did' -> 'It was then' (0.9091), 'It was' (0.9333)
  'discover' -> 'observed' (0.6000), 'was' (0.9333), 'was then' (0.9333)
  'did' -> 'was' (0.9333), 'India' (0.9333)

'English astronomer Edmund Halley studied the timing of this event, and in 1718 concluded that Aldebaran must have changed position since that time, moving several minutes of arc further to the north.'
distance = 20/33 = 0.6060606060606061
exact similarities:
  ('astronomer', 'astronomer') = 0
  ('Aldebaran', 'Aldebaran') = 0
other similarities:
  'What' -> '1718' (0.8571), 'this event' (0.8667), 'moving' (0.9333)
  'What did' -> 'concluded that' (0.9333), 'that' (0.9333)
  'did' -> 'have changed' (0.9231), 'this event' (0.9333), 'have' (0.9333)
  'William' -> 'several' (0.8667), 'timing' (0.9333)
  'discover' -> 'since that time' (0.6667), 'studied' (0.8000), 'concluded' (0.8000)

"Follow on measurements of proper motion showed that Herschel's companion was diverging from Aldebaran, and hence they were not physically connected."
distance = 61/99 = 0.6161616161616161
exact similarities:
  ('Herschel', 'Herschel') = 0
  ('Aldebaran', 'Aldebaran') = 0
other similarities:
  'What did' -> 'hence' (0.8667), 'showed that' (0.9333), 'that' (0.9333)
  'What' -> 'hence' (0.9333)
  'William' -> 'measurements' (0.8667), 'motion' (0.8667), 'hence' (0.9333)
  'discover' -> 'showed that' (0.8000), 'showed' (0.8667), 'that' (0.9333)
  'did' -> 'were' (0.7333), 'they were' (0.8000), 'was' (0.9333)

'It was included with an 11th magnitude companion as a double star as H IV 66 in the Herschel Catalogue of Double Stars and Σ II 2 in the Struve Double Star Catalog, and together with a 14th magnitude star as β 550 in the Burnham Double Star Catalogue.'
distance = 64/99 = 0.6464646464646465
exact similarities:
  ('Herschel', 'Herschel') = 0
other similarities:
  'William' -> 'Catalog' (0.9231), 'magnitude' (0.9333), 'Catalogue' (0.9333)
  'What' -> 'It' (0.9333)
  'Aldebaran' -> 'It' (0.9333), 'magnitude' (0.9333), 'star' (0.9333)
  'What did' -> 'It was' (0.9333)
  'discover' -> 'included' (0.8000), 'was' (0.9333), 'double' (0.9333)
  'did' -> 'was' (0.9333), 'double' (0.9333)

'It is a variable star listed in the General Catalogue of Variable Stars, but it is listed using its Bayer designation and does not have a separate variable star designation.'
distance = 65/99 = 0.6565656565656566
exact similarities:
other similarities:
  'William' -> 'Catalogue' (0.9333)
  'What' -> 'It' (0.9333), 'it' (0.9333), 'using' (0.9333)
  'Herschel' -> 'It is' (0.9333), 'it' (0.9333)
  'What did' -> 'It is' (0.9333), 'it is' (0.9333), 'does' (0.9333)
  'did' -> 'does' (0.2667), 'it is' (0.7333), 'is' (0.9333)
  'Aldebaran' -> 'it' (0.8667), 'It' (0.9333), 'star' (0.9333)
  'discover' -> 'listed' (0.8667), 'using' (0.8667), 'is' (0.9333)
```


### Applying the minHash algorithm with LSH (Locality Sensitive Hashing)

```python
num_perm = 2**7
```

```python
from datasketch import MinHashLSHEnsemble, MinHash

def create_minhash_dict(
    d: dict=None,
    minhash_dict: dict={},
    topn: int=15
):
    for key, value in d.items():
        minhash_dict[key] = MinHash(
            num_perm=num_perm
        )
        for context in value.most_common(topn):
            v = str(context[0]).encode('utf8')
            minhash_dict[key].update(v)
    return minhash_dict

minhash_phrases = create_minhash_dict(d_phrases, {})
minhash_lemmas = create_minhash_dict(d_lemmas, {})
```

```python
s1 = 'king'
s2 = 'queen'
print("estimated Jaccard index: "+str(1 - minhash_phrases[s2].jaccard(minhash_phrases[s1])))
print("real Jaccard index: "+str(1 - float(jaccard_index(
    set(p[0] for p in d_phrases[s1].most_common(15)),
    set(p[0] for p in d_phrases[s2].most_common(15)),
))))
```

```console
estimated Jaccard index: 0.71875
real Jaccard index: 0.6956521739130435
```

```python
s1 = 'was'
s2 = 'be'
print("estimated Jaccard index: "+str(1 - minhash_phrases[s2].jaccard(minhash_phrases[s1])))
print("real Jaccard index: "+str(1 - float(jaccard_index(
    set(p[0] for p in d_phrases[s1].most_common(15)),
    set(p[0] for p in d_phrases[s2].most_common(15)),
))))
```

```console
estimated Jaccard index: 1.0
real Jaccard index: 1.0
```

```python
def create_document_minhash_dict(
    documents: dict=None, 
    phrases_minhash: dict=None,
):
    minhash_dict = dict()
    for key, value in documents.items():
        minhash_dict[key] = MinHash(
            num_perm=num_perm
        )
        for phrase in value.keys():
            minhash_dict[key].merge(phrases_minhash[phrase])
    return minhash_dict

minhash_docs = create_document_minhash_dict(
    doc_phrases, 
    minhash_phrases
)
```

```python
s1 = 'Antares is a variable star and is listed in the General Catalogue of Variable Stars but as a Bayer-designated star it does not have a separate variable star designation.'
s2 = 'It is a variable star listed in the General Catalogue of Variable Stars, but it is listed using its Bayer designation and does not have a separate variable star designation.'
print("estimated Jaccard index: "+str(1 - minhash_docs[s2].jaccard(minhash_docs[s1])))
print("real Jaccard index: "+str(1 - float(jaccard_index(
    merge_multiset(doc_phrases[s1]).keys(),
    merge_multiset(doc_phrases[s2]).keys()
))))

```

```console
estimated Jaccard index: 0.2890625
real Jaccard index: 0.26041666666666663
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
        for key, value in doc_phrases.items()
    ]
)
```

```python
def minhash_search(query: str=None):
    """
    """
    # generate contexts of the text
    query_phrases = document_vector({'query': query}, d_lemmas)
    # minhash_lemmas = create_minhash_dict(query_phrases, minhash_phrases)
    minhash_query = MinHash(
        num_perm=num_perm
    )
    for phrase in query_phrases.keys():
        minhash_query.merge(minhash_lemmas[phrase])
    d = dict()
    for sent in lshensemble.query(minhash_query, len(query_phrases.keys())):
        c1 = merge_multiset(query_phrases).keys()
        c2 = merge_multiset(doc_phrases[sent]).keys()
        containment = containment_index(c1, c2)
        d[sent] = 1 - containment
    d = dict(sorted(d.items(), key=lambda item: item[1]))
    return d
```

```python
query = "The brightest star in the constellation of Taurus"
d = search(query=query)
for item, distance in list(d.items())[0:3]:
    print(repr(item) +': {0:.4f}'.format(float(distance[0])))
```

```console
'Aldebaran is the brightest star in the constellation Taurus and so has the Bayer designation α Tauri, Latinised as Alpha Tauri.': 0.1975
"It is the brightest star in Taurus and generally the fourteenth-brightest star in the night sky, though it varies slowly in brightness between magnitude 0.75 and 0.95. Aldebaran is believed to host a planet several times the mass of Jupiter, named Aldebaran b. Aldebaran is a red giant, cooler than the sun with a surface temperature of 3,900 K, but its radius is about 44 times the sun's, so it is over 400 times as luminous.": 0.3086
'As the brightest star in a Zodiac constellation, it is also given great significance within astrology.': 0.4568
```

```python
query = "the sun in the Taurus cluster"
d = search(query=query)
for item, distance in list(d.items())[0:3]:
    print(repr(item) +': {0:.4f}'.format(float(distance[0])))
```

```console
"It is the brightest star in Taurus and generally the fourteenth-brightest star in the night sky, though it varies slowly in brightness between magnitude 0.75 and 0.95. Aldebaran is believed to host a planet several times the mass of Jupiter, named Aldebaran b. Aldebaran is a red giant, cooler than the sun with a surface temperature of 3,900 K, but its radius is about 44 times the sun's, so it is over 400 times as luminous.": 0.2558
'Aldebaran , designated α Tauri (Latinized to Alpha Tauri, abbreviated Alpha Tau, α Tau), is an orange giant star measured to be about 65 light-years from the Sun in the zodiac constellation Taurus.': 0.3256
'Aldebaran is the brightest star in the constellation Taurus and so has the Bayer designation α Tauri, Latinised as Alpha Tauri.': 0.4651
```

```python
query = "What did astronomer William Herschel discover in relation to Aldebaran?"
d = search(query=query)
for item, distance in list(d.items())[0:3]:
    print(repr(item) +': {0:.4f}'.format(float(distance[0])))
```

```console
'English astronomer William Herschel discovered a faint companion to Aldebaran in 1782; an 11th magnitude star at an angular separation of 117″.': 0.4912
'It was then observed by Scottish astronomer James William Grant FRSE while in India on 23 July 1844.': 0.5789
'English astronomer Edmund Halley studied the timing of this event, and in 1718 concluded that Aldebaran must have changed position since that time, moving several minutes of arc further to the north.': 0.6754

```

```python

```

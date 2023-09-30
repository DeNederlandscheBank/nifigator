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

# Querying a NifVector graph - Dutch

## Introduction

```python
import os, sys, logging
logging.basicConfig(stream=sys.stdout, 
                    format='%(asctime)s %(message)s',
                    level=logging.INFO)
```

## Querying the NifVector graph based on DBpedia


These are results of a NifVector graph created with 100.000 DBpedia pages. We defined a context of a word in it simplest form: the tuple of the previous multiwords and the next multiwords (no preprocessing, no changes to the text, i.e. no deletion of stopwords and punctuation). The maximum phrase length is five words, the maximum left and right context length is also five words.

```python
from rdflib import URIRef

database_url = 'http://localhost:3030/dbpedia_nl'
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


### Most frequent contexts of a phrase


The eight most frequent contexts in which the word 'has' occurs with their number of occurrences are the following:

```python
# most frequent contexts of the word "schrijver"
g.phrase_contexts("is gemaakt", topn=10)
```

This results in

```console
Counter({('gebruik', 'van'): 15,
         ('Het', 'door'): 12,
         ('SENTSTART Het', 'door'): 11,
         ('beeld', 'door'): 7,
         ('tekst', 'door'): 6,
         ('De tekst', 'door'): 5,
         ('SENTSTART De tekst', 'door'): 5,
         ('ei', 'van'): 5,
         ('muziek', 'door'): 5,
         ('en', 'door'): 3})
```

SENTSTART and SENTEND are tokens to indicate the start and end of a sentence.


### Phrase and context frequencies


The contexts in which a word occurs represent to some extent the properties and the meaning of a word. If you derive the phrases that share the most frequent contexts of the word 'has' then you get the following table (the columns contains the contexts, the rows the phrases that have the most contexts in common):

```python
import pandas as pd
pd.DataFrame().from_dict(
    g.dict_phrases_contexts("is gemaakt", topcontexts=8), orient='tight'
)
```

This results in:

```console
                gebruik  Het     SENTSTART Het  beeld 	tekst 	De tekst    SENTSTART De tekst 	ei
                van      door    door 	        door 	door 	door 	    door                van
is gemaakt      15       12      11             7       6       5           5                   5
is geschreven   0        79      78             0       22      12          11                  0
werd geschreven 0        19      19             0       14      10          10                  0
is              0        47      47             2       2       0           0                   0
werd gemaakt    53       2       2              2       0       0           0                   0
was             2    	 10      9              0       0       0           0                   0
werd            0        83      82             2       0       0           0                   0
```


### Phrase similarities


Based on the approach above we can derive top phrase similarities.

```python
# top phrase similarities of the word "has"
g.most_similar("is gemaakt", topn=10, topcontexts=15)
```

This results in

```console
{'is gemaakt': (15, 15),
 'is geschreven': (9, 15),
 'werd': (9, 15),
 'is': (8, 15),
 'werd geschreven': (7, 15),
 'wordt': (7, 15),
 'was': (6, 15),
 'werd gemaakt': (6, 15),
 'wordt gemaakt': (5, 15),
 'gemaakt': (4, 15)}
```

Now take a look at similar words of 'groter'.

```python
# top phrase similarities of the word "larger"
g.most_similar("groter", topn=10, topcontexts=15)
```

Resulting in:

```console
{'groter': (15, 15),
 'kleiner': (14, 15),
 'breder': (11, 15),
 'hoger': (11, 15),
 'lager': (11, 15),
 'beter': (10, 15),
 'langer': (10, 15),
 'meer': (10, 15),
 'sneller': (10, 15),
 'minder': (9, 15)}
```

```python
# top phrase similarities of the word "King"
g.most_similar("koning", topn=10, topcontexts=25)
```

This results in

```console
{'koning': (25, 25),
 'hertog': (22, 25),
 'keizer': (22, 25),
 'vorst': (21, 25),
 'prins': (20, 25),
 'graaf': (19, 25),
 'koningin': (18, 25),
 'Koning': (17, 25),
 'bisschop': (17, 25),
 'groothertog': (17, 25)}
```



Instead of single words we can also find the similarities of multiwords

```python
# top phrase similarities of Willem Alexander (King of the Netherlands)
g.most_similar("Willem Alexander", topn=10, topcontexts=15)
```

```console
{'Willem Alexander': (15, 15),
 'Filip': (8, 15),
 'Boudewijn': (7, 15),
 'Willem I': (7, 15),
 'Willem III': (7, 15),
 'Albert II': (6, 15),
 'George III': (6, 15),
 'Maximiliaan I Jozef van Beieren': (6, 15),
 'Willem II': (6, 15),
 'Christiaan IX van Denemarken': (5, 15)}
```



### Most frequent phrases of a context


Here are some examples of the most frequent phrases of a context.

```python
context = ("koning", "van Engeland")
for r in g.context_phrases(context, topn=10).items():
    print(r)
```

```console
('Eduard III', 21)
('Karel II', 21)
('Karel I', 17)
('Eduard I', 15)
('Hendrik VIII', 13)
('Jacobus II', 13)
('Eduard IV', 11)
('Hendrik VII', 9)
('Jacobus I', 9)
('Hendrik II', 8)
```

```python
context = ("de", "stad")
for r in g.context_phrases(context, topn=10).items():
    print(r)
```

```console
('grootste', 493)
('oude', 228)
('gelijknamige', 178)
('tweede', 120)
('Duitse', 116)
('Nederlandse', 116)
('belangrijkste', 105)
('huidige', 99)
('hele', 97)
('nieuwe', 91)

```


### Phrase similarities given a specific context

Some phrases have multiple meanings. Take a look at the contexts of the word 'middel':

```python
g.phrase_contexts("middel", topn=10)
```

This results in:

```console
Counter({('door', 'van'): 4956,
         ('door', 'van een'): 1516,
         ('door', 'van de'): 406,
         ('SENTSTART Door', 'van'): 398,
         ('Door', 'van'): 390,
         ('door', 'van het'): 264,
         ('worden door', 'van'): 142,
         ('een', 'om'): 135,
         ('die door', 'van'): 117,
         ('Door', 'van een'): 102})
```
It is possible to take into account a specific context when using the most_similar function in the following way:

```python
g.most_similar(phrase="middel", context=("door", "van"), topcontexts=50, topphrases=15, topn=10)
```

The result is:

```console
{'middel': (50, 50),
 'toedoen': (21, 50),
 'gebruik te maken': (19, 50),
 'toepassing': (15, 50),
 'gebruik': (11, 50),
 'leden': (10, 50),
 'toevoeging': (7, 50),
 'die': (6, 50),
 'doelpunten': (4, 50),
 'samenvoeging': (3, 50)}
```

```python
g.most_similar(phrase="middel", context=("een", "dat"), topcontexts=50, topphrases=15, topn=10)
```

In this case the result is:

```console
{'systeem': (5, 5),
 'apparaat': (4, 5),
 'programma': (4, 5),
 'proces': (3, 5),
 'teken': (3, 5),
 'bedrijf': (2, 5),
 'gebied': (2, 5),
 'tijd': (2, 5),
 'woord': (2, 5),
 'boek': (1, 5)}
```


### Phrase similarities given a set of contexts

If you want to find the phrases that fit a set of contexts then this is also possible.

```python
c1 = [
        c[0] for c in (
            g.phrase_contexts("dacht", topn=None) &
            g.phrase_contexts("vond", topn=None)
         ).most_common(15)
]
c1
```

This results in:

```console
[('hij', 'dat'),
 ('Hij', 'dat'),
 ('SENTSTART Hij', 'dat'),
 ('omdat hij', 'dat'),
 ('en', 'dat'),
 ('men', 'dat'),
 ('hij', 'dat de'),
 ('die', 'dat'),
 ('hij', 'dat hij'),
 ('dat hij', 'dat'),
 ('omdat men', 'dat'),
 ('hij', 'dat het'),
 ('omdat hij', 'dat de'),
 ('Hij', 'dat het'),
 ('SENTSTART Hij', 'dat het')]
```

```python
g.most_similar(contexts=c1, topn=10)
```

Resulting in:

```console
{'dacht': (15, 15),
 'meende': (15, 15),
 'vond': (15, 15),
 'stelde': (12, 15),
 'zei': (12, 15),
 'beweerde': (11, 15),
 'denkt': (11, 15),
 'geloofde': (11, 15),
 'vindt': (11, 15),
 'wist': (11, 15)}
```

```python

```

```python

```

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

```python
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from nifigator import NifVectorGraph, URIRef

# Connect to triplestore
store = SPARQLUpdateStore()
query_endpoint = 'http://localhost:3030/dbpedia_en/sparql'
update_endpoint = 'http://localhost:3030/dbpedia_en/update'
store.open((query_endpoint, update_endpoint))

# Create NifVectorGraph with this store
g = NifVectorGraph(store=store, identifier=URIRef("https://mangosaurus.eu/dbpedia"))
```


```python
p = g.phrases()
```

```python
print("Number of phrases: " +str(len(p.keys())))
```

```python
# Creating the NLP processor
import stanza

lang = "en"

# create a Stanza pipeline for pretokenized data
nlp = stanza.Pipeline(
        lang=lang, 
        processors='tokenize, lemma, pos', 
        tokenize_pretokenized=True,
        download_method=None,
        verbose=False
)
```

```python
text = [item.split(" ") for item in list(p.keys())]
```

```python
stanza = nlp(text)
```

```python
len(stanza.sentences)
```

```python
from nifigator import DEFAULT_URI, Lexicon, to_iri, LexicalEntry, Form, Literal, XSD
from nifigator import ComponentList, Component, mapobject

import nifigator

phrase_sep = "+"

lexica = dict()

lemon_entries = list()

# construct lexicon if necessary
if lang not in lexica.keys():
    lexica[lang] = Lexicon(uri=URIRef(DEFAULT_URI + "lexicon/"+lang+"/"))
    lexica[lang].set_language(lang)

for sentence in stanza.sentences:
    
    if all([word.lemma is not None for word in sentence.words]):

        text = " ".join([word.text for word in sentence.words])
        lemma = " ".join([word.lemma for word in sentence.words]).replace("_", "")
        
        # derive lexical entry uri from the lemma
        if not isinstance(lemma, URIRef):
            uri = URIRef(to_iri(str(lexica[lang].uri) + lemma.replace(" ", "+")))
        else:
            uri = lemma
            
        # create the lexical entry
        lexicalEntry = LexicalEntry(
            uri=uri, 
            language=lexica[lang].language
        )
        # set canonicalForm (this is the lemma)
        lexicalEntry.set_canonicalForm(
            Form(
                uri=uri,
                formVariant="canonicalForm",
                writtenReps=[lemma],
            )
        )
        # set otherForm if the anchorOf is not the same as the lemma
        if text != lemma:
            lexicalEntry.set_otherForms(
                [
                    Form(
                        uri=uri,
                        formVariant="otherForm",
                        writtenReps=[text],
                    )
                ]
            )
        # set part of speech if it exists
        pos = [nifigator.upos2olia.get(word.upos, None) for word in sentence.words]
        if pos is not None and len(pos) == 1:
            lexicalEntry.set_partOfSpeechs(pos)

        phrase_feats = []
        for word in sentence.words:
            word_feats = [] 
            if word.feats is not None:
                for i in word.feats.split("|"):
                    p = i.split("=")[0]
                    o = i.split("=")[1]
                    olia = mapobject(p, o)
                    if olia is not None:
                        word_feats.append(URIRef(olia))
            phrase_feats.append(word_feats)
        if phrase_feats is not None and len(phrase_feats) == 1:
            lexicalEntry.set_MorphPatterns(phrase_feats[0])
        lexica[lang].add_entry(lexicalEntry)    
        components = lemma.split(" ")
        if len(components) > 1:
            component_list = ComponentList(
                uri=lexicalEntry.uri,
                components=[],
            )
            for idx, component in enumerate(components):
                component_lexicalEntry = LexicalEntry(
                    uri=URIRef(to_iri(str(lexica[lang].uri)+component)),
                    language=lexica[lang].language,
                    partOfSpeechs=[pos[idx]] if len(pos) > 1 else None,
                    patterns=phrase_feats[idx] if len(phrase_feats) > 1 else None
                )
                component_lexicalEntry.set_canonicalForm(
                    Form(
                        uri=URIRef(to_iri(str(lexica[lang].uri)+component)),
                        formVariant="canonicalForm",
                        writtenReps=[component],
                    )
                )
                lexica[lang].add_entry(component_lexicalEntry)    
                lemon_component = Component(
                    uri=lexicalEntry.uri
                    + "#component"
                    + str(idx + 1),
                    correspondsTo=[component_lexicalEntry],
                )
                component_list.add_component(lemon_component)
            lemon_entries.append(component_list)
```

```python
len(lexica['en'].entries)
```

```python
from nifigator import NifGraph

# Graph identifier
identifier = URIRef("https://mangosaurus.eu/dbpedia")

lexicon = NifGraph(
    identifier=identifier,
)

lexicon.bind("ontolex", URIRef("http://www.w3.org/ns/lemon/ontolex#"))
lexicon.bind("lexinfo", URIRef("http://www.lexinfo.net/ontology/3.0/lexinfo#"))
lexicon.bind("decomp", URIRef("http://www.w3.org/ns/lemon/decomp#"))

for triple in lexica['en'].triples():
    lexicon.add(triple)
    
for entry in lemon_entries:
    for triple in entry.triples():
        lexicon.add(triple)
```

```python
# lexicon.serialize(destination="lexicon.ttl", format="ttl")
# lexicon.serialize(destination="lexicon.", format="ttl")
```

```python
# from rdflib import Graph
# lexicon = Graph()
# lexicon.parse("lexicon.xml")
```

```python
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore, _node_to_sparql
from rdflib import ConjunctiveGraph, Graph, URIRef, BNode
from nifigator import NifVectorGraph

# define conversion of BNodes to sparql
def bnode_sparql_conversion(node):
    if isinstance(node, BNode):
        return '<bnode:b%s>' % node
    return _node_to_sparql(node)

# Connect to triplestore
store = SPARQLUpdateStore(node_to_sparql=bnode_sparql_conversion)
query_endpoint = 'http://localhost:3030/dbpedia_en/sparql'
update_endpoint = 'http://localhost:3030/dbpedia_en/update'
store.open((query_endpoint, update_endpoint))

# Graph identifier
identifier = URIRef("https://mangosaurus.eu/dbpedia")
```

```python
from nifigator import NifGraph

g = NifVectorGraph(
    store=store,
    identifier=identifier,
)
```

```python
g += lexicon
```

```python
g.bind("ontolex", URIRef("http://www.w3.org/ns/lemon/ontolex#"))
g.bind("lexinfo", URIRef("http://www.lexinfo.net/ontology/3.0/lexinfo#"))
g.bind("decomp", URIRef("http://www.w3.org/ns/lemon/decomp#"))
```

```python
q = """
    SELECT DISTINCT ?f
    WHERE
    {
        {
            ?e ontolex:canonicalForm [ ontolex:writtenRep "behave" ] .
            ?e ontolex:otherForm|ontolex:canonicalForm [ ontolex:writtenRep ?f ] .
        }
    }
    group by ?f
"""
results = list(g.query(q))
```

```python
results
```

```python

```

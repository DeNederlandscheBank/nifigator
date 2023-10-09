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


# SPARQL queries for NifVector


## From phrase to contexts in which the phrase is used


This produces the context vector of a phrase

```console
SELECT DISTINCT ?v (sum(?count) as ?n)
WHERE
{
    {
        <phrase_uri> nifvec:isPhraseOf ?w .
        ?w rdf:type nifvec:Window .
        ?w nifvec:hasCount ?count .
        ?w nifvec:hasContext ?c .
        ?c rdf:value ?v .
    }
}
GROUP BY ?v
ORDER BY DESC(?n)
```


## From context to phrases that are used in the context


This produces the phrase vector of a context

```console
SELECT distinct ?v (sum(?count) as ?num)
WHERE
{
    {
        <context_uri> nifvec:isContextOf ?w .
        ?w rdf:type nifvec:Window .
        ?w nifvec:hasCount ?count .
        ?p nifvec:isPhraseOf ?w .
        ?p rdf:value ?v .
    }
}
GROUP BY ?v
ORDER BY DESC(?num)
```

## Most similar phrases of a phrase


```console
SELECT distinct ?v (count(?c) as ?num1)
WHERE
{
    {
        {
            SELECT DISTINCT ?c (sum(?count1) as ?n1) 
            WHERE
            {
                <phrase_uri> nifvec:isPhraseOf ?w1 .
                ?w1 rdf:type nifvec:Window .
                ?w1 nifvec:hasContext ?c .
                ?w1 nifvec:hasCount ?count1 .
            }
            GROUP BY ?c
            ORDER BY DESC(?n1)
            LIMIT topcontexts
        }
        ?c nifvec:isContextOf ?w .
        ?p nifvec:isPhraseOf ?w .
        ?w rdf:type nifvec:Window .
        ?p rdf:value ?v .
    }
}
GROUP BY ?v
ORDER BY DESC (?num1)
```

## Most similar phrases of a phrase with a context


```console
SELECT distinct ?v (count(?c) as ?num1)
WHERE
{
    {
        {
            SELECT DISTINCT ?c (sum(?count1) as ?n1) 
            WHERE
            {
                <phrase_uri> nifvec:isPhraseOf ?w1 .
                ?w1 rdf:type nifvec:Window .
                ?w1 nifvec:hasContext ?c .
                ?w1 nifvec:hasCount ?count1 .
            }
            GROUP BY ?c
            ORDER BY DESC(?n1)
            LIMIT topcontexts
        }
        {
            SELECT DISTINCT ?p (sum(?count2) as ?n2)
            WHERE
            {
                <context_uri> nifvec:isContextOf ?w2 .
                ?w2 rdf:type nifvec:Window .
                ?w2 nifvec:hasPhrase ?p .
                ?w2 nifvec:hasCount ?count2 .
            }
            GROUP BY ?p
            ORDER BY DESC(?n2)
            LIMIT topphrases
        }
        ?c nifvec:isContextOf ?w .
        ?p nifvec:isPhraseOf ?w .
        ?w rdf:type nifvec:Window .
        ?p rdf:value ?v .
    }
}
GROUP BY ?v
ORDER BY DESC (?num1)
```


```python
from collections import Counter

# phrases
q = """
SELECT distinct ?v ?l ?r (sum(?count) as ?num)
WHERE
{
    ?p rdf:type nif:Phrase .
    ?p nifvec:isPhraseOf ?w .
    ?w rdf:type nifvec:Window .
    ?w nifvec:hasContext ?c .
    ?w nifvec:hasCount ?count .
    ?p rdf:value ?v .
    ?c nifvec:hasLeftValue ?l .
    ?c nifvec:hasRightValue ?r .
}
GROUP BY ?v ?l ?r
ORDER BY DESC (?num)
"""
results_phrases = list(g.query(q))

d_phrases = defaultdict(Counter)
for r in results_phrases:
    d_phrases[r[0].value][(r[1].value, r[2].value)] = r[3].value

with open('..//data//phrase_contexts_vectors.pickle', 'wb') as handle:
    pickle.dump(d_phrases, handle, protocol=pickle.HIGHEST_PROTOCOL)
```

```python
from collections import Counter

# contexts
q = """
SELECT distinct ?l ?r ?v (sum(?count) as ?num)
WHERE
{
    ?c nifvec:hasLeftValue ?l .
    ?c nifvec:hasRightValue ?r .
    ?w nifvec:hasContext ?c .
    ?w nifvec:hasPhrase ?p .
    ?w rdf:type nifvec:Window .
    ?w nifvec:hasCount ?count .
    ?p rdf:value ?v .
}
GROUP BY ?l ?r ?v 
ORDER BY DESC (?num)
"""
results_context_phrases = list(g.query(q))

d_context_phrases = defaultdict(Counter)
for r in results_context_phrases:
    d_context_phrases[(r[0].value, r[1].value)][r[2].value] = r[3].value
    
with open('..//data//context_phrases_vectors.pickle', 'wb') as handle:
    pickle.dump(d_context_phrases, handle, protocol=pickle.HIGHEST_PROTOCOL)
```

```python
# lemmas
q = """
SELECT distinct ?v ?l ?r (sum(?count) as ?num)
WHERE
{
    {
        ?p rdf:value ?v .
        {
            ?e ontolex:canonicalForm [ ontolex:writtenRep ?v ] .
        }
        UNION
        {
            ?e ontolex:otherForm [ ontolex:writtenRep ?v ] .
        }
        ?e ontolex:otherForm|ontolex:canonicalForm [ ontolex:writtenRep ?f ] .
        ?lemma rdf:value ?f .
        ?lemma nifvec:isPhraseOf ?w .
        ?w rdf:type nifvec:Window .
        ?w nifvec:hasContext ?c .
        ?w nifvec:hasCount ?count .
        ?c nifvec:hasLeftValue ?l .
        ?c nifvec:hasRightValue ?r .
    }
}
GROUP BY ?v ?l ?r
ORDER BY DESC (?num)
"""
results_lemmas = list(g.query(q))

d_lemmas = defaultdict(Counter)
for r in results_lemmas:
    d_lemmas[r[0].value][(r[1].value, r[2].value)] = r[3].value 

with open('..//data//lemma_contexts_vectors.pickle', 'wb') as handle:
    pickle.dump(d_lemmas, handle, protocol=pickle.HIGHEST_PROTOCOL) 
```

```python
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

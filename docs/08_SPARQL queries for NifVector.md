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



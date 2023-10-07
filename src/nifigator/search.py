# -*- coding: utf-8 -*-

"""
"""

from collections import Counter, namedtuple
from datasketch import MinHashLSHEnsemble, MinHash, lshensemble
from .multisets import containment_index, merge_multiset
from .nifvecobjects import document_vector

MatchResult = namedtuple("MatchResult", ["score", "full_matches", "close_matches"])

class MinHashSearch:
    """

    param: base_vectors (dict): the base vectors from which to derive hashes

    params: documents (dict): set of documents

    params: minhash_dict (dict): minhash object that contains the minhashes (optional)

    param: num_perm (int): Number of random permutation functions.

    """
    def __init__(
        self,
        base_vectors: dict = None,
        documents: dict = None, 
        minhash_dict: dict = None,
        num_perm: int = 2**7,
        num_part: int = 2**5,
        threshold: float = 0.5,
        topn: int = 15,
    ) -> None:
        """
        """
        self.num_perm = num_perm
        self.num_part = num_part
        self.threshold = threshold
        self.topn = topn
        self.set_base_vectors(base_vectors)
        self.set_minhash_dict(minhash_dict)
        self.set_documents(documents)

    def set_base_vectors(self, base_vectors: dict=None):
        if base_vectors is not None:
            self.base_vectors = base_vectors

    def set_minhash_dict(self, minhash_dict: dict=None):
        if minhash_dict is None:
            self.minhash_dict = self.setup_vectors_minhash()
        else:
            self.minhash_dict = minhash_dict

    def set_documents(self, documents: dict=None):
        if documents is not None:
            self.documents = documents
            self.minhash_documents = self.merge_minhash(self.documents)
            self.lshensemble = self.create_lshensemble(self.documents)

    def setup_vectors_minhash(
        self,
    ):
        """
        """
        mh_dict = dict()
        for key, value in self.base_vectors.items():
            mh_dict[key] = MinHash(
                num_perm=self.num_perm
            )
            for ((item, count)) in value.most_common(self.topn):
                v = str(item).encode('utf8')
                mh_dict[key].update(v)
        return mh_dict

    def create_lshensemble(
        self,
        documents: dict=None
        ):
        """
        """
        lshensemble = MinHashLSHEnsemble(
            threshold=self.threshold, 
            num_perm=self.num_perm,
            num_part=self.num_part
        )
        lshensemble.index(
            [
                (key, self.minhash_documents[key], len(value.keys()))
                for key, value in documents.items()
            ]
        )
        return lshensemble

    def merge_minhash(
        self,
        documents: dict=None
    ):
        """

        param: document: a document dictionary (id and text)

        """
        mh = dict()
        for key, elements in documents.items():
            mh[key] = MinHash(num_perm=self.num_perm)
            for element in elements.keys():
                mh[key].merge(self.minhash_dict[element])
        return mh

    def get_scores(self,
        query: str=None,
    ):
        """
        """
        v = document_vector({'query': query}, self.base_vectors)
        minhash_query = MinHash(num_perm=self.num_perm)
        for element in v.keys():
            minhash_query.merge(self.minhash_dict[element])
        scores = dict()
        for doc in self.lshensemble.query(
            minhash_query, 
            len(v.keys())
        ):
            c1 = merge_multiset(v).keys()
            c2 = merge_multiset(self.documents[doc]).keys()
            scores[doc] = 1 - containment_index(c1, c2)
        scores = dict(sorted(scores.items(), key=lambda item: item[1]))
        return scores

    def matches(
        self,
        key1: str = None,
        key2: str = None,
        topn: int = 15
        ):
        """
        """
        # generate contexts of the text
        v1 = document_vector({'query': key1}, self.base_vectors, topn=topn)
        v2 = document_vector({'query': key2}, self.base_vectors, topn=topn)
        # find the full phrase matches of the text and the sentence
        full_matches = {
            p1: [(p2, 0)
            for p2, c2 in v2.items()
            if 1 - containment_index(c2, c1) == 0]
            for p1, c1 in v1.items()
        }
        full_matches = {key: value for key, value in full_matches.items() if value != []}
        # find the close phrase matches of the text and the sentence
        close_matches = {
            p1: [(p2, 1 - containment_index(c2, c1))
            for p2, c2 in v2.items()
            if 1 - containment_index(c2, c1) < 1 and 
               p1 not in full_matches.keys() and 
               p2 not in [p[0] for p in full_matches.values()]]
            for p1, c1 in v1.items()
        }
        close_matches = {key: sorted(value, key=lambda item: item[1]) for key, value in close_matches.items() if value!=[]}
        close_matches = dict(sorted(close_matches.items(), key=lambda item: item[1]))
        # calculate the containment index
        c1 = merge_multiset(v1)
        c2 = merge_multiset(v2)
        score = 1 - containment_index(c1, c2)
        return MatchResult(score, full_matches, close_matches)

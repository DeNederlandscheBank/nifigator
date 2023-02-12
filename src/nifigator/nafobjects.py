# -*- coding: utf-8 -*-

import logging
import datetime
from collections import OrderedDict, deque, namedtuple

from typing import Union

from lxml import etree

WordformElement = namedtuple("WfElement", "id sent para page offset length xpath text")

RAW_LAYER_TAG = "raw"
TEXT_LAYER_TAG = "text"
TEXT_OCCURRENCE_TAG = "wf"


class NafBase(object):
    def __init__(self):
        pass

    def get_attributes(self, data=None, namespace=None, exclude=list()):
        """ """
        if not isinstance(data, dict):
            data = data._asdict()
        for key, value in dict(data).items():
            if value is None:
                del data[key]
            if isinstance(value, datetime.datetime):
                data[key] = time_in_correct_format(value)
            if isinstance(value, float):
                data[key] = str(value)
            if isinstance(value, int):
                data[key] = str(value)
            if isinstance(value, list):
                del data[key]
        if namespace:
            for key, value in dict(data).items():
                qname = etree.QName("{" + namespace + "}" + key, key)
                del data[key]
                data[qname] = value
        for key in dict(data).keys():
            if key in exclude:
                del data[key]
        return data

    def layer(self, tree: etree._ElementTree = None, layer_tag: str = None):
        """ """
        layer = tree.find(layer_tag)
        if layer is None:
            layer = etree.SubElement(tree.getroot(), layer_tag)
        return layer

    def subelement(
        self,
        element: etree._Element = None,
        tag: str = None,
        data={},
        attributes_to_ignore: list = [],
    ):
        """ """
        if not isinstance(data, dict):
            data = data._asdict()

        data = dict(data)
        for attr in attributes_to_ignore:
            del data[attr]

        subelement = etree.SubElement(
            element,
            tag,
            self.get_attributes(data),
        )

        return subelement


class NafRawLayer(NafBase):
    """ """

    def __init__(self, raw: str = None):
        self.set_raw(raw)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        s = self._raw[0:500]
        if self._raw > 500:
            s += " ..."
        return s

    @property
    def raw(self):
        """
        Returns the raw text of the document
        """
        if self._raw is not None:
            return self._raw
        else:
            return None

    def set_raw(self, raw: str = None):
        """
        Sets the raw text of the document
        """
        self._raw = raw

    def write(self, tree: etree._ElementTree = None):
        """
        Add the raw layer to the xml tree
        """
        layer = tree.find(RAW_LAYER_TAG)
        if layer is None:
            layer = etree.SubElement(tree.getroot(), RAW_LAYER_TAG)
        layer.text = self._raw

    def parse(self, tree: etree._ElementTree = None):
        """
        Parse the raw layer from an xml tree
        """
        self._raw = self.find(RAW_LAYER_TAG).text


class NafHeaderLayer(NafBase):
    """ """

    def __init__(
        self,
        metadata: dict = None,
    ):
        self.set_metadata(metadata)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        if self._metadata is not None and self._metadata != {}:
            for d in self._metadata.keys():
                s += f"  {d} : {self._metadata[d]}\n"
        return s

    @property
    def metadata(self):
        return self._metadata

    def set_metadata(self, metadata):
        self._metadata = metadata

    def write(self, tree: etree._ElementTree = None):
        """ """

    def parse(self, tree: etree._ElementTree = None):
        """ """


class NafTextLayer(NafBase):
    """ """

    def __init__(self, wordforms: list[WordformElement] = None):
        self.set_wordforms(wordforms)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        s = ""
        return s

    @property
    def wordforms(self):
        return self._wordforms

    def set_wordforms(self, wordforms: list[WordformElement]):
        self._wordforms = wordforms

    def write(self, tree: etree._ElementTree = None):
        """ """
        for wordform in self._wordforms:
            wf = self.subelement(
                element=self.layer(tree, TEXT_LAYER_TAG),
                tag=TEXT_OCCURRENCE_TAG,
                data=wordform,
                attributes_to_ignore=["text"],
            )

            wf.text = (
                etree.CDATA(
                    wordform.text
                    if "]]>" not in wordform.text
                    else " " * len(wordform.text)
                )
                # if cdata
                # else wordform.text
            )

    def parse(self, tree: etree._ElementTree = None):
        """ """
        self._wordforms = [
            WordformElement(
                id=wordform.get("id", None),
                sent=wordform.get("sent", None),
                para=wordform.get("para", None),
                page=wordform.get("page", None),
                offset=wordform.get("offset", None),
                length=wordform.get("length", None),
                xpath=None,
                text=wordform.text,
            )
            for wordform in self.findall(TEXT_LAYER_TAG + "/" + TEXT_OCCURRENCE_TAG)
        ]


class NafTermsLayer(NafBase):
    """ """

    def __init__(
        self,
    ):
        pass

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        s = ""
        return s

    def write(self, tree: etree._ElementTree = None):
        """ """

    def parse(self, tree: etree._ElementTree = None):
        """ """


class NafEntitiesLayer(object):
    """ """

    def __init__(
        self,
    ):
        pass

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        s = ""
        return s

    def write(self, tree: etree._ElementTree = None):
        """ """

    def parse(self, tree: etree._ElementTree = None):
        """ """


class NafDepsLayer(object):
    """ """

    def __init__(
        self,
    ):
        pass

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        s = ""
        return s

    def write(self, tree: etree._ElementTree = None):
        """ """

    def parse(self, tree: etree._ElementTree = None):
        """ """

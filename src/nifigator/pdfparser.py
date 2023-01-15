# -*- coding: utf-8 -*-

import re
from collections import namedtuple
from io import BytesIO
from typing import Union

from lxml import etree
from pdfminer.converter import HTMLConverter, TextConverter, XMLConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage


class PDFDocument:
    def __init__(
        self, file: Union[str, BytesIO] = None, codec: str = "utf-8", password: str = ""
    ):

        """Function to convert pdf to xml or text
        Args:
            file: location or stream of the file to be converted
            codec: codec to be used to conversion
            password: password to be used for conversion
            params: the general params dict to store results
        Returns:
            str: the result of the conversion
        """

        self.PDF_offset = namedtuple("PDF_offset", ["beginIndex", "endIndex"])

        rsrcmgr = PDFResourceManager()
        retstr = BytesIO()
        laparams = LAParams()

        device = XMLConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)

        if isinstance(file, str):
            fp = open(file, "rb")
        else:
            fp = BytesIO(file)

        interpreter = PDFPageInterpreter(rsrcmgr, device)
        maxpages = 0
        caching = True
        pagenos = set()
        pages = 0
        for page in PDFPage.get_pages(
            fp,
            pagenos,
            maxpages=maxpages,
            password=password,
            caching=caching,
            check_extractable=False,
        ):
            interpreter.process_page(page)
            pages += 1
        # in case the file is opened, it is closed (a stream is not closed)
        if not isinstance(file, BytesIO):
            fp.close()
        device.close()

        result = retstr.getvalue()
        retstr.close()

        self.CONTROL = re.compile("[\x00-\x08\x0b-\x0c\x0e-\x1f]")

        self.tree = etree.fromstring(result)

    @property
    def text(self):
        text = []
        for page in self.tree:
            for textbox in page:
                if textbox.tag == "textbox":
                    for textline in textbox:
                        for text_element in textline:
                            text.append(text_element.text)
                    text.append("\n")
                elif textbox.tag == "figure":
                    for text_element in textbox:
                        text.append(text_element.text)
                elif textbox.tag == "textline":
                    for text_element in textbox:
                        text.append(text_element.text)
        text = "".join([t for t in text if t is not None])
        result = self.CONTROL.sub("", text)
        return result

    @property
    def page_offsets(self):
        page_offsets = []
        text = ""
        for page in self.tree:
            page_start = len(text)
            for textbox in page:
                if textbox.tag == "textbox":
                    for textline in textbox:
                        for text_element in textline:
                            if text_element.text is not None:
                                text += self.CONTROL.sub("", text_element.text)
                    text += "\n"
                elif textbox.tag == "figure":
                    for text_element in textbox:
                        if text_element.text is not None:
                            text += self.CONTROL.sub("", text_element.text)
                elif textbox.tag == "textline":
                    for text_element in textbox:
                        if text_element.text is not None:
                            text += self.CONTROL.sub("", text_element.text)
            page_end = len(text)
            page_offsets.append(self.PDF_offset(page_start, page_end))
        return page_offsets

    @property
    def paragraph_offsets(self):
        paragraph_offsets = []
        text = ""
        for page in self.tree:
            paragraph_start = len(text)
            for textbox in page:
                if textbox.tag == "textbox":
                    for textline in textbox:
                        for text_element in textline:
                            if text_element.text is not None:
                                text += self.CONTROL.sub("", text_element.text)
                        if (len(textline[-2].text.strip()) > 0) and (
                            textline[-2].text.strip()[-1] in [".", "?"]
                        ):
                            paragraph_end = len(text)
                            paragraph_offsets.append(
                                self.PDF_offset(paragraph_start, paragraph_end)
                            )
                            paragraph_start = len(text)
                    text += "\n"
                elif textbox.tag == "figure":
                    for text_element in textbox:
                        if text_element.text is not None:
                            text += self.CONTROL.sub("", text_element.text)
                elif textbox.tag == "textline":
                    for text_element in textbox:
                        if text_element.text is not None:
                            text += self.CONTROL.sub("", text_element.text)

        return paragraph_offsets

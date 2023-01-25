# -*- coding: utf-8 -*-

import regex
import logging
from collections import namedtuple
from io import BytesIO
from typing import Union

from lxml import etree
from pdfminer.converter import XMLConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage


class PDFDocument:
    def __init__(
        self,
        file: Union[str, BytesIO] = None,
        codec: str = "utf-8",
        password: str = "",
        laparams: LAParams = LAParams(),
        join_hyphenated_words=True,
    ):

        """Function to convert pdf to xml or text

        Args:

            file: location or stream of the file to be converted
            codec: codec to be used to conversion
            password: password to be used for conversion
            laparams: laparams for the pdfminer.six parser
            join_hyphenated_words: Join 'hyhen-\\n ated wor- \\nds' to 'hyphenated words'

        Returns:

        """
        self.join_hyphenated_words = join_hyphenated_words

        self.PDF_offset = namedtuple("PDF_offset", ["beginIndex", "endIndex"])

        rsrcmgr = PDFResourceManager()
        retstr = BytesIO()
        device = XMLConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)

        if isinstance(file, str):
            fp = open(file, "rb")
        else:
            fp = BytesIO(file)

        interpreter = PDFPageInterpreter(rsrcmgr, device)
        maxpages = 0
        caching = True
        pagenos = set()
        for page in PDFPage.get_pages(
            fp,
            pagenos,
            maxpages=maxpages,
            password=password,
            caching=caching,
            check_extractable=False,
        ):
            interpreter.process_page(page)

        # in case the file is opened, it is closed (a stream is not closed)
        if not isinstance(file, BytesIO):
            fp.close()
        device.close()

        result = retstr.getvalue()
        retstr.close()

        self.tree = etree.fromstring(result)

    @property
    def text(self):

        # setup regexes
        CONTROL = regex.compile("[\x00-\x08\x0b-\x0c\x0e-\x1f]")
        _hyphens = "\u00AD\u058A\u05BE\u0F0C\u1400\u1806\u2010\u2011\u2012\u2e17\u30A0-"
        _hyphen_newline = regex.compile(
            r"(?<=\p{L})[" + _hyphens + "][ \t\u00a0\r]*\n{1,2}[ \t\u00a0]*(?=\\p{L})"
        )

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

        # delete control characters
        text = CONTROL.sub("", text)

        # delete hyphens
        if self.join_hyphenated_words:
            text = _hyphen_newline.subn("", text)[0]

        return text

    @property
    def page_offsets(self):

        # setup regexes
        CONTROL = regex.compile("[\x00-\x08\x0b-\x0c\x0e-\x1f]")
        _hyphens = "\u00AD\u058A\u05BE\u0F0C\u1400\u1806\u2010\u2011\u2012\u2e17\u30A0-"
        _hyphen_newline = regex.compile(
            r"(?<=\p{L})[" + _hyphens + "][ \t\u00a0\r]*\n{1,2}[ \t\u00a0]*(?=\\p{L})"
        )

        page_offsets = []
        text = ""
        page_start_correction = 0
        page_end_correction = 0
        for page in self.tree:
            page_start = len(text)
            for textbox in page:
                if textbox.tag == "textbox":
                    for textline in textbox:
                        for text_element in textline:
                            if text_element.text is not None:
                                text += CONTROL.sub("", text_element.text)
                    text += "\n"
                elif textbox.tag == "figure":
                    for text_element in textbox:
                        if text_element.text is not None:
                            text += CONTROL.sub("", text_element.text)
                elif textbox.tag == "textline":
                    for text_element in textbox:
                        if text_element.text is not None:
                            text += CONTROL.sub("", text_element.text)
            page_end = len(text)

            if self.join_hyphenated_words:
                # retrieve all hyphens in text and calculate correction
                text_hyphens = regex.finditer(_hyphen_newline, text)
                page_end_correction = sum(
                    [hyphen.end() - hyphen.start() for hyphen in text_hyphens]
                )
                if logging.DEBUG and page_end_correction > 0:
                    logging.debug(
                        "nifigator.pdfparser.page_offsets: page_start "
                        + str(page_start)
                        + " corrected with "
                        + str(page_start_correction)
                    )
                    logging.debug(
                        "nifigator.pdfparser.page_offsets: page_end   "
                        + str(page_end)
                        + " corrected with "
                        + str(page_end_correction)
                    )
                # append corrected page offsets
                page_offsets.append(
                    self.PDF_offset(
                        page_start - page_start_correction,
                        page_end - page_end_correction,
                    )
                )
                # set page_start_correction for next page
                page_start_correction = page_end_correction
            else:
                # append page offsets
                page_offsets.append(self.PDF_offset(page_start, page_end))

        return page_offsets

    # @property
    # def paragraph_offsets(self):
    #     paragraph_offsets = []
    #     text = ""
    #     for page in self.tree:
    #         paragraph_start = len(text)
    #         for textbox in page:
    #             if textbox.tag == "textbox":
    #                 for textline in textbox:
    #                     for text_element in textline:
    #                         if text_element.text is not None:
    #                             text += self.CONTROL.sub("", text_element.text)
    #                     if (len(textline[-2].text.strip()) > 0) and (
    #                         textline[-2].text.strip()[-1] in [".", "?"]
    #                     ):
    #                         paragraph_end = len(text)
    #                         paragraph_offsets.append(
    #                             self.PDF_offset(paragraph_start, paragraph_end)
    #                         )
    #                         paragraph_start = len(text)
    #                 text += "\n"
    #             elif textbox.tag == "figure":
    #                 for text_element in textbox:
    #                     if text_element.text is not None:
    #                         text += self.CONTROL.sub("", text_element.text)
    #             elif textbox.tag == "textline":
    #                 for text_element in textbox:
    #                     if text_element.text is not None:
    #                         text += self.CONTROL.sub("", text_element.text)

    #     return paragraph_offsets

# -*- coding: utf-8 -*-

import sys

if sys.version_info[:2] >= (3, 8):
    # TODO: Import directly (no need for conditional) when `python_requires = >= 3.8`
    from importlib.metadata import PackageNotFoundError, version  # pragma: no cover
else:
    from importlib_metadata import PackageNotFoundError, version  # pragma: no cover

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__
    __version__ = version(dist_name)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.1.19"
finally:
    del version, PackageNotFoundError

from .const import *
from .converters import *
from .nifgraph import *
from .nifobjects import *
from .nifvecobjects import *
from .nafobjects import *
from .pdfparser import *
from .utils import *
from .lemongraph import *
from .lemonobjects import *
from .multisets import *
from. search import *

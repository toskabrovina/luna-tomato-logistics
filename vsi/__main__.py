"""Lets the copied folder work without installing: `python -m vsi list`."""

import sys

from .cli import main

sys.exit(main())

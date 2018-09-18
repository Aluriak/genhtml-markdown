# Default header, importing many recurrent packages
import itertools
import functools
import collections
try:
    import plotly.offline as offline
    import plotly.graph_objs as go
except ImportError:
    pass
try:
    import pandas as pd
except ImportError:
    pass
try:
    import networkx as nx
except ImportError:
    pass
try:
    import clyngor
except ImportError:
    pass

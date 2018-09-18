#!/usr/bin/env python
"""
    [plotly][] Extension for [Python-Markdown][]
    ==============================================

    This plugin implements a block extension which can be used to specify
    a [plotly][] chart which will be converted into an HTML element and inserted in the document.
    Code is heavily inspired by [PlantUML][].

    Syntax:

        ::plot:: [format="div|png|svg"] [alt="text for alt"]
            plotly python script
        ::end-plot::

    Example:

        ::plot:: format="png" alt="My super scatter plot in png"
            data = go.Scatter(x=[1, 2, 3, 4], y=[4, 3, 2, 1])
            layout = go.Layout(title="hello world")
        ::end-plot::

    Options are optional, but if present must be specified in the order format, alt.
    The option value may be enclosed in single or double quotes.

    Installation
    ------------
    You need to install [plotly][] (`pip install plotly` or alike).

    [Python-Markdown]: http://pythonhosted.org/Markdown/
    [PlantUML]: http://plantuml.sourceforge.net/
    [plotly]: https://plot.ly/python
"""

import os
import re
import base64
import textwrap
from subprocess import Popen, PIPE
import logging
import markdown
from markdown.util import etree, AtomicString


__version__ = '1.0.0'
logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)


# For details see https://pythonhosted.org/Markdown/extensions/api.html#blockparser
class PlotPreprocessor(markdown.preprocessors.Preprocessor):
    # Regular expression inspired from fenced_code
    args_reg = r'''
        # args
        \s*(format=(?P<quotformat>"|')(?P<format>\w+)(?P=quotformat))?
        \s*(alt=(?P<quotalt>"|')(?P<alt>[\w\s"']+)(?P=quotalt))?
        \s*\n
    '''.strip()
    BLOCK_RE = re.compile(r'''
        ::plot::
        ''' + args_reg + '''
        (?P<code>.*?)(?<=\n)
        ::end-plot::[ ]*$
        ''', re.MULTILINE | re.DOTALL | re.VERBOSE)

    # FENCED_BLOCK_RE = re.compile(r'''
        # (?P<fence>^(?:~{3,}|`{3,}))[ ]*         # Opening ``` or ~~~
        # (\{?\.?plot)[ ]*                 # Optional {, and lang
        # ''' + args_reg + '''
        # [ ]*
        # }?[ ]*\n                                # Optional closing }
        # (?P<code>.*?)(?<=\n)
        # (?P=fence)[ ]*$
        # ''', re.MULTILINE | re.DOTALL | re.VERBOSE)

    def __init__(self, md):
        super().__init__(md)
        self.build_configs()

    def run(self, lines):
        text = '\n'.join(lines)
        did_replace = True

        while did_replace:
            text, did_replace = self._replace_block(text)

        return text.split('\n')

    def _replace_block(self, text):
        # Parse configuration params
        # m = self.FENCED_BLOCK_RE.search(text)
        # if not m:
        m = self.BLOCK_RE.search(text)
        if not m:
            return text, False

        # Parse configuration params
        img_format = m.group('format') if m.group('format') else self.config['format']
        alt = m.group('alt') if m.group('alt') else self.config['alt']

        # Extract plot source and convert it
        code = m.group('code')
        plot_code = self.generate_plot(code, img_format)

        if img_format == 'png':
            data = 'data:image/png;base64,{}'.format(
                base64.b64encode(plot_code).decode('ascii')
            )
            img = etree.Element('img')
            img.attrib['src'    ] = data
            img.attrib['classes'] = classes
            img.attrib['alt'    ] = alt
            img.attrib['title'  ] = title
        elif img_format == 'svg':
            # Firefox handles only base64 encoded SVGs
            data = 'data:image/svg+xml;base64,{0}'.format(
                base64.b64encode(plot_code).decode('ascii')
            )
            img = etree.Element('img')
            img.attrib['src'    ] = data
            img.attrib['classes'] = classes
            img.attrib['alt'    ] = alt
            img.attrib['title'  ] = title
        elif img_format == 'div':
            pass  # plot_code is already HTML

        return text[:m.start()] + plot_code + text[m.end():], True

    def generate_plot(self, python_code:str, img_format):
        python_code = '\n'.join((
            self.imports,
            textwrap.dedent(python_code),
            self.footer[img_format]
        ))
        outputs = {}
        exec(python_code, outputs)
        if 'output' in outputs:
            return outputs['output']
        else:
            logger.warning('Plot code do not define any output…')
            return 'INVALID PLOT CODE:\n' + python_code


    def build_configs(self):
        self.imports = textwrap.dedent(
        '''
            import plotly.offline as offline
            import plotly.graph_objs as go
            try:
                import pandas as pd
            except ImportError:
                pass
        ''')
        self.footer = {
            'div': textwrap.dedent(
                '''
                    figure = go.Figure(data=[data], layout=layout)
                    output = offline.plot(figure, output_type='div')
                ''')
        }


# For details see https://pythonhosted.org/Markdown/extensions/api.html#extendmarkdown
class PlotMarkdownExtension(markdown.Extension):
    # For details see https://pythonhosted.org/Markdown/extensions/api.html#configsettings
    def __init__(self, *args, **kwargs):
        self.config = {
            'alt': ["plot", "Text to show when image is not available. Defaults to 'plot'."],
            'format': ["div", "Format of image to generate (div, png, svg). Defaults to 'div'."],
        }
        super().__init__(*args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        blockprocessor = PlotPreprocessor(md)
        blockprocessor.config = self.getConfigs()
        # need to go before both fenced_code_block and things like retext's PosMapMarkPreprocessor
        md.preprocessors.add('plot', blockprocessor, '_begin')


def makeExtension(*args, **kwargs):
    return PlotMarkdownExtension(*args, **kwargs)

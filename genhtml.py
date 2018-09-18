#!/usr/bin/env python
"""
    Programmable HTML Extension for [Python-Markdown][]
    ==============================================

    This plugin implements a block extension which can be used to build page content using python.
    The python code will be converted into an HTML element and inserted in the document.
    Code is heavily inspired by [plot-markdown][].

    Example:

        ::genhtml:: header=none footer=none
            print('<b> hello ! </b>')
        ::end-genhtml::

    Header and footer are name of pre-configured set of imports and exports to do.

    Installation
    ------------
    `pip install genhtml-markdown`.

    [Python-Markdown]: http://pythonhosted.org/Markdown/
    [plot-markdown]: https://github.com/aluriak/plot-markdown
"""

import os
import io
import re
import glob
import textwrap
import traceback
import contextlib
import logging
import markdown
from markdown.util import etree, AtomicString


__version__ = '1.0.4.dev0'
FALSY_VALUES = {'0', 'no', 'false', 'f'}
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def gen_headfoots_from_dir(directory:str) -> [(str, str)]:
    """Yield pairs (name, lines) of headers/footers found in given directory"""

    def filter_first_comments(it:[str]) -> [str]:
        "Ignore lines while starting with #, then yield all remaining lines"
        it = iter(it)
        for line in it:
            if not line.startswith('#'):
                yield line
                break
        yield from it

    for headerfile in glob.glob(os.path.join(directory, '*.py')):
        header_name = os.path.splitext(os.path.basename(headerfile))[0]
        with open(headerfile) as fd:
            header_lines = ''.join((filter_first_comments(fd)))
        yield header_name, header_lines


# For details see https://pythonhosted.org/Markdown/extensions/api.html#blockparser
class GenHTMLPreprocessor(markdown.preprocessors.Preprocessor):
    # Regular expression inspired from fenced_code
    BLOCK_RE = re.compile(r'''
        ^::genhtml:: (?P<args>[=\w'" -]*)\s*\n
        (?P<code>.*?)(?<=\n)
        ^::end-genhtml::[ ]*$
        ''', re.MULTILINE | re.DOTALL | re.VERBOSE)

    def __init__(self, md):
        super().__init__(md)

    def run(self, lines):
        text = '\n'.join(lines)
        did_replace = True

        while did_replace:
            text, did_replace = self._replace_block(text)

        return text.split('\n')

    def _replace_block(self, text):
        # Parse block
        m = self.BLOCK_RE.search(text)
        if not m:
            return text, False

        # Parse arguments
        ARG_RE = re.compile(r'''(?P<field>[\w-]+)=(?P<quote>"|'|)(?P<value>[a-zA-Z0-9,]+)(?P=quote)''')
        header, footer, interpret = '', '', True
        for key, _, value in ARG_RE.findall(m.group('args')):
            if key == 'header':
                header = value.strip().strip('"\'')
            elif key == 'footer':
                footer = value.strip().strip('"\'')
            elif key == 'interpret':
                interpret = value.lower() not in FALSY_VALUES
            else:
                logger.warning(f"Unrecognized option '{key}' with value '{value}'")

        raw_code = self.generate_python_code(m.group('code'), header.split(','), footer.split(','))
        if interpret:
            raw_html = self.generate_html(raw_code)
            return text[:m.start()] + raw_html + text[m.end():], True
        else:  # just show python code
            return text[:m.start()] + textwrap.indent(raw_code, ' '*4) + text[m.end():], True


    def generate_html(self, python_code:str) -> str:
        fd = io.StringIO()
        with contextlib.redirect_stdout(fd):
            try:
                exec(python_code, {}, {})
            except Exception as err:
                tb = traceback.format_exc()
                logger.warning(f"{type(err).__name__} raised by python code. Will be printed in output:\n{tb}")
                return textwrap.indent(tb, ' '*4)
        return fd.getvalue()

    def generate_python_code(self, python_code:str, headers:[str], footers:[str]) -> str:
        return '\n'.join((
            *(self.header.get(header, '') for header in headers),
            textwrap.dedent(python_code),
            *(self.footer.get(footer, '') for footer in footers)
        ))


    def build_configs(self):
        "Load default and custom headers/footers in memory"
        self.header = dict(gen_headfoots_from_dir('headers'))
        self.footer = dict(gen_headfoots_from_dir('footers'))
        if self.config.get('headers_dir'):
            logger.info(f"Load custom headers in {self.config['headers_dir']}")
            self.header.update(dict(gen_headfoots_from_dir(self.config['headers_dir'])))
        if self.config.get('footers_dir'):
            logger.info(f"Load custom footers in {self.config['footers_dir']}")
            self.footer.update(dict(gen_headfoots_from_dir(self.config['footers_dir'])))
        self.header[''] = self.header['default']
        self.footer[''] = self.footer['default']
        self.header['none'] = ''
        self.footer['none'] = ''


# For details see https://pythonhosted.org/Markdown/extensions/api.html#extendmarkdown
class GenHTMLMarkdownExtension(markdown.Extension):
    # For details see https://pythonhosted.org/Markdown/extensions/api.html#configsettings
    def __init__(self, *args, **kwargs):
        self.config = {
            'headers_dir': ['', "Directory containing custom python headers."],
            'footers_dir': ['', "Directory containing custom python footers."],
        }
        super().__init__(*args, **kwargs)

    def extendMarkdown(self, md, md_globals):
        blockprocessor = GenHTMLPreprocessor(md)
        blockprocessor.config = self.getConfigs()
        blockprocessor.build_configs()
        md.preprocessors.add('genhtml', blockprocessor, '_begin')


def makeExtension(*args, **kwargs):
    return GenHTMLMarkdownExtension(*args, **kwargs)

#!/usr/bin/env python
"""
    Programmable HTML Extension for [Python-Markdown][]
    ==============================================

    This plugin implements a block extension which can be used to build page content using python.
    The python code will be converted into an HTML element and inserted in the document.
    Code is heavily inspired by [plot-markdown][].

    Example:

        ```genhtml header=none footer=none
        print('<b> hello ! </b>')
        ```

    Header and footer are name of pre-configured code
    that will be added respectively before and after the code.

    Options:

        header -- header to use. You can combine with comma
        footer -- footer to use. You can combine with comma
        interpret -- if set to false, will show the code instead of its results
        global-env -- if set to true, the python code will use the global environment.
        isolate-env -- if set to true, the python code will not modify the global environment
        format -- define how to understand the code output. Default is html.
        alt -- when producing images (see format), define the alt text
        title -- when producing images (see format), define the title text

    The global environment is, at the beginning of the parsing, empty.
    It will be updated by all python codes. As a consequence, you can use
    the global environment to use data computed by scripts before the one you write.

    The format parameter is by default html.
    Other possible values are png and svg. Note that the python code should not just
    print raw png/svg data, but must first encode it in base64
    with the standard module of the same name.

    Installation
    ------------
    `pip install genhtml-markdown`.

    [Python-Markdown]: http://pythonhosted.org/Markdown/
    [plot-markdown]: https://github.com/aluriak/plot-markdown
"""

import os
import io
import re
import copy
import glob
import base64
import logging
import textwrap
import traceback
import contextlib
import pkg_resources
import markdown
from functools import partial
from markdown.util import etree, AtomicString


FALSY_VALUES = {'0', 'no', 'false', 'f'}
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def raw_to_b64image(raw:str, alt:str='', title:str='', format:str='png') -> str:
    "Return given raw data (understood as base64-encoded png) as an HTML-ready png image"
    data = f'data:image/{format};base64,{raw.strip()}'
    alt = f' alt="{alt}"' if alt else ''
    title = f' title="{title}"' if title else ''
    return f'<img src="{data}"{alt}{title} />'
def raw_to_raw(raw:str, alt:str='', title:str='', format:str='png') -> str:
    "Return raw as-is, whatever the other arguments are. Mocking behavior of raw_to_* functions"
    return raw

DATA_FORMATS = {
    'png': partial(raw_to_b64image, format='png'),
    'jpg': partial(raw_to_b64image, format='jpg'),
    'svg': partial(raw_to_b64image, format='svg+xml'),
    'html': raw_to_raw,
    'markdown': raw_to_raw,
}

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
        ^```gen(html|mark) (?P<args>[=\w'" +,_-]*)\s*\n
        (?P<code>.*?)(?<=\n)
        ^``` *$
        ''', re.MULTILINE | re.DOTALL | re.VERBOSE)

    def __init__(self, md):
        super().__init__(md)

    def run(self, lines):
        self.__global_env = {}
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
        ARG_RE = re.compile(r'''(?P<field>[\w-]+)=(?P<quote>"|'|)(?P<value>[a-zA-Z0-9,+_-]+)(?P=quote)''')
        header, footer, interpret, dataformat, alt, title = '', '', True, 'html', '', ''
        use_global_env, isolate_env = False, False
        for key, _, value in ARG_RE.findall(m.group('args')):
            if key == 'header':
                header = value.strip().strip('"\'')
            elif key == 'footer':
                footer = value.strip().strip('"\'')
            elif key == 'interpret':
                interpret = value.lower() not in FALSY_VALUES
            elif key == 'format':
                dataformat = value.lower()
                if dataformat not in DATA_FORMATS:
                    logger.warning(f"Unrecognized format '{dataformat}'. 'html' will be used instead")
                    dataformat = 'html'
            elif key == 'alt':
                alt = value.strip('\'"')
            elif key == 'title':
                title = value.strip('\'"')
            elif key in {'global-env', 'global'}:
                use_global_env = value.lower() not in FALSY_VALUES
            elif key in {'isolate-env', 'isolated-env', 'isolated'}:
                isolate_env = value.lower() not in FALSY_VALUES
            else:
                logger.warning(f"Unrecognized option '{key}' with value '{value}'")

        raw_code = self.generate_python_code(m.group('code'), header.split(','), footer.split(','))
        if interpret:
            raw_html = self.generate_html(raw_code, dataformat, use_global_env, isolate_env, alt, title)
            return text[:m.start()] + raw_html + text[m.end():], True
        else:  # just show python code
            return text[:m.start()] + textwrap.indent(raw_code, ' '*4) + text[m.end():], True


    def generate_html(self, python_code:str, format:str, use_global_env:bool,
                      isolate_env:bool, alt:str, title:str) -> str:
        fd = io.StringIO()
        env = self.__global_env if use_global_env else {}
        if isolate_env:
            env = copy.deepcopy(env)
        with contextlib.redirect_stdout(fd):
            try:
                # see https://docs.python.org/3/library/functions.html#exec for params duplication
                exec(python_code, env, env)
            except Exception as err:
                tb = traceback.format_exc()
                logger.warning(f"{type(err).__name__} raised by python code. Will be printed in output:\n{tb}")
                ret = textwrap.indent(tb, ' '*4)
            else:
                ret = DATA_FORMATS[format](fd.getvalue(), alt, title)
        if not isolate_env:
            self.__global_env.update(env)
        return ret

    def generate_python_code(self, python_code:str, headers:[str], footers:[str]) -> str:
        return '\n'.join((
            *(self.header.get(header, '') for header in headers),
            textwrap.dedent(python_code),
            *(self.footer.get(footer, '') for footer in footers)
        ))


    def build_configs(self):
        "Load default and custom headers/footers in memory"
        header_libdir = pkg_resources.resource_filename('genhtml', 'headers/')
        footer_libdir = pkg_resources.resource_filename('genhtml', 'footers/')
        self.header = dict(gen_headfoots_from_dir(header_libdir))
        self.footer = dict(gen_headfoots_from_dir(footer_libdir))
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

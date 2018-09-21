"""Run tests for available examples.

An available example is a .mkd file found in examples/ that also exist as .test.
.test files are HTML files.
Since some examples are non-deterministic, it's is not possible to just read the HTML.
Hence, the presence of a .test file indicate that the example is testable
and the content provides the expected data.

"""

import os
from glob import glob
import genhtml
from markdown import markdown as markdown_compiler


def gen_examples() -> [str, str, str]:
    for testfile in glob('examples/*.test'):
        markfile = os.path.splitext(testfile)[0] + '.mkd'
        testname = os.path.basename(os.path.splitext(testfile)[0])
        assert os.path.exists(markfile)
        with open(markfile) as fd:
            markdown = fd.read()
        with open(testfile) as fd:
            html = fd.read()
        yield testname, markdown, html


def template_test_example(markdown:str, expected_html:str):
    html = markdown_compiler(markdown, extensions=['genhtml'])
    assert html.rstrip() == expected_html.rstrip()  # handle (un)voluntary eol at the eof


for testname, markdown, expected_html in gen_examples():
    globals()['test_' + testname] = lambda: template_test_example(markdown, expected_html)

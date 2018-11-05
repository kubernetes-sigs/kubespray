import os
import sys

sys.path.append('..')
import mitogen
VERSION = '%s.%s.%s' % mitogen.__version__

author = u'David Wilson'
copyright = u'2018, David Wilson'
exclude_patterns = ['_build']
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.intersphinx', 'sphinxcontrib.programoutput']
html_show_sourcelink = False
html_show_sphinx = False
html_sidebars = {'**': ['globaltoc.html', 'github.html']}
html_static_path = ['_static']
html_theme = 'alabaster'
html_theme_options = {
    'font_family': "Georgia, serif",
    'head_font_family': "Georgia, serif",
}
htmlhelp_basename = 'mitogendoc'
intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}
language = None
master_doc = 'toc'
project = u'Mitogen'
pygments_style = 'sphinx'
release = VERSION
source_suffix = '.rst'
templates_path = ['_templates']
todo_include_todos = False
version = VERSION

rst_epilog = """

.. |mitogen_version| replace:: %(VERSION)s

.. |mitogen_url| replace:: `mitogen-%(VERSION)s.tar.gz <https://files.pythonhosted.org/packages/source/m/mitogen/mitogen-%(VERSION)s.tar.gz>`__

""" % locals()

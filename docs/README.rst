Omnia Documentation
-------------------

**Omnia** is an open source project hosted on `GitHub <https://github.com/dell/omnia>`_. Go to `GitHub <https://github.com/dell/omnia>`_ to view the source, open issues, ask questions, and participate in the project.

The Omnia docs are hosted here: https://omnia-doc.readthedocs.io/en/latest/index.html and are written in reStructuredText (`.rst`).

Building Docs
--------------

* Clone this project

* Install or update sphinx (See: https://pip.readthedocs.io/) ::

    pip install sphinx

or::

   pip install sphinx --upgrade


* Install ReadTheDocs theme::

   pip install sphinx_rtd_theme


* Build the Docs::

   cd omnia/docs
   make html


* View the documentation by pointing a browser to: ``omnia/docs/build/html/index.html``
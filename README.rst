
Usage
============

Output files
------------------------

.. code-block:: bash

  $ ./renderers.py

Files output to `./outputs/`.

Update
-------------------------

.. code-block:: bash

  $ git submodule update ./git


Files
=============

:templates/: Golang template files directory.
:outputs/: Golang files output directory.
:texts.py: It parses usage help from `git` documents.
:analyzers.py: It analysizes help texts.
:fixers.py: It arranges help texts.
:renderers.py: It renders and creates golang files.

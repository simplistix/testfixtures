%PYTHON_EXE% bootstrap.py
bin\buildout -d
bin\nosetests --with-xunit

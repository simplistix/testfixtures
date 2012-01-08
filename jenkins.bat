%PYTHON_EXE% bootstrap.py
CHOICE /T 10 /C w /D w
bin\buildout
bin\nosetests --with-xunit

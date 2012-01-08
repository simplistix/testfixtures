%PYTHON_EXE% bootstrap.py -d
bin\buildout
CHOICE /T 10 /C w /D w
bin\nosetests --with-xunit

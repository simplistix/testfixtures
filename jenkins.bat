%PYTHON_EXE% bootstrap.py
CHOICE /T 20 /C w /D w
bin\buildout
bin\nosetests --with-xunit --with-cov --cov=testfixtures --cov-report=xml
bin\docpy setup.py sdist

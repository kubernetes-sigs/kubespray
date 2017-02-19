venv: venv/bin/activate

venv/bin/activate: requirements.txt
	test -d venv || virtualenv --no-setuptools -p `which python` venv
	. venv/bin/activate; pip install -r requirements.txt

clean:
	$(RM) -rf venv
	find . -name "*.pyc" -exec $(RM) -rf {} \;

.PHONY:clean venv

.PHONY: test clean

test:
	python -m pytest -q

clean:
	rm -rf .pytest_cache dist build
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +

format: refractr/ tests/ bin/
	@poetry run black $^
	@poetry run isort $^

.PHONY: format

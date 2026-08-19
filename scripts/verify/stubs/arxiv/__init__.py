"""minimal arxiv stub for offline smoke test"""
from typing import Any


class SortCriterion:
    Relevance = "relevance"
    SubmittedDate = "submittedDate"
    LastUpdatedDate = "lastUpdatedDate"


class Search:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs


class Result:
    title = "stub paper"
    summary = "stub summary"
    entry_id = "http://arxiv.org/abs/0000.00000"
    pdf_url = "http://arxiv.org/pdf/0000.00000"
    published = None

    def __init__(self) -> None:
        self.authors = [type("A", (), {"name": "Author"})()]


class Client:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def results(self, search: Search) -> list[Result]:
        return [Result()]

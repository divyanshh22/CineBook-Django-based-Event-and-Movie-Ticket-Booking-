from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    """Default pagination used across the API.

    Response shape:
        {
            "count": 124,
            "next": "...?page=3",
            "previous": "...?page=1",
            "results": [...]
        }
    """

    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 100

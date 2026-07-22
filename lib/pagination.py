from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class AllowAllPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 1000

    def paginate_queryset(self, queryset, request, view=None):
        if request and request.query_params.get("all") == "1":
            self.request = request
            return list(queryset)
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        request = self.request
        if request and request.query_params.get("all") == "1":
            return Response(data)
        return Response({
            "count": self.page.paginator.count,
            "page": self.page.number,
            "results": data,
        })

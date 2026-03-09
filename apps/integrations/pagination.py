from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class EnvelopePagination(PageNumberPagination):
    def get_paginated_response(self, data):
        meta = {
            'total_pages': self.page.paginator.num_pages,
            'page': self.page.number,
            'total_count': self.page.paginator.count,
        }
        return Response({'data': data, 'errors': [], 'meta': meta})


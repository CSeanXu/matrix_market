from django.http.response import JsonResponse
from django.views.decorators.cache import cache_page

from market.crawler import crawl_ticker


@cache_page(10 * 1)  # seconds
def ticker(request):
    _ticker = crawl_ticker()

    json = {
        "status": "success" if _ticker else "fail",
        "data": _ticker
    }

    return JsonResponse(json)

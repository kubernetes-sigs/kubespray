from django.http import HTTPResponse


def index(request):
    return HTTPResponse('hello, world')


def shutdown(request):
     raise KeyboardInterrupt

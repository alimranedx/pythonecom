from django.http import HttpResponse

def index(request):
    return HttpResponse("Hello Product Page")

# Create your views here.

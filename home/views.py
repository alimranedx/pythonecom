from django.http import HttpResponse

def index(request):
    return HttpResponse("Hello home page")

# Create your views here.

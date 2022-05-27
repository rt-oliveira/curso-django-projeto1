from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def home(request):
    return render(request, 'recipes/home.html', {
        'name': 'Rafael',
    })

def contato(request):
    return HttpResponse('Contato')

def sobre(request):
    return HttpResponse('Sobrea')
from .models import Movie
from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    search_term = request.GET.get('searchMovie')
    if search_term:
        movies = Movie.objects.filter(title__icontains=search_term)
    else:
        movies = Movie.objects.all()
    return render(request, 'home.html', {'movies': movies})

def about(request):
    return HttpResponse('<h1>About us</h1>')

def signup(request):
    email = request.GET.get('email')
    return render(request, 'signup.html', {'email': email})
from django.shortcuts import render

from movie.models import Movie
from .models import News
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from django.db.models import Count
from io import BytesIO
import base64


def news(request):
    newss = News.objects.all().order_by('-date')
    return render(request, 'news.html', {'newss': newss})

def statistics_view(request):
    # Movies per year
    year_data = (Movie.objects
                 .exclude(year__isnull=True)
                 .values('year')
                 .annotate(total=Count('id'))
                 .order_by('year'))
    years = [d['year'] for d in year_data]
    counts = [d['total'] for d in year_data]

    plt.figure(figsize=(10,4))
    plt.bar(years, counts)
    plt.title('Movies per Year')
    plt.xlabel('Year')
    plt.ylabel('Count')
    plt.xticks(rotation=90)
    plt.tight_layout()
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)
    graphic_year = base64.b64encode(buffer.read()).decode()

    # Movies per genre (first genre only)
    genres = {}
    for m in Movie.objects.exclude(genre__exact=''):
        g = m.genre.split(',')[0].strip()
        genres[g] = genres.get(g, 0) + 1

    plt.figure(figsize=(10,4))
    plt.bar(genres.keys(), genres.values())
    plt.title('Movies per Genre')
    plt.xlabel('Genre')
    plt.ylabel('Count')
    plt.xticks(rotation=45)
    plt.tight_layout()
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    buffer.seek(0)
    graphic_genre = base64.b64encode(buffer.read()).decode()

    return render(request, 'statistics.html',
                  {'graphic_year': graphic_year,
                   'graphic_genre': graphic_genre})
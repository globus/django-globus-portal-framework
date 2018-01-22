from django.shortcuts import render


def index(request):
    context = {'user': 'anonymous'}
    return render(request, 'search.html', context)

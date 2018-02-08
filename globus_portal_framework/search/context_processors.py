from django.conf import settings


def globals(request):
    return {
        'project_title': settings.PROJECT_TITLE
    }

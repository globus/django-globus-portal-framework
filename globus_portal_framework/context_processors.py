from django.conf import settings


def globals(request):
    return {
        'project_title': getattr(settings, 'PROJECT_TITLE',
                                 'Globus Portal Framework'),
        'auth_enabled': bool('social_django' in settings.INSTALLED_APPS)
    }

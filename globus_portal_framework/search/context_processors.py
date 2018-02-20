from globus_portal_framework.search import settings


def globals(request):
    return {
        'project_title': settings.PROJECT_TITLE
    }

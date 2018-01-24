"""globus_portal_framework URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # We will likely use this at some point
    path('admin/', admin.site.urls),
    # Social auth provides /login /logout. Provides no default urls
    path('', include('social_django.urls')),
    path('', include('django.contrib.auth.urls')),
    # Globus search portal. Provides default url '/'.
    path('', include('globus_portal_framework.search.urls'))
]

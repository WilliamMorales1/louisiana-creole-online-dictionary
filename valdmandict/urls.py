from django.contrib import admin
from django.urls import path
from creoledict import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('search/', views.search_dictionary, name='search_dictionary'),
]

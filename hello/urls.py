from django.urls import path
from . import views


app_name='session'
urlpatterns = [
    path('', views.sessfun, name="sessfun"),

]


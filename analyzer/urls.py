from django.urls import path

from .views import (index, fetch_windy_data, fetch_weatherapp_data,
                    fetch_weatherapi_data, getweather, fetch_weatherbit_data,
                    fetch_virtualcrossing_data, fetch_open_meteo_data, about, compare_temperatures)

app_name = "analyzer"

urlpatterns = [
    path("", index, name="index"),
    path("windy/", fetch_windy_data, name="windy"),
    path("open-weather-map/", fetch_weatherapp_data, name="open_weather_map"),
    path("weather-api/", fetch_weatherapi_data, name="weather_api"),
    path("python-weather/", getweather, name="python_weather"),
    path("weather-bit/", fetch_weatherbit_data, name="weather-bit"),
    path("virtualcrossing/", fetch_virtualcrossing_data, name="virtualcrossing"),
    path("open-meteo/", fetch_open_meteo_data, name="open-meteo"),
    path("about/", about, name="about"),
    path('compare_temperatures/', compare_temperatures, name='compare_temperatures'),
]
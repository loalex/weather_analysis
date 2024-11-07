from django.urls import path

from .views import index, fetch_windy_data, fetch_weatherapp_data, fetch_weatherapi_data, getweather

app_name = "analyzer"

urlpatterns = [
    path("", index, name="index"),
    path("windy/", fetch_windy_data, name="windy"),
    path("open-weather-map/", fetch_weatherapp_data, name="open_weather_map"),
    path("weather-api/", fetch_weatherapi_data, name="weather_api"),
    path("python-weather/", getweather, name="python_weather"),

]
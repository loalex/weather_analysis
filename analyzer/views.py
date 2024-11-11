import urllib
from datetime import datetime
import json

import python_weather
import requests

from django.shortcuts import render

from weatherapi import WeatherPoint
from weatherbit.api import Api


from open_meteo import OpenMeteo
from open_meteo.models import DailyParameters, HourlyParameters


def index(request):
    return render(request, "index.html")


def fetch_windy_data(request):
    API_KEY = "tvt0g6AqPDQ5tYN2e58BAVvAoRrjAaH3"
    API_URL = "https://api.windy.com/api/point-forecast/v2"

    headers = {
        'Content-Type': 'application/json',
    }

    payload = {
        "lat": 54.516,
        "lon": 18.556,
        "model": "gfs",
        "parameters": ["wind", "dewpoint", "rh", "pressure"],
        "levels": ["surface", "800h", "300h"],
        "key": API_KEY
    }

    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            data = response.json()
            time_from_timestamp = []
            print(f"{data['ts']=}")
            for element in data['ts']:
                time_from_timestamp.append(datetime.fromtimestamp(element / 1000))
            print(f"{time_from_timestamp=}")

            return render(request, "windy.html", {"data": data})
        else:
            print(response.json())
            print(f"Błąd podczas pobierania danych: {response.status_code}")
            print(f"Treść odpowiedzi: {response.text}")
            return None
    except requests.RequestException as e:
        print(f"Wystąpił błąd sieci: {e}")
        return render(request, "error.html")


def fetch_weatherapp_data(request):
    api_key = '0d1764dc7eace6612e7d9a5e1168371f'
    city = 'Gdynia'  # będzie wczytywane z formularza!
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        temp = data['main']['temp']
        temp = temp - 273.15
        wind_speed = data['wind']['speed']
        wind_direction = data['wind']['deg']
        desc = data['weather'][0]['description']
        print(f'Temperature: {temp} C')
        print(f'Wind speed: {wind_speed} m/s')
        print(f'Wind direction: {wind_direction}')
        print(f'Description: {desc}')
        return render(request, "openweathermap.html", {"data": data})

    else:
        print('Error fetching weather data')
        return render(request, "error.html")


def fetch_weatherapi_data(request):
    # ustawienie punktu
    api_key = '32ac4dbcfb684f52b9275344240311'
    latitude = 54.31
    longitude = 18.31

    # Initializing the WeatherPoint
    point = WeatherPoint(latitude, longitude)

    # Setting the key for data access
    point.set_key(api_key)

    # get current weather data
    p = point.get_current_weather()
    print(f"{p=}")

    print(point.temp_c)  # temperature in celsius
    print(point.wind_kph)  # wind in kilometers per hour
    print(point.localtime)  # local datetime of the request
    return render(request, "weatherapi.html", {"data": point})


async def getweather(request):
    # declare the client. the measuring unit used defaults to the metric system (celcius, km/h, etc.)
    async with python_weather.Client(unit=python_weather.IMPERIAL) as client:
        # fetch a weather forecast from a city
        weather = await client.get('Gdynia')
        available_attributes = [item for item in dir(weather) if not item.startswith("__")]

        # print(getattr(weather))

        # returns the current day's forecast temperature (int)
        print(weather.temperature)

        # get the weather forecast for a few days
        for daily in weather:
            print(daily)

            # hourly forecasts
            for hourly in daily:
                print(f' --> {hourly!r}')
    return render(request, "python-weather.html", {"data": weather, "attributes": available_attributes})


def fetch_weatherbit_data(request):
    api_key = "e7f4bdfe9101470982721ecc9e87f4f3"
    lat = 38.00
    lon = -125.75

    api = Api(api_key)
    api.set_granularity('daily')

    try:
        # Można użyć dowolnej z poniższych opcji do pobrania prognozy
        forecast = api.get_forecast(lat=lat, lon=lon)
        # forecast = api.get_forecast(city="Raleigh,NC")
        # forecast = api.get_forecast(city="Raleigh", state="North Carolina", country="US")

        # Pobieranie danych prognozy temperatury i opadów
        series = forecast.get_series(['temp', 'precip', 'solar_rad'])

        return render(request, "weatherbit.html", {"forecast_data": series})

    except Exception as e:
        print(f"Error fetching Weatherbit data: {e}")
        return render(request, "error.html")


def fetch_virtualcrossing_data(request):
    BaseURL = 'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/'
    ApiKey = 'PZ7J682SJRRNLFDVJ3F4GRGXL'
    UnitGroup = 'us'
    Location = 'Gdynia'
    StartDate = ''
    EndDate = ''
    ContentType = "json"
    Include = "days"

    # Tworzenie URL z parametrami
    ApiQuery = f"{BaseURL}{Location}"
    if StartDate:
        ApiQuery += f"/{StartDate}"
        if EndDate:
            ApiQuery += f"/{EndDate}"
    ApiQuery += f"?unitGroup={UnitGroup}&contentType={ContentType}&include={Include}&key={ApiKey}"

    try:
        response = urllib.request.urlopen(ApiQuery)
        data = response.read().decode("utf-8")

        # Parsowanie JSON, jeśli potrzebne, np. json.loads(data)
        return render(request, "virtualcrossing.html", {"forecast_data": data})

    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} {e.read().decode()}")
        return render(request, "error.html")
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
        return render(request, "error.html")


async def fetch_open_meteo_data(request):
    """Asynchronous function to fetch weather forecast data using Open-Meteo API."""
    async with OpenMeteo() as open_meteo:
        forecast = await open_meteo.forecast(
            latitude=52.27,
            longitude=6.87417,
            current_weather=True,
            daily=[
                DailyParameters.SUNRISE,
                DailyParameters.SUNSET,
            ],
            hourly=[
                HourlyParameters.TEMPERATURE_2M,
                HourlyParameters.RELATIVE_HUMIDITY_2M,
            ],
        )

    return render(request, "open_meteo.html", {"forecast": forecast})

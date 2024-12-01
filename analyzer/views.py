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

import math


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
            temperatura = []  # Nowa lista na temperatury

            print(f"{data['ts']=}")
            print(data)

            for element, dewpoint, rh in zip(data['ts'], data['dewpoint-surface'], data['rh-surface']):
                # Przetwarzanie timestamp na czas
                time_from_timestamp.append(datetime.fromtimestamp(element / 1000))

                # Obliczanie temperatury z punktu rosy i wilgotności
                dewpoint_celsius = dewpoint - 273.15  # Punkt rosy z kelwinów na stopnie Celsjusza
                a = 17.625
                b = 243.04
                alpha = math.log(rh / 100) + (a * dewpoint_celsius) / (b + dewpoint_celsius)
                temp_celsius = (b * alpha) / (a - alpha)
                temperatura.append(temp_celsius)  # Dodaj temperaturę do listy

            print(f"{time_from_timestamp=}")
            print(f"{temperatura=}")

            return render(request, "windy.html", {
                "time_from_timestamp": time_from_timestamp,
                "wind_u_surface": data["wind_u-surface"],
                "dewpoint_surface": data["dewpoint-surface"],
                "pressure_surface": data["pressure-surface"],
                "rh_surface": data["rh-surface"],
                "temperatura": temperatura,  # Dodajemy temperaturę do danych zwracanych do szablonu
            })
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
    #api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API key}
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
        print(data)
        return render(request, "openweathermap.html", {"data": data})

    else:
        print('Error fetching weather data')
        return render(request, "error.html")


def fetch_weatherapi_data(request):
    # ustawienie punktu
    api_key = '32ac4dbcfb684f52b9275344240311'
    latitude = 54.31
    longitude = 18.31

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
    # Klient do pobierania danych pogodowych
    async with python_weather.Client(unit=python_weather.IMPERIAL) as client:
        # Pobierz prognozę pogody dla Gdyni
        weather = await client.get('Gdynia')

        # Zmienna przechowująca dane
        forecast_data = []

        # Przetwarzanie prognozy dziennej
        for daily in weather:
            daily_data = {
                "date": daily.date,
                "temperature": round((daily.temperature - 32) * 5 / 9, 2),  # Fahrenheit -> Celsius
                "hourly": []
            }

            # Przetwarzanie prognozy godzinowej
            for hourly in daily:
                hourly_data = {
                    "time": hourly.time,
                    "temperature": round((hourly.temperature - 32) * 5 / 9, 2),  # Fahrenheit -> Celsius
                    "wind_speed": getattr(hourly, "wind_speed", "N/A"),  # Jeśli brak danych
                    "pressure": round(getattr(hourly, "pressure", 0) * 33.8639, 2) if hasattr(hourly, "pressure") else "N/A",  # inHg -> hPa
                    "humidity": getattr(hourly, "humidity", "N/A"),  # Wilgotność
                    "precipitation": getattr(hourly, "precipitation", "N/A"),  # Opady
                    "description": hourly.description
                }
                daily_data["hourly"].append(hourly_data)

            forecast_data.append(daily_data)

    return render(request, "python-weather.html", {"forecast_data": forecast_data})


def fetch_weatherbit_data(request):
    api_key = "e7f4bdfe9101470982721ecc9e87f4f3"
    lat = 54.31
    lon = 18.31

    api = Api(api_key)
    api.set_granularity('daily')

    try:
        # Można użyć dowolnej z poniższych opcji do pobrania prognozy
        forecast = api.get_forecast(lat=lat, lon=lon)
        # forecast = api.get_forecast(city="Raleigh,NC")
        # forecast = api.get_forecast(city="Raleigh", state="North Carolina", country="US")

        series = forecast.get_series(['datetime', 'temp', 'precip', 'pres', 'clouds','wind_spd', 'uv'])
        print(series)
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
        forecast_data = json.loads(data)
        return render(request, "virtualcrossing.html", {"forecast_data": forecast_data})

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
                DailyParameters.WIND_DIRECTION_10M_DOMINANT,
                DailyParameters.APPARENT_TEMPERATURE_MAX,
                DailyParameters.WIND_SPEED_10M_MAX
            ],
            hourly=[
                HourlyParameters.TEMPERATURE_2M,
                HourlyParameters.RELATIVE_HUMIDITY_2M,
            ],
        )
    print(forecast.daily.sunrise)
    return render(request, "open_meteo.html", {"sunrise": forecast.daily.sunrise,
                                               "sunset":forecast.daily.sunset,
                                               "temp":forecast.daily.apparent_temperature_max})

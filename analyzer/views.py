from datetime import datetime
import json
import math
import urllib

from django.shortcuts import render
from geopy.geocoders import Nominatim
from open_meteo import OpenMeteo
from open_meteo.models import DailyParameters, HourlyParameters
import python_weather
import requests
from weatherapi import WeatherPoint
from weatherbit.api import Api
from urllib.parse import quote
from collections import defaultdict
from geopy.geocoders import Nominatim
from datetime import datetime
from dateutil.parser import parse

loc = Nominatim(user_agent="Geopy Library")


def index(request):
    return render(request, "index.html")

def fetch_windy_data(request):
    API_KEY = "tvt0g6AqPDQ5tYN2e58BAVvAoRrjAaH3"
    API_URL = "https://api.windy.com/api/point-forecast/v2"

    headers = {
        "Content-Type": "application/json",
    }

    query = request.GET.get("localization_query")
    print(f"{query=}")
    getLoc = loc.geocode(query)


    if getLoc:
        print(f"{getLoc=}")
        print(getLoc.address)

        print("Latitude = ", getLoc.latitude, "\n")
        print("Longitude = ", getLoc.longitude)
    else:
        query = "Gdynia"
        getLoc = loc.geocode(query)

    payload = {
        "lat": getLoc.latitude,
        "lon": getLoc.longitude,
        "model": "gfs",
        "parameters": ["wind", "dewpoint", "rh", "pressure"],
        "levels": ["surface", "800h", "300h"],
        "key": API_KEY,
    }

    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            data = response.json()
            time_from_timestamp = []
            temperatura = []

            for element, dewpoint, rh in zip(
                data["ts"], data["dewpoint-surface"], data["rh-surface"]
            ):

                time_from_timestamp.append(datetime.fromtimestamp(element / 1000))

                dewpoint_celsius = (
                    dewpoint - 273.15
                )
                a = 17.625
                b = 243.04
                alpha = math.log(rh / 100) + (a * dewpoint_celsius) / (
                    b + dewpoint_celsius
                )
                temp_celsius = (b * alpha) / (a - alpha)
                temperatura.append(temp_celsius)

            return render(
                request,
                "windy.html",
                {
                    "time_from_timestamp": time_from_timestamp,
                    "wind_u_surface": data["wind_u-surface"],
                    "dewpoint_surface": data["dewpoint-surface"],
                    "pressure_surface": data["pressure-surface"],
                    "rh_surface": data["rh-surface"],
                    "temperatura": temperatura,
                    "query": query,
                    "adres": getLoc.address
                },
            )
        else:
            # print(response.json())
            print(f"Błąd podczas pobierania danych: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Wystąpił błąd sieci: {e}")
        return render(request, "error.html")


def fetch_weatherapp_data(request):
    api_key = "0d1764dc7eace6612e7d9a5e1168371f"
    default_city = "Gdynia"  # Domyślna lokalizacja
    geolocator = Nominatim(user_agent="weather_app")

    city = request.GET.get("localization_query", default_city)

    getLoc = geolocator.geocode(city)
    if not getLoc:
        city = default_city
        getLoc = geolocator.geocode(city)

    latitude = getLoc.latitude
    longitude = getLoc.longitude

    url = f"http://api.openweathermap.org/data/2.5/forecast?lat={latitude}&lon={longitude}&appid={api_key}"

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        forecast_data = []
        for entry in data["list"]:
            forecast_data.append(
                {
                    "time": entry["dt_txt"],
                    "temperature": round(
                        entry["main"]["temp"] - 273.15, 2
                    ),  # Temperatura w °C
                    "wind_speed": entry["wind"]["speed"],
                    "wind_direction": entry["wind"][
                        "deg"
                    ],
                    "humidity": entry["main"]["humidity"],
                    "pressure": entry["main"]["pressure"],
                    "description": entry["weather"][0]["description"],
                    "precipitation": entry.get("rain", {}).get("3h", 0),
                }
            )

        return render(
            request,
            "openweathermap.html",
            {"forecast_data": forecast_data, "city": city},
        )

    else:
        return render(
            request,
            "openweathermap.html",
            {"forecast_data": None, "city": city, "error": "Błąd pobierania danych z API"}
        )


def fetch_weatherapi_data(request):
    api_key = "32ac4dbcfb684f52b9275344240311"

    query = request.GET.get("localization_query", "Gdynia")

    days = 3
    url = f"https://api.weatherapi.com/v1/forecast.json?key={api_key}&q={query}&days={days}"

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        hourly_forecast_data = []

        probe_number = 1
        for day in data["forecast"]["forecastday"]:
            for hour in day["hour"]:
                hourly_forecast_data.append(
                    {
                        "probe": probe_number,
                        "time": hour["time"],
                        "temperature": hour["temp_c"],
                        "precipitation": hour["precip_mm"],
                        "humidity": hour["humidity"],
                        "condition": hour["condition"]["text"],
                        "wind_speed": hour["wind_kph"],
                        "wind_direction": hour["wind_dir"],
                        "pressure": hour["pressure_mb"],
                        "uv": hour.get("uv", "Brak danych"),
                    }
                )
                probe_number += 1

        return render(
            request,
            "weatherapi.html",
            {
                "forecast_data": hourly_forecast_data,
                "city": data.get("location", {}).get("name", "Nieznane"),
                "query": query,
            },
        )

    else:
        return render(
            request,
            "error.html",
            {
                "message": "Nie udało się pobrać prognozy pogody. Sprawdź poprawność lokalizacji.",
                "query": query,
            },
        )


async def getweather(request):
    query = request.GET.get("localization_query", "Gdynia")

    async with python_weather.Client(unit=python_weather.IMPERIAL) as client:
        try:
            weather = await client.get(query)

            forecast_data = []

            for daily in weather:
                daily_data = {
                    "date": daily.date,
                    "temperature": round(
                        (daily.temperature - 32) * 5 / 9, 2
                    ),  # Fahrenheit -> Celsius
                    "hourly": [],
                }

                for hourly in daily:
                    hourly_data = {
                        "time": hourly.time,
                        "temperature": round(
                            (hourly.temperature - 32) * 5 / 9, 2
                        ),  # Fahrenheit -> Celsius
                        "wind_speed": getattr(
                            hourly, "wind_speed", "N/A"
                        ),
                        "pressure": (
                            round(getattr(hourly, "pressure", 0) * 33.8639, 2)
                            if hasattr(hourly, "pressure")
                            else "N/A"
                        ),  # inHg -> hPa
                        "humidity": getattr(hourly, "humidity", "N/A"),  # Wilgotność
                        "precipitation": getattr(hourly, "precipitation", "N/A"),  # Opady
                        "description": hourly.description,
                    }
                    daily_data["hourly"].append(hourly_data)

                forecast_data.append(daily_data)

            return render(
                request,
                "python-weather.html",
                {
                    "forecast_data": forecast_data,
                    "query": query,
                },
            )

        except Exception as e:
            return render(
                request,
                "error.html",
                {
                    "message": f"Nie udało się pobrać prognozy pogody dla lokalizacji: {query}. Spróbuj ponownie.",
                    "query": query,
                },
            )


async def fetch_open_meteo_data(request):
    geolocator = Nominatim(user_agent="weather_app")

    query = request.GET.get("localization_query", "Gdynia")
    print(f"Zapytanie użytkownika: {query}")

    try:
        getLoc = geolocator.geocode(query)

        if getLoc:
            print(f"Znaleziono lokalizację: {getLoc.address}")
            latitude = getLoc.latitude
            longitude = getLoc.longitude
        else:
            print("Nie znaleziono lokalizacji, ustawiono domyślnie Gdynię.")
            query = "Gdynia"
            getLoc = geolocator.geocode(query)
            latitude = getLoc.latitude
            longitude = getLoc.longitude

    except Exception as e:
        print(f"Wystąpił błąd geokodowania: {e}")
        return render(
            request,
            "error.html",
            {"message": f"Nie udało się pobrać współrzędnych dla lokalizacji: {query}. Spróbuj ponownie."},
        )

    try:
        async with OpenMeteo() as open_meteo:
            forecast = await open_meteo.forecast(
                latitude=latitude,
                longitude=longitude,
                current_weather=True,
                daily=[
                    DailyParameters.SUNRISE,
                    DailyParameters.SUNSET,
                ],
                hourly=[
                    HourlyParameters.TEMPERATURE_2M,
                    HourlyParameters.RELATIVE_HUMIDITY_2M,
                    HourlyParameters.PRECIPITATION,
                    HourlyParameters.PRESSURE_MSL,
                    HourlyParameters.CLOUD_COVER,
                    HourlyParameters.WIND_SPEED_10M,
                    HourlyParameters.WIND_DIRECTION_10M,
                ],
            )

        hourly_data = [
            {
                "time": forecast.hourly.time[i],
                "temperature": forecast.hourly.temperature_2m[i],
                "wind_speed": forecast.hourly.wind_speed_10m[i],
                "precipitation": forecast.hourly.precipitation[i],
                "pressure": forecast.hourly.pressure_msl[i],
                "humidity": forecast.hourly.relative_humidity_2m[i],
                "cloud_cover": forecast.hourly.cloud_cover[i],
                "wind_direction": forecast.hourly.wind_direction_10m[i],
            }
            for i in range(0, len(forecast.hourly.time), 3)
        ]

        return render(
            request,
            "open_meteo.html",
            {"hourly_data": hourly_data, "query": query, "adres": getLoc.address},
        )

    except Exception as e:
        print(f"Wystąpił błąd podczas pobierania danych pogodowych: {e}")
        return render(
            request,
            "error.html",
            {"message": f"Nie udało się pobrać prognozy pogody dla lokalizacji: {query}. Spróbuj ponownie."},
        )


def fetch_weatherbit_data(request):
    api_key = "e7f4bdfe9101470982721ecc9e87f4f3"
    geolocator = Nominatim(user_agent="weatherbit_app")

    query = request.GET.get("localization_query", "Gdynia")  # Domyślnie Gdynia
    getLoc = geolocator.geocode(query)

    if getLoc:
        lat = getLoc.latitude
        lon = getLoc.longitude
        address = getLoc.address
    else:
        query = "Gdynia"
        getLoc = geolocator.geocode(query)
        lat = getLoc.latitude
        lon = getLoc.longitude
        address = getLoc.address

    api = Api(api_key)
    api.set_granularity("daily")

    try:
        forecast = api.get_forecast(lat=lat, lon=lon)

        series = forecast.get_series(
            ["datetime", "temp", "precip", "pres", "clouds", "wind_spd", "uv"]
        )

        return render(
            request,
            "weatherbit.html",
            {
                "forecast_data": series,
                "query": query,
                "address": address,
            },
        )
    except Exception as e:
        print(f"Error fetching Weatherbit data: {e}")
        return render(request, "error.html")


def fetch_virtualcrossing_data(request):
    BaseURL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"
    ApiKey = "PZ7J682SJRRNLFDVJ3F4GRGXL"
    UnitGroup = "metric"

    Location = request.GET.get("localization_query", "Gdynia")

    Location = quote(Location)  # Teraz spacje zamienią się na %20

    StartDate = ""
    EndDate = ""
    ContentType = "json"
    Include = "hours"

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

        hourly_forecast_data = []
        for day in forecast_data.get("days", []):
            for hour in day.get("hours", []):
                hourly_forecast_data.append(
                    {   "date": day["datetime"],
                        "time": hour["datetime"],
                        "temperature": hour["temp"],
                        "precipitation": hour.get("precip", 0),
                        "humidity": hour.get("humidity", 0),
                        "condition": hour.get("conditions", "Brak danych"),
                        "wind_speed": hour.get("windspeed", 0),
                        "wind_direction": hour.get("winddir", "Brak danych"),
                        "pressure": hour.get("pressure", 0),
                        "uv": hour.get("uvindex", "Brak danych"),
                    }
                )

        return render(
            request,
            "virtualcrossing.html",
            {
                "forecast_data": hourly_forecast_data,
                "city": forecast_data.get("resolvedAddress", "Nieznane"),
                "query": request.GET.get("localization_query", "Gdynia"),
            },
        )

    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} {e.read().decode()}")
        return render(request, "error.html", {"message": "Błąd po stronie API."})
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
        return render(request, "error.html", {"message": "Nie można połączyć się z API."})


async def compare_temperatures(request):
    city = request.GET.get("localization_query", "Gdynia")
    geolocator = Nominatim(user_agent="weather_comparison_app")
    location = geolocator.geocode(city)

    if not location:
        return render(request, "error.html", {"message": "Nie znaleziono lokalizacji."})

    latitude, longitude = location.latitude, location.longitude

    windy_api_key = "tvt0g6AqPDQ5tYN2e58BAVvAoRrjAaH3"
    windy_url = "https://api.windy.com/api/point-forecast/v2"
    windy_payload = {
        "lat": latitude,
        "lon": longitude,
        "model": "gfs",
        "parameters": ["dewpoint", "rh"],
        "levels": ["surface"],
        "key": windy_api_key,
    }
    windy_headers = {"Content-Type": "application/json"}
    windy_temperatures = []
    windy_times = []

    try:
        windy_response = requests.post(windy_url, headers=windy_headers, json=windy_payload)
        if windy_response.status_code == 200:
            windy_data = windy_response.json()
            for timestamp, dewpoint, rh in zip(
                    windy_data["ts"], windy_data["dewpoint-surface"], windy_data["rh-surface"]
            ):
                time = datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
                dewpoint_celsius = dewpoint - 273.15
                a, b = 17.625, 243.04
                alpha = math.log(rh / 100) + (a * dewpoint_celsius) / (b + dewpoint_celsius)
                temperature = (b * alpha) / (a - alpha)
                windy_times.append(time)
                windy_temperatures.append(round(temperature, 2))
        else:
            print(f"Błąd Windy API: {windy_response.status_code}")
    except Exception as e:
        print(f"Błąd połączenia z Windy API: {e}")

    weather_api_key = "32ac4dbcfb684f52b9275344240311"
    weather_url = f"https://api.weatherapi.com/v1/forecast.json?key={weather_api_key}&q={city}&days=3"
    weather_temperatures = []
    weather_times = []

    try:
        weather_response = requests.get(weather_url)
        if weather_response.status_code == 200:
            weather_data = weather_response.json()
            for day in weather_data["forecast"]["forecastday"]:
                for hour in day["hour"]:
                    weather_times.append(hour["time"])
                    weather_temperatures.append(hour["temp_c"])
        else:
            print(f"Błąd WeatherAPI: {weather_response.status_code}")
    except Exception as e:
        print(f"Błąd połączenia z WeatherAPI: {e}")

    python_weather_temperatures = []
    python_weather_times = []

    try:
        async with python_weather.Client(unit=python_weather.IMPERIAL) as client:
            weather = await client.get(city)
            for daily in weather:
                for hourly in daily:
                    time = f"{daily.date} {hourly.time}"
                    temp_celsius = round((hourly.temperature - 32) * 5 / 9, 2)  # Fahrenheit -> Celsius
                    python_weather_times.append(time)
                    python_weather_temperatures.append(temp_celsius)
    except Exception as e:
        print(f"Błąd Python-Weather: {e}")

    open_meteo_temperatures = []
    open_meteo_times = []

    try:
        async with OpenMeteo() as open_meteo:
            forecast = await open_meteo.forecast(
                latitude=latitude,
                longitude=longitude,
                hourly=["temperature_2m"]
            )
            open_meteo_times = forecast.hourly.time
            open_meteo_temperatures = forecast.hourly.temperature_2m
    except Exception as e:
        print(f"Błąd OpenMeteo: {e}")

    comparison_data = []
    for w_time, w_temp in zip(windy_times, windy_temperatures):
        weather_temp = next((t for t, t_time in zip(weather_temperatures, weather_times) if parse(t_time) == parse(w_time)), None)
        python_temp = next((t for t, t_time in zip(python_weather_temperatures, python_weather_times) if parse(t_time) == parse(w_time)), None)
        open_meteo_temp = next(
            (
                t
                for t, t_time in zip(open_meteo_temperatures, open_meteo_times)
                if (t_time if isinstance(t_time, datetime) else parse(t_time)) ==
                   (w_time if isinstance(w_time, datetime) else parse(w_time))
            ),
            None,
        )

        comparison_data.append({
            "time": w_time,
            "windy_temp": w_temp,
            "weather_temp": weather_temp,
            "python_temp": python_temp,
            "open_meteo_temp": open_meteo_temp,
        })

    return render(request, "compare_temperatures.html", {
        "city": city,
        "comparison_data": comparison_data,
    })

def about(request):
    return render(request, "about.html")
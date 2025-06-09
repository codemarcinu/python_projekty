# plugins/weather_tool.py

import requests
import json
from core.plugin_system import tool
from core.config_manager import get_settings

@tool
def get_current_weather(city: str) -> str:
    """
    Sprawdza i zwraca aktualną pogodę dla podanego miasta.
    Użyj tego narzędzia, gdy użytkownik pyta o pogodę, temperaturę, warunki atmosferyczne itp. w konkretnej lokalizacji.
    
    :param city: Nazwa miasta, dla którego ma być sprawdzona pogoda.
    :return: Sformatowany ciąg znaków z danymi pogodowymi lub komunikat o błędzie.
    """
    settings = get_settings()
    api_key = settings.WEATHER_API_KEY
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    
    complete_url = f"{base_url}q={city}&appid={api_key}&units=metric&lang=pl"
    
    print(f"DEBUG: Wywołuję narzędzie 'get_current_weather' dla miasta: {city}")

    try:
        response = requests.get(complete_url)
        response.raise_for_status()  # Rzuci wyjątkiem dla złych odpowiedzi (4xx lub 5xx)
        
        weather_data = response.json()
        
        if weather_data["cod"] != 200:
            return f"Błąd: Nie można znaleźć pogody dla miasta {city}. Powód: {weather_data.get('message', 'Nieznany błąd')}"
            
        main_data = weather_data["main"]
        description = weather_data["weather"][0]["description"]
        temp = main_data["temp"]
        pressure = main_data["pressure"]
        humidity = main_data["humidity"]
        
        report = (
            f"Pogoda w mieście {city.capitalize()}:\n"
            f"- Warunki: {description.capitalize()}\n"
            f"- Temperatura: {temp}°C\n"
            f"- Ciśnienie: {pressure} hPa\n"
            f"- Wilgotność: {humidity}%"
        )
        return report

    except requests.exceptions.HTTPError as http_err:
        return f"Błąd HTTP podczas zapytania o pogodę: {http_err}"
    except Exception as err:
        return f"Wystąpił nieoczekiwany błąd: {err}" 
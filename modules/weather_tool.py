# modules/weather_tool.py

import requests
import json
from core.module_system import tool
from core.config_manager import settings

@tool
def get_current_weather(city: str) -> str:
    """
    Sprawdza i zwraca aktualną pogodę dla podanego miasta.
    Użyj tego narzędzia, gdy użytkownik pyta o pogodę, temperaturę, warunki atmosferyczne itp. w konkretnej lokalizacji.
    
    :param city: Nazwa miasta, dla którego ma być sprawdzona pogoda.
    :return: Sformatowany ciąg znaków z danymi pogodowymi lub komunikat o błędzie.
    """
    api_key = settings.WEATHER_API_KEY
    if not api_key:
        return "Błąd: Brak klucza API do serwisu pogodowego. Skontaktuj się z administratorem."
        
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    
    # Upewnij się, że nazwa miasta jest poprawnie sformatowana
    city = city.strip().capitalize()
    complete_url = f"{base_url}q={city}&appid={api_key}&units=metric&lang=pl"
    
    print(f"DEBUG: Wywołuję narzędzie 'get_current_weather' dla miasta: {city}")
    print(f"DEBUG: URL zapytania: {complete_url}")

    try:
        response = requests.get(complete_url)
        response.raise_for_status()
        
        weather_data = response.json()
        
        if weather_data["cod"] != 200:
            error_msg = weather_data.get('message', 'Nieznany błąd')
            print(f"DEBUG: Błąd API pogodowego: {error_msg}")
            return f"Błąd: Nie można znaleźć pogody dla miasta {city}. Powód: {error_msg}"
            
        main_data = weather_data["main"]
        description = weather_data["weather"][0]["description"]
        temp = main_data["temp"]
        pressure = main_data["pressure"]
        humidity = main_data["humidity"]
        
        report = (
            f"Pogoda w mieście {city}:\n"
            f"- Warunki: {description.capitalize()}\n"
            f"- Temperatura: {temp}°C\n"
            f"- Ciśnienie: {pressure} hPa\n"
            f"- Wilgotność: {humidity}%"
        )
        return report

    except requests.exceptions.HTTPError as http_err:
        print(f"DEBUG: Błąd HTTP: {http_err}")
        if "404" in str(http_err):
            return f"Nie mogę znaleźć pogody dla miasta '{city}'. Sprawdź, czy nazwa miasta jest poprawna."
        return f"Błąd HTTP podczas zapytania o pogodę: {http_err}"
    except requests.exceptions.RequestException as req_err:
        print(f"DEBUG: Błąd połączenia: {req_err}")
        return f"Nie mogę połączyć się z serwisem pogodowym. Sprawdź swoje połączenie internetowe."
    except Exception as err:
        print(f"DEBUG: Nieoczekiwany błąd: {err}")
        return f"Wystąpił nieoczekiwany błąd: {err}" 
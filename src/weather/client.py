"""Weather integration and Agronomic Spray Advisor for Pakistani agricultural regions."""
import os
import requests
from typing import Dict, Any, Optional

# Pre-populated geographical coordinates for key agricultural districts in Pakistan
PAKISTAN_AGRICULTURAL_DISTRICTS = {
    "faisalabad": {"name": "Faisalabad, Punjab", "lat": 31.4504, "lon": 73.1350},
    "multan": {"name": "Multan, Punjab", "lat": 30.1575, "lon": 71.5249},
    "sargodha": {"name": "Sargodha, Punjab", "lat": 32.0836, "lon": 72.6711},
    "sahiwal": {"name": "Sahiwal, Punjab", "lat": 30.6682, "lon": 73.1114},
    "rahim_yar_khan": {"name": "Rahim Yar Khan, Punjab", "lat": 28.4212, "lon": 70.2989},
    "bahawalpur": {"name": "Bahawalpur, Punjab", "lat": 29.3544, "lon": 71.6911},
    "rawalpindi": {"name": "Rawalpindi / Islamabad", "lat": 33.5651, "lon": 73.0169},
    "hyderabad": {"name": "Hyderabad, Sindh", "lat": 25.3960, "lon": 68.3578},
    "shaheed_benazirabad": {"name": "Nawabshah / Shaheed Benazirabad, Sindh", "lat": 26.2483, "lon": 68.4096},
    "mirpur_khas": {"name": "Mirpur Khas, Sindh", "lat": 25.5276, "lon": 69.0125},
    "peshawar": {"name": "Peshawar, KP", "lat": 34.0151, "lon": 71.5249},
    "swat": {"name": "Swat / Mingora, KP", "lat": 34.7717, "lon": 72.3602},
    "quetta": {"name": "Quetta, Balochistan", "lat": 30.1798, "lon": 66.9750}
}

class WeatherAdvisor:
    """
    Fetches real-time weather and provides scientifically grounded spray recommendations.
    Uses Open-Meteo by default (free, open-access, no API key required).
    Optionally supports OpenWeatherMap if OPENWEATHER_API_KEY is provided.
    """
    def __init__(self, provider="open-meteo"):
        self.provider = os.getenv("WEATHER_PROVIDER", provider).lower()
        self.openweather_key = os.getenv("OPENWEATHER_API_KEY", "").strip()
        self.open_meteo_url = "https://api.open-meteo.com/v1/forecast"
        self.openweather_url = "https://api.openweathermap.org/data/2.5/weather"

    def get_weather(self, district_or_lat=None, lon=None) -> Dict[str, Any]:
        """
        Fetch real-time weather metrics for coordinates or district name.
        """
        lat, lng, location_name = 31.4504, 73.1350, "Faisalabad, Punjab (Default)"
        
        if isinstance(district_or_lat, str):
            key = district_or_lat.lower().replace(" ", "_")
            if key in PAKISTAN_AGRICULTURAL_DISTRICTS:
                d = PAKISTAN_AGRICULTURAL_DISTRICTS[key]
                lat, lng, location_name = d["lat"], d["lon"], d["name"]
        elif isinstance(district_or_lat, (int, float)) and isinstance(lon, (int, float)):
            lat, lng, location_name = float(district_or_lat), float(lon), f"Lat: {district_or_lat:.2f}, Lon: {lon:.2f}"
            
        # If OpenWeather API key is provided and requested, use OpenWeatherMap
        if self.openweather_key and self.provider == "openweather":
            return self._fetch_openweather(lat, lng, location_name)
            
        # Default: Open-Meteo (No API key needed)
        return self._fetch_open_meteo(lat, lng, location_name)

    def _fetch_open_meteo(self, lat: float, lng: float, location_name: str) -> Dict[str, Any]:
        params = {
            "latitude": lat,
            "longitude": lng,
            "current": "temperature_2m,relative_humidity_2m,precipitation,rain,weather_code,wind_speed_10m",
            "hourly": "precipitation_probability",
            "forecast_days": 1,
            "timezone": "auto"
        }
        try:
            res = requests.get(self.open_meteo_url, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json()
                current = data.get("current", {})
                hourly = data.get("hourly", {})
                
                temp = current.get("temperature_2m", 25.0)
                humidity = current.get("relative_humidity_2m", 50.0)
                wind_speed = current.get("wind_speed_10m", 5.0)
                precip = current.get("precipitation", 0.0)
                
                precip_prob_list = hourly.get("precipitation_probability", [0])
                rain_prob = max(precip_prob_list[:6]) if precip_prob_list else 0
                
                spray_eval = self._evaluate_spray_conditions(temp, humidity, wind_speed, rain_prob)
                
                return {
                    "status": "success",
                    "provider": "Open-Meteo (Free / Keyless)",
                    "location": location_name,
                    "latitude": lat,
                    "longitude": lng,
                    "temperature_c": temp,
                    "relative_humidity": humidity,
                    "wind_speed_kmh": wind_speed,
                    "rain_probability": rain_prob,
                    "current_precipitation_mm": precip,
                    "spray_suitability": spray_eval["suitability"],
                    "spray_advice_en": spray_eval["advice_en"],
                    "spray_advice_ur": spray_eval["advice_ur"],
                    "spray_advice_roman_ur": spray_eval["advice_roman_ur"]
                }
            else:
                return self._fallback_weather(location_name, f"Open-Meteo Error: {res.status_code}")
        except Exception as e:
            return self._fallback_weather(location_name, str(e))

    def _fetch_openweather(self, lat: float, lng: float, location_name: str) -> Dict[str, Any]:
        params = {
            "lat": lat,
            "lon": lng,
            "appid": self.openweather_key,
            "units": "metric"
        }
        try:
            res = requests.get(self.openweather_url, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json()
                main = data.get("main", {})
                wind = data.get("wind", {})
                
                temp = main.get("temp", 25.0)
                humidity = main.get("humidity", 50.0)
                wind_speed = wind.get("speed", 3.0) * 3.6  # Convert m/s to km/h
                rain_prob = 0  # Basic OpenWeather endpoint doesn't supply hourly probability
                
                spray_eval = self._evaluate_spray_conditions(temp, humidity, wind_speed, rain_prob)
                return {
                    "status": "success",
                    "provider": "OpenWeatherMap",
                    "location": location_name,
                    "latitude": lat,
                    "longitude": lng,
                    "temperature_c": temp,
                    "relative_humidity": humidity,
                    "wind_speed_kmh": round(wind_speed, 1),
                    "rain_probability": rain_prob,
                    "current_precipitation_mm": 0.0,
                    "spray_suitability": spray_eval["suitability"],
                    "spray_advice_en": spray_eval["advice_en"],
                    "spray_advice_ur": spray_eval["advice_ur"],
                    "spray_advice_roman_ur": spray_eval["advice_roman_ur"]
                }
            else:
                return self._fetch_open_meteo(lat, lng, location_name)  # Fallback to keyless Open-Meteo
        except Exception:
            return self._fetch_open_meteo(lat, lng, location_name)

    def _evaluate_spray_conditions(self, temp, humidity, wind_speed, rain_prob) -> Dict[str, str]:
        """Agronomic rule-based evaluation of spray safety."""
        warnings_en = []
        warnings_ur = []
        warnings_roman = []
        
        if rain_prob > 40:
            warnings_en.append(f"Rain probability is high ({rain_prob}%). Avoid spraying to prevent chemical washoff.")
            warnings_ur.append(f"بارش کا امکان زیادہ ہے ({rain_prob}%)۔ دوائی دھلنے سے بچانے کے لیے سپرے نہ کریں۔")
            warnings_roman.append(f"Baarish ka imkan ziada hai ({rain_prob}%). Spray na karein taakay chemical dhul na jaye.")
            
        if wind_speed > 15.0:
            warnings_en.append(f"High wind speed ({wind_speed} km/h). Spray drift may cause uneven application or harm adjacent crops.")
            warnings_ur.append(f"تیز ہوا ({wind_speed} کلومیٹر/گھنٹہ) کی وجہ سے سپرے اڑ سکتا ہے۔")
            warnings_roman.append(f"Tez hawa ({wind_speed} km/h) ki wajah se spray ud sakta hai.")
            
        if temp > 38.0:
            warnings_en.append(f"High daytime temperature ({temp}°C). Spraying under harsh sun can cause foliage scorch. Spray early morning or late afternoon.")
            warnings_ur.append(f"شدید گرمی ({temp}°C)۔ صبح کے وقت یا شام کے ٹھنڈے وقت میں سپرے کریں۔")
            warnings_roman.append(f"Shadeed garmi ({temp}°C). Subah ya shaam ke thanday waqt spray karein.")
            
        if not warnings_en:
            return {
                "suitability": "Optimal",
                "advice_en": f"Weather is favorable for spraying (Temp: {temp}°C, Humidity: {humidity}%, Wind: {wind_speed} km/h).",
                "advice_ur": f"سپرے کے لیے موسمی حالات موزوں ہیں (درجہ حرارت: {temp}°C، نمی: {humidity}٪، ہوا: {wind_speed} کلومیٹر/گھنٹہ)۔",
                "advice_roman_ur": f"Spray ke liye mausam theek hai (Darja hararat: {temp}°C, Nami: {humidity}%, Hawa: {wind_speed} km/h)."
            }
        else:
            return {
                "suitability": "Caution / Suboptimal",
                "advice_en": " ".join(warnings_en),
                "advice_ur": " ".join(warnings_ur),
                "advice_roman_ur": " ".join(warnings_roman)
            }

    def _fallback_weather(self, location, error_msg) -> Dict[str, Any]:
        return {
            "status": "unavailable",
            "provider": "Offline",
            "location": location,
            "temperature_c": None,
            "relative_humidity": None,
            "wind_speed_kmh": None,
            "rain_probability": None,
            "spray_suitability": "Unknown",
            "spray_advice_en": "Weather service currently unavailable. Follow general label guidelines.",
            "spray_advice_ur": "موسمی ڈیٹا دستیاب نہیں ہے۔ معیاری حفاظتی ہدایات پر عمل کریں۔",
            "spray_advice_roman_ur": "Mausam ka data dastiyab nahi hai. Standard hidayaat par amal karein."
        }

# speedtest/utils/geo_utils.py
import requests
from typing import Dict, Optional


class IPGeolocation:
    """IP manzil orqali joylashuv va ISP ma'lumotlarini olish"""

    # Bepul API xizmatlari
    APIS = {
        'ipapi': 'https://ipapi.co/{ip}/json/',
        'ip-api': 'http://ip-api.com/json/{ip}',
        'ipwhois': 'https://ipwhois.app/json/{ip}',
    }

    @staticmethod
    def get_info_from_ipapi(ip: str) -> Optional[Dict]:
        """ipapi.co dan ma'lumot olish (eng aniq)"""
        try:
            response = requests.get(
                f'https://ipapi.co/{ip}/json/',
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    'ip': ip,
                    'city': data.get('city', 'Noma\'lum'),
                    'region': data.get('region', 'Noma\'lum'),
                    'country': data.get('country_name', 'Noma\'lum'),
                    'country_code': data.get('country_code', 'UZ'),
                    'isp': data.get('org', 'Noma\'lum ISP'),
                    'latitude': data.get('latitude'),
                    'longitude': data.get('longitude'),
                    'timezone': data.get('timezone', 'Asia/Tashkent'),
                    'postal': data.get('postal', ''),
                    'connection_type': 'Unknown'
                }
        except Exception as e:
            print(f"ipapi.co error: {e}")
            return None

    @staticmethod
    def get_info_from_ip_api(ip: str) -> Optional[Dict]:
        """ip-api.com dan ma'lumot olish (backup)"""
        try:
            response = requests.get(
                f'http://ip-api.com/json/{ip}',
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return {
                        'ip': ip,
                        'city': data.get('city', 'Noma\'lum'),
                        'region': data.get('regionName', 'Noma\'lum'),
                        'country': data.get('country', 'Noma\'lum'),
                        'country_code': data.get('countryCode', 'UZ'),
                        'isp': data.get('isp', 'Noma\'lum ISP'),
                        'latitude': data.get('lat'),
                        'longitude': data.get('lon'),
                        'timezone': data.get('timezone', 'Asia/Tashkent'),
                        'postal': data.get('zip', ''),
                        'connection_type': 'Unknown'
                    }
        except Exception as e:
            print(f"ip-api.com error: {e}")
            return None

    @staticmethod
    def get_info_from_ipwhois(ip: str) -> Optional[Dict]:
        """ipwhois.app dan ma'lumot olish (yana bir backup)"""
        try:
            response = requests.get(
                f'https://ipwhois.app/json/{ip}',
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return {
                        'ip': ip,
                        'city': data.get('city', 'Noma\'lum'),
                        'region': data.get('region', 'Noma\'lum'),
                        'country': data.get('country', 'Noma\'lum'),
                        'country_code': data.get('country_code', 'UZ'),
                        'isp': data.get('isp', 'Noma\'lum ISP'),
                        'latitude': data.get('latitude'),
                        'longitude': data.get('longitude'),
                        'timezone': data.get('timezone', 'Asia/Tashkent'),
                        'postal': '',
                        'connection_type': data.get('connection_type', 'Unknown')
                    }
        except Exception as e:
            print(f"ipwhois.app error: {e}")
            return None

    @classmethod
    def get_location_data(cls, ip: str) -> Dict:
        """
        Barcha API lardan ma'lumot olishga harakat qilish
        Birinchi muvaffaqiyatli natijani qaytarish
        """
        # Agar local IP bo'lsa, default qiymatlar
        if ip in ['127.0.0.1', 'localhost', '::1']:
            return cls.get_default_data(ip)

        # Har bir API ni sinab ko'rish
        for api_name, api_method in [
            ('ipapi', cls.get_info_from_ipapi),
            ('ip-api', cls.get_info_from_ip_api),
            ('ipwhois', cls.get_info_from_ipwhois)
        ]:
            result = api_method(ip)
            if result:
                print(f"✅ Ma'lumot {api_name} dan olindi")
                return result

        # Agar hech narsa ishlamasa, default
        print("⚠️ Hech bir API ishlamadi, default qiymatlar")
        return cls.get_default_data(ip)

    @staticmethod
    def get_default_data(ip: str) -> Dict:
        """Default qiymatlar (API ishlamasa)"""
        return {
            'ip': ip,
            'city': 'Toshkent',
            'region': 'Toshkent viloyati',
            'country': 'O\'zbekiston',
            'country_code': 'UZ',
            'isp': 'UZTELECOM',
            'latitude': 41.2995,
            'longitude': 69.2401,
            'timezone': 'Asia/Tashkent',
            'postal': '100000',
            'connection_type': 'Unknown'
        }

    @staticmethod
    def parse_isp_name(isp_full: str) -> str:
        """
        ISP nomini tozalash
        Masalan: "AS12345 UZTELECOM LLC" -> "UZTELECOM"
        """
        # AS raqamini olib tashlash
        if isp_full.startswith('AS'):
            parts = isp_full.split(' ', 1)
            if len(parts) > 1:
                isp_full = parts[1]

        # LLC, JSC va shunga o'xshashlarni olib tashlash
        for suffix in [' LLC', ' JSC', ' LTD', ' Inc', ' Corp']:
            if isp_full.upper().endswith(suffix.upper()):
                isp_full = isp_full[:-len(suffix)]

        return isp_full.strip()


# O'zbekiston provayderlarini tanish uchun helper
class UzbekistanISPDetector:
    """O'zbekiston provayderlarini aniqlash"""

    KNOWN_ISPS = {
        'UZTELECOM': ['uztelecom', 'uztelekom', 'ucell'],
        'Perfectum Mobile': ['perfectum', 'beeline'],
        'UZDIGITAL': ['uzdigital', 'mobiuz'],
        'Turon Telecom': ['turon', 'turontelecom'],
        'Sarkor Telecom': ['sarkor'],
        'Sharq Telecom': ['sharq'],
        'Eastnet': ['eastnet'],
        'Unitel': ['unitel'],
        'Stream Telecom': ['stream'],
        'Universal Mobile': ['universal', 'umobile'],
    }

    @classmethod
    def identify_provider(cls, isp_string: str) -> str:
        """ISP stringidan aniq provayderni aniqlash"""
        isp_lower = isp_string.lower()

        for provider_name, keywords in cls.KNOWN_ISPS.items():
            for keyword in keywords:
                if keyword in isp_lower:
                    return provider_name

        # Agar topa olmasa, asl nomni qaytarish
        return IPGeolocation.parse_isp_name(isp_string)


# Test uchun
if __name__ == "__main__":
    test_ips = [
        '8.8.8.8',  # Google DNS
        '82.215.99.63',  # UZTELECOM
        '195.69.189.1',  # Turon Telecom
    ]

    print("🔍 IP Geolocation Test\n")

    for ip in test_ips:
        print(f"Testing IP: {ip}")
        data = IPGeolocation.get_location_data(ip)
        print(f"  📍 Location: {data['city']}, {data['country']}")
        print(f"  🌐 ISP: {data['isp']}")
        print(f"  📊 Coordinates: {data['latitude']}, {data['longitude']}")
        print()
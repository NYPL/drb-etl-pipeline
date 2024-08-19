import requests


def map_ip_address_to_country(ip_address: str) -> str | None:
    ip_info_url = f'https://ipinfo.io/{ip_address}/json'

    ip_info_response = requests.get(ip_info_url)
    ip_info_data = ip_info_response.json()

    return ip_info_data.get('country', None)

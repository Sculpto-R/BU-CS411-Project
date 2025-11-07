import requests

def get_coordinates(address, api_key):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"
    response = requests.get(url)
    data = response.json()
    
    if data['status'] == 'OK':
        location = data['results'][0]['geometry']['location']
        return location['lat'], location['lng']
    else:
        print("Geocoding error:", data['status'])
        return None, None

# Replace this with your actual API key
api_key = "AIzaSyC2tWZApy0oF5lBrlK0rmjfX0DFa3dk8do"

lat, lng = get_coordinates("Camden Market, London, UK", api_key)
print("Latitude:", lat, "Longitude:", lng)

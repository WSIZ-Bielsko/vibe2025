import pgeocode

nomi = pgeocode.Nominatim('PL')
# location = nomi.query_postal_code('31-123')
location = nomi.query_postal_code('43-365')

print(f"Lat: {location.latitude}, Lng: {location.longitude}")
print(f"City: {location.place_name}")

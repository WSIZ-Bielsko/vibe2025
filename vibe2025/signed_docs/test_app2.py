import requests

payload = {
    'signer_id': 42,
    'public_key_pem': '''-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAsfdRGj66yKnbEzgQuxiQ
kCi27rd0ENboMpeM5OcOwzbtOvEYoGNRZWf/a3+TBh6NYqR49ozbHcyBJvrRxNnq
4OprXPRWfd0Xn6/3Dxjnakn2K2iHx3dUxhsb4Z4hLBd3eMIOr4dQzFi7jiC1hAIq
YJX8f3BGR605N7JXP0bocJGiYZwlEVZpN3GRoXt6G6IjpWIZFYl9caxJD7HQtqPp
XpcYpMwKrxKbjBO3vtsbhzZpTG3jQjYAIIVddLyhkGnMaY9xKgH9XjHLQO+XXChv
fUl1ZuNs41YmUP4/2/X2HK7afHnpUC3gzsIY75NNAWLMNwp6TVmRYRwtIdCZpg05
zQIDAQAB
-----END PUBLIC KEY-----'''
}

response = requests.post('http://localhost:8000/keys/add', json=payload)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

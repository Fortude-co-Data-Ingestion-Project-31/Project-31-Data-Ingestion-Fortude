import httpx 

# httpx s a Python library that lets your Python program send HTTP requests to web servers/APIs and receive their responses.
# response = httpx.get("https://api.open-meteo.com/v1/forecast", follow_redirects=True)

# # checking if the request is successful
# print ("Status Code: ", response.status_code)

# # Print the JSON data returned by the API
# #print("JSON Data:", response.json())


# print (response.text)

# parameters for the API request, this one is current weather which is a param which tell us how to get the current weather data from the API
parameters = {"current_weather": True,
              "latitude": -37.81,
              "longitude": 144.96} 

headers = {
    "Accept": "application/json"
}

response = httpx.get("https://api.open-meteo.com/v1/forecast", params = parameters, headers= headers, follow_redirects = True)

# print ("URL acutally requested:", response.url)
# print( "Status: ", response.status_code)
# print("Response:", response.text)



data = response.json()
print("Current Temperature: ", data["current_weather"]["temperature"])

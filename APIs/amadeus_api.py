from amadeus import Client, ResponseError

amadeus = Client(client_id='YDp2dotKO0oTzRQ2EALTAKVH4cY1D1Qm', client_secret='0v2nA55ooj6PKVgm')

try:
    response = amadeus.reference_data.airlines.get(airlineCodes='U2')
    print(response.data)
except ResponseError as error:
    print(error)

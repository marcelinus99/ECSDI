# Import JSON module
import json
from amadeus import Client, ResponseError

amadeus = Client(client_id='YDp2dotKO0oTzRQ2EALTAKVH4cY1D1Qm', client_secret='0v2nA55ooj6PKVgm')

IATA = {'Barcelona':'BCN', 'Madrid':'MAD', 'Paris':'PAR', 'Milan':'MIL', 'Londres':'LON', 'Munich':'MUC', 'NuevaYork':'NYC', 'Berlin':'BER'}
def search_hotels(destination):
    try:

        response = amadeus.shopping.hotel_offers.get(cityCode=IATA[destination]).result
        s1 = json.dumps(response)
        d2 = json.loads(s1)
        contenidoHoteles = {}
        for i in d2['data']:
            if i['hotel']['name'] not in "TEST CONTENT":
                name = i['hotel']['name']
                price = i['offers'][0]['price']['total']
                contenidoHoteles[name] = price

        return contenidoHoteles
    except ResponseError as error:
        print(error)


def search_vuelos(fechaIn, fechaFin, origin, destination):
    try:
        departureDate = fechaIn.replace('/', '-')
        response = amadeus.shopping.flight_offers_search.get(originLocationCode=IATA[origin], destinationLocationCode=IATA[destination], departureDate=departureDate, adults=1).result
        #response = amadeus.shopping.flight_offers_search.get(originLocationCode='SYD', destinationLocationCode='BKK', departureDate='2021-06-20', adults=1).result
        s1 = json.dumps(response)
        d2 = json.loads(s1)
        print(response)
        contenidoViaje = {}
        for i in d2['data']:

            price = i['price']['total']
            print(price)

        return contenidoViaje
    except ResponseError as error:
        print(error)

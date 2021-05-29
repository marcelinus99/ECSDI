# Import JSON module
import json
from amadeus import Client, ResponseError
from pyairports.airports import Airports

amadeus = Client(client_id='YDp2dotKO0oTzRQ2EALTAKVH4cY1D1Qm', client_secret='0v2nA55ooj6PKVgm')

IATA = {'Barcelona': 'BCN', 'Madrid': 'MAD', 'Paris': 'PAR', 'Milan': 'MIL', 'Londres': 'LON', 'Munich': 'MUC',
        'NuevaYork': 'NYC', 'Berlin': 'BER'}


def search_hotels(city):
    try:
        destination = str(city)
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
    global final
    try:
        fechaIn = str(fechaIn)
        fechaFin = str(fechaFin)
        origin = str(origin)
        destination = str(destination)
        departureDate = fechaIn.replace('/', '-')
        response = amadeus.shopping.flight_offers_search.get(originLocationCode=IATA[origin],
                                                             destinationLocationCode=IATA[destination],
                                                             departureDate=departureDate, adults=1).result
        s1 = json.dumps(response)
        d2 = json.loads(s1)
        airports = Airports()
        contenidoViaje = {}
        for i in d2['data']:
            price = i['price']['total']
            it = i['itineraries'][0]['segments']
            for i2 in it:
                final = i2['arrival']['iataCode']
            a = airports.airport_iata(final)
            #cositas = a[0] + "/" + price
            contenidoViaje[a[0]] = price

        return contenidoViaje
    except ResponseError as error:
        print(error)

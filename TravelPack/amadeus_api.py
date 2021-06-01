# Import JSON module
import json

import foursquare
from amadeus import Client, ResponseError
from TravelPack.pyairports.airports import Airports

amadeus = Client(client_id='YDp2dotKO0oTzRQ2EALTAKVH4cY1D1Qm', client_secret='0v2nA55ooj6PKVgm')

IATA = {'Barcelona': 'BCN', 'Madrid': 'MAD', 'Paris': 'PAR', 'Milan': 'MIL', 'Londres': 'LON', 'Munich': 'MUC',
        'NuevaYork': 'NYC', 'Berlin': 'BER'}

GEO = {'Barcelona': '41.390205/2.154007', 'Madrid': '40.416775/-3.703790', 'Paris': '48.858093/2.294694',
       'Milan': '45.464664/9.188540', 'Londres': '51.509865/-0.118092', 'Munich': '48.137154/11.576124',
       'NuevaYork': '40.785091/-73.968285', 'Berlin': '52.531677/13.381777'}

CLIENT_ID = 'OTXPMRAIY0GHYDTPXELL1EDHFYNVVRFEMQLHUUVXNEYV1DDS'
CLIENT_SECRET = '50FCYQPJSHM4CBVXVQFKXVM2AMKAIAEQ3LDZVZZZ44O10MTV'


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
            # cositas = a[0] + "/" + price
            contenidoViaje[a[0]] = price

        return contenidoViaje
    except ResponseError as error:
        print(error)


def search_activity(ciudad):
    pos = GEO[str(ciudad)].split('/')
    latitude = pos[0]
    longitud = pos[1]

    client = foursquare.Foursquare(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

    v = client.venues.search(params={'ll': '41.4,2.14',
                                     'intent': 'browse',
                                     'radius': '4000',
                                     'query': 'museo'})
    k = v["venues"]
    for result in k:
        print(result["name"])

    response = amadeus.reference_data.locations.points_of_interest.get(latitude=float(latitude),
                                                                       longitude=float(longitud)).result
    s1 = json.dumps(response)
    d2 = json.loads(s1)
    contenidoHoteles = {}
    for i in d2['data']:
        nombre = i["name"]
        categoria = i["category"]
        contenidoHoteles[nombre] = categoria
    return contenidoHoteles

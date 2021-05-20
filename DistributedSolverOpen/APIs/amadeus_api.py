# Import JSON module
import json
from amadeus import Client, ResponseError

amadeus = Client(client_id='YDp2dotKO0oTzRQ2EALTAKVH4cY1D1Qm', client_secret='0v2nA55ooj6PKVgm')


def search_hotels():
    try:
        response = amadeus.shopping.hotel_offers.get(cityCode='LON').result
        s1 = json.dumps(response)
        d2 = json.loads(s1)

        putamierda = ''

        print(response)
        for i in d2['data']:
            if i['hotel']['name'] not in "TEST CONTENT":
                print(i['hotel']['name'])
                putamierda = i['offers']
                s2 = json.dumps(putamierda)
                d3 = json.loads(s2)
                for i2 in d3['price']:
                    print(i2['total'])


        return response
    except ResponseError as error:
        print(error)

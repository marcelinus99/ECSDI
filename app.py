from flask import Flask, request
import foursquare


DBPEDIA = "http://dbpedia.org/sparql"
GEODATA = "http://linkedgeodata.org/sparql"
LGEODATA = "http://live.linkedgeodata.org/sparql"

app = Flask(__name__)

url = 'http://127.0.0.1:5000/'


@app.route('/')
def hello():
    CLIENT_ID = 'OTXPMRAIY0GHYDTPXELL1EDHFYNVVRFEMQLHUUVXNEYV1DDS'
    CLIENT_SECRET = '50FCYQPJSHM4CBVXVQFKXVM2AMKAIAEQ3LDZVZZZ44O10MTV'

    client = foursquare.Foursquare(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

    v = client.venues.search(params={'ll': '41.4,2.14',
                                     'intent': 'browse',
                                     'radius': '4000',
                                     'query': 'museo'})
    k = v["venues"]
    for result in k:
        var = result["name"]
        print(var)
    return 'hello'


@app.route('/agente', methods=['GET', 'POST'])
def peticion_objeto():
    if request.method == 'GET':
        return 'GET recibido'
    else:
        return 'POST recibido'


@app.route('/sumador', methods=['GET'])
def sumador():
    if request.method == 'GET':
        x = int(request.args['x'])
        y = int(request.args['y'])
        return str(x + y)


if __name__ == '__main__':
    app.run()

import requests
from flask import Flask, request
import requests
from rdflib import URIRef, BNode, Literal, Namespace, RDF, FOAF, Graph
from SPARQLWrapper import SPARQLWrapper, JSON
import foursquare

app = Flask(__name__)

g = Graph()

url = 'http://127.0.0.1:5000/'

array = ["pepito", "a"]

url2 = 'http://127.0.0.1:5000/persona'


def getHotels():
    CLIENT_ID = 'OTXPMRAIY0GHYDTPXELL1EDHFYNVVRFEMQLHUUVXNEYV1DDS'
    CLIENT_SECRET = '50FCYQPJSHM4CBVXVQFKXVM2AMKAIAEQ3LDZVZZZ44O10MTV'

    client = foursquare.Foursquare(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

    v = client.venues.search(params={'ll': '41.4,2.14',
                                     'intent': 'browse',
                                     'radius': '4000',
                                     'query': 'museo'})
    k = v["venues"]
    for result in k:
        print(result["name"])


def prueba():
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setQuery("""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT DISTINCT *
            WHERE { <http://dbpedia.org/resource/American_Airlines> ?prop ?val.
            }""")
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    for result in results["results"]["bindings"]:
        print(result["prop"]["value"])

    print('---------------------------')

    pedro = URIRef(url2 + '/pedro')
    maria = BNode()

    nombre = Literal('Pedro')
    edad = Literal(22)
    mm = Namespace(url2)

    pedro = mm.pedro
    maria = mm.maria

    g.add((pedro, RDF.type, FOAF.Person))
    g.add((maria, RDF.type, FOAF.Person))
    g.add((pedro, FOAF.name, Literal('Pedro')))
    g.add((maria, FOAF.name, Literal('Maria')))
    g.add((pedro, FOAF.knows, maria))


@app.route('/persona')
def hello2():
    mm = Namespace(url2)
    if (mm.jose, RDF.type, FOAF.Person) in g:
        print("Pedro es una persona")

    return "Hello, World!"


@app.route('/')
def hello():
    numeros = {'x': 'olaktal'}
    requests.post(url + '/agente', params=numeros)
    getHotels()
    return "Hello, World!"


@app.route('/agente', methods=['GET', 'POST'])
def peticion_objeto():
    if request.method == 'GET':
        # peticion = {'x': 22, 'y': 65}
        # r = requests.get(url + '/sumador', params=peticion)
        print(array)
        return array[2]
    else:
        x = request.args['x']
        array.insert(2, x)
        return 'posteado'


@app.route('/sumador')
def sumador():
    x = int(request.args['x'])
    y = int(request.args['y'])
    return str(x + y)


if __name__ == '__main__':
    app.run()


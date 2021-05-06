import requests
from flask import Flask, request
import requests
from rdflib import URIRef, BNode, Literal, Namespace, RDF, FOAF, Graph
from SPARQLWrapper import SPARQLWrapper, JSON


app = Flask(__name__)

g = Graph()

url = 'http://127.0.0.1:5000/'

array = ["pepito","a"]

url2 = 'http://127.0.0.1:5000/persona'


def getHotels():
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setQuery("""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX ogc: <http://www.opengis.net/ont/geosparql#>
        PREFIX geom: <http://geovocab.org/geometry#>
        PREFIX lgdo: <http://linkedgeodata.org/ontology/>
        SELECT *
        WHERE {
            ?s rdf:type lgdo:Restaurant ;
            rdfs:label ?l ;
            geom:geometry [ogc:asWKT ?g] .
            Filter(bif:st_intersects (?g, bif:st_point (2.16, 41.4), 0.4)) .
        }

        """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    for result in results["results"]["bindings"]:
        print(result["label"]["value"])

    print('---------------------------')

    for result in results["results"]["bindings"]:
        print('%s: %s' % (result["label"]["xml:lang"], result["label"]["value"]))


    


def prueba():

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
        #peticion = {'x': 22, 'y': 65}
        #r = requests.get(url + '/sumador', params=peticion)
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
    return str(x+y)


if __name__ == '__main__':
    app.run()
    

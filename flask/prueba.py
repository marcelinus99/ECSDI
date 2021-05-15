from rdflib import URIRef, BNode, Literal, Namespace, RDF, FOAF, Graph





class A(object):

    url = 'http://127.0.0.1:5000/grafos'

    def prueba:
        g = Graph()

        mm = Namespace(url)

        pedro = mm.pedro
        maria = mm.maria

        g.add((pedro, RDF.type, FOAF.persona))
        g.add((maria, RDF.type, FOAF.persona))
        g.add((pedro, FOAF.name, Literal('Pedro')))
        g.add((maria, FOAF.name, Literal('Maria')))
        g.add((pedro, FOAF.knows, maria))



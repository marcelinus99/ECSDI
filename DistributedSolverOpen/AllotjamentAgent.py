"""
.. module:: AllotjamentAgent

AllotjamentAgent
*************

:Description: Allotjament Agent

    Buscador de alojamientos para un paquete de viaje

:Authors:
    Carles Llongueras Aparicio
    Alexandre Fló Cuesta
    Marc González Moratona


:Version:

:Created on: 18/05/2021 17:06

"""
from uuid import uuid4
from rdflib import Graph, Namespace, Literal
from AgentUtil.DSO import DSO
from AgentUtil.Agent import Agent
from AgentUtil.ACLMessages import build_message, send_message, get_message_properties
from rdflib.namespace import FOAF, RDF, XSD
from AgentUtil.ACL import ACL
from AgentUtil.OntoNamespaces import EJEMPLO
from amadeus_api import search_hotels
from Util import gethostname
import socket
import argparse
from FlaskServer import shutdown_server
import requests
from flask import Flask, request, render_template
from multiprocessing import Process, Queue
import logging
from AgentUtil.Logging import config_logger

__author__ = 'Alexandre Fló Cuesta', 'Marc González Moratona', 'Carles Llongueras Aparicio'

a = ''

app = Flask(__name__)

problems = {}

# Logging
logger = config_logger(level=1)

# Configuration constants and variables
agn = Namespace("http://www.agentes.org#")

# Contador de mensajes
mss_cnt = 0

# Definimos los parametros de la linea de comandos
parser = argparse.ArgumentParser()
parser.add_argument('--open', help="Define si el servidor esta abierto al exterior o no", action='store_true',
                    default=False)
parser.add_argument('--verbose', help="Genera un log de la comunicacion del servidor web", action='store_true',
                    default=False)
parser.add_argument('--port', type=int, help="Puerto de comunicacion del agente")
parser.add_argument('--dhost', help="Host del agente de directorio")
parser.add_argument('--dport', type=int, help="Puerto de comunicacion del agente de directorio")

# parsing de los parametros de la linea de comandos
args = parser.parse_args()
if not args.verbose:
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

# Configuration stuff
if args.port is None:
    port = 9020
else:
    port = args.port

if args.open:
    hostname = '0.0.0.0'
    hostaddr = gethostname()
else:
    hostaddr = hostname = socket.gethostname()

if args.dport is None:
    dport = 9000
else:
    dport = args.dport

if args.dhost is None:
    dhostname = socket.gethostname()
else:
    dhostname = args.dhost

# Datos del Agente
AllotjamentAgent = Agent('HotelAgent',
                         agn.AllotjamentAgent,
                         'http://%s:%d/comm' % (hostaddr, port),
                         'http://%s:%d/stop' % (hostaddr, port))

# Directory agent address
DirectoryService = Agent('DirectoryService',
                         agn.DirectoryService,
                         'http://%s:%d/register' % (dhostname, dport),
                         'http://%s:%d/stop' % (dhostname, dport))

# Global dsgraph triplestore
dsgraph = Graph()

# Cola de comunicacion entre procesos
cola1 = Queue()


def obscure(dir):
    """
    Hide real hostnames
    """
    odir = {}
    for d in dir:
        _, _, port = dir[d][1].split(':')
        odir[d] = (dir[d][0], f'{uuid4()}:{port}', dir[d][2], dir[d][3])

    return odir


@app.route('/info')
def info():
    """
    Entrada que da informacion sobre el agente a traves de una pagina web
    """
    return a


def solver(city):
    """
    Hace la resolucion de un problema

    :param param:
    :return:
    """
    res = search_hotels(city)
    return res


def register_message():
    """
    Envia un mensaje de registro al servicio de registro
    usando una performativa Request y una accion Register del
    servicio de directorio

    :param gmess:
    :return:
    """

    logger.info('Nos registramos')

    global mss_cnt
    global agn

    gmess = Graph()

    # Construimos el mensaje de registro
    gmess.bind('foaf', FOAF)
    gmess.bind('dso', DSO)
    reg_obj = agn[AllotjamentAgent.name + '-Register']
    gmess.add((reg_obj, RDF.type, DSO.Register))
    gmess.add((reg_obj, DSO.Uri, AllotjamentAgent.uri))
    gmess.add((reg_obj, FOAF.name, Literal(AllotjamentAgent.name)))
    gmess.add((reg_obj, DSO.Address, Literal(AllotjamentAgent.address)))
    gmess.add((reg_obj, DSO.AgentType, DSO.HotelsAgent))

    # Lo metemos en un envoltorio FIPA-ACL y lo enviamos
    gr = send_message(
        build_message(gmess, perf=ACL.request,
                      sender=AllotjamentAgent.uri,
                      receiver=DirectoryService.uri,
                      content=reg_obj,
                      msgcnt=mss_cnt),
        DirectoryService.address)

    mss_cnt += 1

    return gr


@app.route("/stop")
def stop():
    """
    Entrypoint que para el agente

    :return:
    """
    tidyup()
    shutdown_server()
    return "Parando Servidor"


@app.route("/comm")
def comunicacion():
    """
    Entrypoint de comunicacion del agente
    Simplemente retorna un objeto fijo que representa una
    respuesta a una busqueda de hotel

    Asumimos que se reciben siempre acciones que se refieren a lo que puede hacer
    el agente (buscar con ciertas restricciones, reservar)
    Las acciones se mandan siempre con un Request
    Prodriamos resolver las busquedas usando una performativa de Query-ref
    """
    global dsgraph
    global mss_cnt

    logger.info('Peticion de informacion recibida')

    # Extraemos el mensaje y creamos un grafo con el
    message = request.args['content']
    gm = Graph()
    gm.parse(data=message)

    msgdic = get_message_properties(gm)

    # Comprobamos que sea un mensaje FIPA ACL
    if msgdic is None:
        # Si no es, respondemos que no hemos entendido el mensaje
        gr = build_message(Graph(), ACL['not-understood'], sender=AllotjamentAgent.uri, msgcnt=mss_cnt)
    else:
        # Obtenemos la performativa
        perf = msgdic['performative']

        if perf != ACL.request:
            # Si no es un request, respondemos que no hemos entendido el mensaje
            gr = build_message(Graph(), ACL['not-understood'], sender=AllotjamentAgent.uri, msgcnt=mss_cnt)
        else:
            # Extraemos el objeto del contenido que ha de ser una accion de la ontologia de acciones del agente
            # de registro
            # Averiguamos el tipo de la accion
            respuesta = Graph()
            if 'content' in msgdic:
                content = msgdic['content']
                accion = gm.value(subject=content, predicate=RDF.type)
                if accion == EJEMPLO.VIAJE:
                    c = gm.value(subject=content, predicate=EJEMPLO.City)
                    solution = solver(c)

                    for value in solution:
                        clave = value
                        valor = solution[value]
                        reg_obj = EJEMPLO[AllotjamentAgent.name + '-response' + value]
                        respuesta.add((reg_obj, RDF.type, EJEMPLO.ALOJAMIENTO))
                        respuesta.add((reg_obj, EJEMPLO.Nombre, Literal(clave, datatype=XSD.string)))
                        respuesta.add((reg_obj, EJEMPLO.Precio, Literal(valor)))

            # Aqui realizariamos lo que pide la accion
            # Por ahora simplemente retornamos un Inform-done
                gr = build_message(respuesta,
                                   ACL['inform'],
                                   sender=AllotjamentAgent.uri,
                                   msgcnt=mss_cnt,
                                   receiver=msgdic['sender'], )
            else:
                gr = build_message(Graph(),
                   ACL['inform'],
                   sender=AllotjamentAgent.uri,
                   msgcnt=mss_cnt,
                   receiver=msgdic['sender'], )

    logger.info('Respondemos a la peticion')
    mss_cnt += 1
    return gr.serialize(format='xml')


def tidyup():
    """
    Acciones previas a parar el agente

    """
    global cola1
    cola1.put(0)


def agentbehavior1(cola):
    """
    Un comportamiento del agente

    :return:
    """
    # Registramos el agente
    gr = register_message()

    # Escuchando la cola hasta que llegue un 0
    """fin = False
    while not fin:
        while cola.empty():
            pass
        v = cola.get()
        if v == 0:
            fin = True
        else:
            print(v)"""


if __name__ == '__main__':
    # Ponemos en marcha los behaviors
    ab1 = Process(target=agentbehavior1, args=(cola1,))
    ab1.start()

    # Ponemos en marcha el servidor
    app.run(host=hostname, port=port)

    # Esperamos a que acaben los behaviors
    ab1.join()



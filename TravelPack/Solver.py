"""
.. module:: Solver

Solver
*************

:Description: Solver

    Solver generico que pasa los problemas a solvers especializados

:Authors:
    Carles Llongueras Aparicio
    Alexandre Fló Cuesta
    Marc González Moratona

:Version:

:Created on: 18/05/2021 17:06

"""

from multiprocessing import Process, Queue, Pipe
from Util import gethostname
import socket
import argparse
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import FOAF, RDF, XSD
from AgentUtil.ACL import ACL
from AgentUtil.DSO import DSO
from AgentUtil.OntoNamespaces import ECSDI
from AgentUtil.ACLMessages import build_message, send_message, get_message_properties

from FlaskServer import shutdown_server
from flask import Flask, render_template, request
from uuid import uuid4
import logging
from AgentUtil.Logging import config_logger
from AgentUtil.Agent import Agent
from rdflib import Graph, Namespace

__author__ = 'Alexandre Fló Cuesta', 'Marc González Moratona', 'Carles Llongueras Aparicio'

# Definimos los parametros de la linea de comandos
parser = argparse.ArgumentParser()
parser.add_argument('--open', help="Define si el servidor esta abierto al exterior o no", action='store_true',
                    default=False)
parser.add_argument('--verbose', help="Genera un log de la comunicacion del servidor web", action='store_true',
                    default=False)
parser.add_argument('--port', type=int, help="Puerto de comunicacion del agente")
parser.add_argument('--dhost', help="Host del agente de directorio")
parser.add_argument('--dport', type=int, help="Puerto de comunicacion del agente de directorio")

# Logging
logger = config_logger(level=1)

# parsing de los parametros de la linea de comandos
args = parser.parse_args()

if not args.verbose:
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

# Configuration stuff
if args.port is None:
    port = 9001
else:
    port = args.port

if args.dport is None:
    dport = 9000
else:
    dport = args.dport

if args.open:
    hostname = '0.0.0.0'
    hostaddr = gethostname()
else:
    hostaddr = hostname = socket.gethostname()

if args.dhost is None:
    dhostname = gethostname()
else:
    dhostname = args.dhost

# Configuration constants and variables
agn = Namespace("http://www.agentes.org#")

# Contador de mensajes
mss_cnt = 0

# Datos del Agente
Solver = Agent('SolverAgent',
               agn.Solver,
               'http://%s:%d/comm' % (hostaddr, port),
               'http://%s:%d/stop' % (hostaddr, port))

# Directory agent address
DirectoryService = Agent('ServiceAgent',
                         agn.DirectoryService,
                         'http://%s:%d/register' % (dhostname, dport),
                         'http://%s:%d/stop' % (dhostname, dport))

# Global dsgraph triplestore
dsgraph = Graph()

# Cola de comunicacion entre procesos
cola1 = Queue()

app = Flask(__name__)

allot = {}
transp = {}
activ = {}
peticiones = 0

alojamientos = {}
transportes = {}
actividades = {}
t_barato = []
t_bar = {}
a_barato = []
all_l = {}
tr_l = {}


@app.route('/info')
def info():
    """
    Entrada que da informacion sobre el agente a traves de una pagina web
    """
    global allot
    global transp
    global activ
    return render_template('solverproblems.html', all=allot, tra=transp, act=activ)


@app.route('/iface')
def iface():
    """
    Interfaz con el solver a traves de una pagina de web
    """
    global allot
    global transp
    global activ

    citylist = ['Barcelona', 'Madrid', 'Paris', 'Milan', 'Londres', 'Munich', 'NuevaYork', 'Berlin']
    activity = ['Nada', 'Algo', 'Normal', 'Mucho']
    return render_template('iface.html', cities=citylist, activitytype=activity, all=allot, tra=transp, act=activ)


def tidyup():
    """
    Acciones previas a parar el agente

    """
    pass


@app.route("/stop")
def stop():
    """
    Entrypoint que para el agente

    :return:
    """
    tidyup()
    shutdown_server()
    return "Parando Servidor"


@app.route("/message", methods=['GET', 'POST'])
def start():
    global allot
    global transp
    global activ

    global alojamientos
    global transportes
    global actividades

    global peticiones
    global a_barato
    global t_barato
    global all_l
    global tr_l
    global t_bar

    if request.method == 'POST':
        q1 = Queue()
        q2 = Queue()
        q3 = Queue()
        origen = request.form['origin-city']
        destino = request.form['destination-city']
        fecha_ini = request.form['trip-start']
        fecha_fin = request.form['trip-end']
        max_p = request.form['price-max']
        min_p = request.form['price-min']
        p1 = Process(target=buscarAllotjament, args=(fecha_ini, fecha_fin, destino, q1))
        p2 = Process(target=buscarTransport, args=(fecha_ini, fecha_fin, origen, destino, q2))
        p3 = Process(target=buscarActivitats, args=(destino, q3))
        p1.start()
        p2.start()
        p3.start()
        p1.join()
        p2.join()
        p3.join()
        allot = q1.get()
        transp = q2.get()
        activ = q3.get()
        peticiones += 1

        for i in range(len(allot)):
            for j in range(len(transp)):
                if (float(max_p) >= float(allot[i][5]) + float(transp[j][6])) and (
                        float(allot[i][5]) + float(transp[j][6]) >= float(min_p)):
                    t_barato.append(
                        [fecha_ini, fecha_fin, origen, destino, allot[i][4], allot[i][5], transp[j][5], transp[j][6],
                         round((float(transp[j][6]) + float(allot[i][5])), 2)])

        for i in range(len(allot)):
            if float(max_p) >= float(allot[i][5]) >= float(min_p):
                all_l[i] = allot[i]

        for i in range(len(transp)):
            if float(max_p) >= float(transp[i][6]) >= float(min_p):
                tr_l[i] = transp[i]

        for i in range(len(t_barato)):
            t_bar[i] = t_barato[i]

    if all_l is None or tr_l is None or t_bar is None or activ is None:
        return render_template('clientproblems.html', all=all_l, tra=tr_l, bar=t_bar, act=activ, p=peticiones)
    else:
        return render_template('restricted.html')


def directory_search_message(type):
    """
    Busca en el servicio de registro mandando un
    mensaje de request con una accion Seach del servicio de directorio

    Podria ser mas adecuado mandar un query-ref y una descripcion de registo
    con variables

    :param type:
    :return:
    """
    global mss_cnt
    logger.info('Buscamos en el servicio de registro')

    gmess = Graph()

    gmess.bind('foaf', FOAF)
    gmess.bind('dso', DSO)
    reg_obj = agn[Solver.name + '-search']
    gmess.add((reg_obj, RDF.type, DSO.Search))
    gmess.add((reg_obj, DSO.AgentType, type))
    msg = build_message(gmess, perf=ACL.request,
                        sender=Solver.uri,
                        receiver=DirectoryService.uri,
                        content=reg_obj,
                        msgcnt=mss_cnt)
    gr = send_message(msg, DirectoryService.address)
    mss_cnt += 1
    logger.info('Recibimos informacion del agente')

    return gr


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
        gr = build_message(Graph(), ACL['not-understood'], sender=Solver.uri, msgcnt=mss_cnt)
    else:
        # Obtenemos la performativa
        perf = msgdic['performative']

        if perf != ACL.request:
            # Si no es un request, respondemos que no hemos entendido el mensaje
            gr = build_message(Graph(), ACL['not-understood'], sender=Solver.uri, msgcnt=mss_cnt)
        else:
            # Extraemos el objeto del contenido que ha de ser una accion de la ontologia de acciones del agente
            # de registro

            # Averiguamos el tipo de la accion
            if 'content' in msgdic:
                content = msgdic['content']
                accion = gm.value(subject=content, predicate=RDF.type)

            # Aqui realizariamos lo que pide la accion
            # Por ahora simplemente retornamos un Inform-done
            gr = build_message(Graph(),
                               ACL['inform'],
                               sender=Solver.uri,
                               msgcnt=mss_cnt,
                               receiver=msgdic['sender'], )
    mss_cnt += 1

    logger.info('Respondemos a la peticion')

    return gr.serialize(format='xml')


def buscarTransport(fecha_ini, fecha_fin, origen, destino, q1):
    global mss_cnt
    global transportes
    global transp

    gr = directory_search_message(DSO.FlightsAgent)
    logger.info('Enviamos informacion a transport')
    grafo = Graph()
    reg_obj = ECSDI[Solver.name + '-info-sendTran']
    grafo.add((reg_obj, RDF.type, ECSDI.LLEGAR))
    grafo.add((reg_obj, ECSDI.INI, Literal(fecha_ini, datatype=XSD.string)))
    grafo.add((reg_obj, ECSDI.FI, Literal(fecha_fin, datatype=XSD.string)))
    grafo.add((reg_obj, ECSDI.CityIN, Literal(origen, datatype=XSD.string)))
    grafo.add((reg_obj, ECSDI.CityFIN, Literal(destino, datatype=XSD.string)))

    msg = gr.value(predicate=RDF.type, object=ACL.FipaAclMessage)
    content = gr.value(subject=msg, predicate=ACL.content)
    ragn_addr = gr.value(subject=content, predicate=DSO.Address)
    ragn_uri = gr.value(subject=content, predicate=DSO.Uri)

    msg = build_message(grafo, perf=ACL.request,
                        sender=Solver.uri,
                        receiver=ragn_uri,
                        content=reg_obj,
                        msgcnt=mss_cnt)
    gr_allot = send_message(msg, ragn_addr)
    i = 0
    for objects in gr_allot.subjects(RDF.type, ECSDI.FlightsAgent):
        nom = gr_allot.value(subject=objects, predicate=ECSDI.Nombre)
        precio = gr_allot.value(subject=objects, predicate=ECSDI.Precio)
        transportes[i] = [nom, precio]
        i += 1
    logger.info('Respuesta transport recibida')
    mss_cnt += 1

    for i in range(len(transportes)):
        transp[i] = ['REQTRANSPORT',  fecha_ini, fecha_fin, origen, destino, transportes[i][0], transportes[i][1], 0.00]

    q1.put(transp)


def buscarAllotjament(fecha_ini, fecha_fin, destino, q2):
    """
    Un comportamiento del agente

    :return:
    """

    # Buscamos en el directorio
    # un agente de hoteles
    global mss_cnt
    global alojamientos
    global allot

    gr = directory_search_message(DSO.HotelsAgent)
    logger.info('Enviamos informacion a allotjament')
    grafo = Graph()
    reg_obj = ECSDI[Solver.name + '-info-sendAl']
    grafo.add((reg_obj, RDF.type, ECSDI.VIAJE))
    grafo.add((reg_obj, ECSDI.City, Literal(destino, datatype=XSD.string)))

    msg = gr.value(predicate=RDF.type, object=ACL.FipaAclMessage)
    content = gr.value(subject=msg, predicate=ACL.content)
    ragn_addr = gr.value(subject=content, predicate=DSO.Address)
    ragn_uri = gr.value(subject=content, predicate=DSO.Uri)

    msg = build_message(grafo, perf=ACL.request,
                        sender=Solver.uri,
                        receiver=ragn_uri,
                        content=reg_obj,
                        msgcnt=mss_cnt)
    gr_transp = send_message(msg, ragn_addr)
    i = 0
    for objects in gr_transp.subjects(RDF.type, ECSDI.ALOJAMIENTO):
        nom = gr_transp.value(subject=objects, predicate=ECSDI.Nombre)
        precio = gr_transp.value(subject=objects, predicate=ECSDI.Precio)
        alojamientos[i] = [nom, precio]
        i += 1
    logger.info('Respuesta allotjament recibida')
    mss_cnt += 1

    for i in range(len(alojamientos)):
        allot[i] = ['REQALLOTJAMENT', fecha_ini, fecha_fin, destino, alojamientos[i][0], alojamientos[i][1]]

    q2.put(allot)


def buscarActivitats(destino, q3):
    global mss_cnt
    global actividades
    global activ

    gr = directory_search_message(DSO.TravelServiceAgent)
    logger.info('Enviamos informacion a activitats')
    grafo = Graph()
    reg_obj = ECSDI[Solver.name + '-info-sendAc']
    grafo.add((reg_obj, RDF.type, ECSDI.VIAJE))
    grafo.add((reg_obj, ECSDI.City, Literal(destino, datatype=XSD.string)))

    msg = gr.value(predicate=RDF.type, object=ACL.FipaAclMessage)
    content = gr.value(subject=msg, predicate=ACL.content)
    ragn_addr = gr.value(subject=content, predicate=DSO.Address)
    ragn_uri = gr.value(subject=content, predicate=DSO.Uri)

    msg = build_message(grafo, perf=ACL.request,
                        sender=Solver.uri,
                        receiver=ragn_uri,
                        content=reg_obj,
                        msgcnt=mss_cnt)
    gr_act = send_message(msg, ragn_addr)
    i = 0
    for objects in gr_act.subjects(RDF.type, ECSDI.ACTIVITY):
        nom = gr_act.value(subject=objects, predicate=ECSDI.Nombre)
        tipo = gr_act.value(subject=objects, predicate=ECSDI.Tipo)
        actividades[i] = [nom, tipo]
        i += 1
    logger.info('Respuesta activitats recibida')
    mss_cnt += 1

    for i in range(len(actividades)):
        if str(actividades[i][1]) == "RESTAURANT":
            actividades[i][1] = "Lúdica"
        elif str(actividades[i][1]) == "SHOPPING":
            actividades[i][1] = "Festiva"
        elif str(actividades[i][1]) == "SIGHTS":
            actividades[i][1] = "Cultural"
        else:
            actividades[i][1] = "Lúdica"
        activ[i] = ['REQACTIVITAT', destino, actividades[i][0], actividades[i][1]]
    q3.put(activ)


def infoagent_search_message(addr, ragn_uri):
    """
    Envia una accion a un agente de informacion
    """
    global mss_cnt
    logger.info('Hacemos una peticion al servicio de informacion')

    gmess = Graph()

    # Supuesta ontologia de acciones de agentes de informacion
    IAA = Namespace('IAActions')

    gmess.bind('foaf', FOAF)
    gmess.bind('iaa', IAA)
    reg_obj = agn[Solver.name + '-info-search']
    gmess.add((reg_obj, RDF.type, IAA.Search))

    msg = build_message(gmess, perf=ACL.request,
                        sender=Solver.uri,
                        receiver=ragn_uri,
                        msgcnt=mss_cnt)
    gr = send_message(msg, addr)
    mss_cnt += 1
    logger.info('Recibimos respuesta a la peticion al servicio de informacion')

    return gr


if __name__ == '__main__':
    # Ponemos en marcha el servidor Flask
    app.run(host=hostname, port=port, debug=True, use_reloader=False)

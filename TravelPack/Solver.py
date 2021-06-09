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
import random
from datetime import date, timedelta
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
    global allot2
    global transp
    global activ

    citylist = ['Barcelona', 'Paris', 'Londres', 'NuevaYork', 'Berlin']
    activity = ['Sí', 'No']
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
    global allot, activities
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
        ludicas = request.form['ludic-activities']
        festivas = request.form['party-activities']
        cultural = request.form['cultural-activities']
        origen = request.form['origin-city']
        destino = request.form['destination-city']
        fecha_ini = request.form['trip-start']
        fecha_fin = request.form['trip-end']
        logger.info(fecha_ini)
        fi = fecha_ini.split('-')
        fn = fecha_fin.split('-')
        d0 = date(int(str(fi[0])), int(str(fi[1])), int(str(fi[2])))
        d1 = date(int(str(fn[0])), int(str(fn[1])), int(str(fn[2])))
        delt = d1 - d0

        max_p = request.form['price-max']
        min_p = request.form['price-min']
        if str(origen) == str(destino):
            return render_template('restricted.html', error="La ciudad de origen es la misma que la de destino.")
        elif int(delt.days) > 10:
            return render_template('restricted.html', error="El tiempo máximo de un viaje en nuestro sistema son 10 días.")
        elif int(str(min_p)) >= int(str(max_p)):
            return render_template('restricted.html', error="El precio mínimo es igual o superior al precio máximo.")
        elif str(cultural) == "No" and str(festivas) == "No" and str(ludicas) == "No":
            return render_template('restricted.html', error="No has marcado ningún tipo de actividad.")
        elif d0 >= d1:
            return render_template('restricted.html', error="La fecha de retorno es posterior o igual a la de salida.")
        else:
            p1 = Process(target=buscarAllotjament, args=(fecha_ini, fecha_fin, destino, q1))
            p2 = Process(target=buscarTransport, args=(fecha_ini, fecha_fin, origen, destino, q2))
            p3 = Process(target=buscarActivitats, args=(destino, ludicas, festivas, cultural, q3))
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
            activities = {}
            keys = list(activ.keys())
            random.shuffle(keys)
            for i in range(delt.days*3):
                activities[i] = activ[i]
                if i % 3 == 0:
                    activities[i][5] = "Mañana"
                elif i % 3 == 1:
                    activities[i][5] = "Tarde"
                elif i % 3 == 2:
                    activities[i][5] = "Noche"

            d1 = date(int(str(fn[0])), int(str(fn[1])), int(str(fn[2])))
            i = 0
            for single_date in daterange(d0, d1):
                for j in range(0, 3):
                    activities[i][4] = single_date.strftime("%Y-%m-%d")
                    i += 1

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

    if len(all_l) == 0:
        return render_template('restricted.html', error="No se han encontrado alojamientos en la ciudad indicada.")
    elif len(tr_l) == 0:
        return render_template('restricted.html', error="No se ha encontrado ningún transporte entre las ciudades indicadas.")
    elif len(t_bar) == 0:
        return render_template('restricted.html',
                               error="No se ha encontrado ninguna combinación de transporte y alojamiento con el rango de precios indicado.")
    elif len(activ) == 0:
        return render_template('restricted.html', error="No se ha encontrado ninguna actividad en la ciudad indicada.")
    else:
        return render_template('clientproblems.html', all=all_l, tra=tr_l, bar=t_bar, act=activities, p=peticiones)


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)



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
    grafo.add((reg_obj, RDF.type, ECSDI.VIAJE))
    grafo.add((reg_obj, ECSDI.FechaInicio, Literal(fecha_ini, datatype=XSD.string)))
    grafo.add((reg_obj, ECSDI.FechaFinal, Literal(fecha_fin, datatype=XSD.string)))
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
    for objects in gr_allot.subjects(RDF.type, ECSDI.Transporte):
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


def buscarActivitats(destino, ludicas, festivas, cultural, q3):
    global mss_cnt
    global actividades
    global activ

    gr = directory_search_message(DSO.TravelServiceAgent)
    logger.info('Enviamos informacion a activitats')
    grafo = Graph()
    reg_obj = ECSDI[Solver.name + '-info-sendAc']
    grafo.add((reg_obj, RDF.type, ECSDI.VIAJE))
    grafo.add((reg_obj, ECSDI.City, Literal(destino, datatype=XSD.string)))
    grafo.add((reg_obj, ECSDI.Cultural, Literal(cultural, datatype=XSD.string)))
    grafo.add((reg_obj, ECSDI.Festiva, Literal(festivas, datatype=XSD.string)))
    grafo.add((reg_obj, ECSDI.Ludica, Literal(ludicas, datatype=XSD.string)))

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
        if str(actividades[i][1]) == "L":
            actividades[i][1] = "Lúdica"
        elif str(actividades[i][1]) == "F":
            actividades[i][1] = "Festiva"
        elif str(actividades[i][1]) == "C":
            actividades[i][1] = "Cultural"
        else:
            actividades[i][1] = "Lúdica"
        activ[i] = ['REQACTIVITAT', destino, actividades[i][0], actividades[i][1], "01/01/1970", "------"]
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

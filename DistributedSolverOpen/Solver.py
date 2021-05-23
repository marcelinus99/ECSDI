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

from multiprocessing import Process
from Util import gethostname
import socket
import argparse
from rdflib.namespace import FOAF, RDF
from AgentUtil.ACL import ACL
from AgentUtil.DSO import DSO
from AgentUtil.ACLMessages import build_message, send_message

from FlaskServer import shutdown_server
from flask import Flask, render_template
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

# parsing de los parametros de la linea de comandos
args = parser.parse_args()
if not args.verbose:
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

# Configuration stuff
if args.port is None:
    port = 9010
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
    hostaddr = hostname = '127.0.0.1'

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


app = Flask(__name__)

problems = {}

# Logging
logger = config_logger(level=1)


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
    global problems

    return render_template('solverproblems.html', probs=obscure(problems))


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
    # logger.info('Buscamos en el servicio de registro')

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
    # logger.info('Recibimos informacion del agente')

    return gr


def buscarAllotjament():
    """
    Un comportamiento del agente

    :return:
    """

    # Buscamos en el directorio
    # un agente de hoteles
    gr = directory_search_message(DSO.HotelsAgent)

    # Obtenemos la direccion del agente de la respuesta
    # No hacemos ninguna comprobacion sobre si es un mensaje valido
    msg = gr.value(predicate=RDF.type, object=ACL.FipaAclMessage)
    content = gr.value(subject=msg, predicate=ACL.content)
    ragn_addr = gr.value(subject=content, predicate=DSO.Address)
    ragn_uri = gr.value(subject=content, predicate=DSO.Uri)

    # Ahora mandamos un objeto de tipo request mandando una accion de tipo Search
    # que esta en una supuesta ontologia de acciones de agentes
    infoagent_search_message(ragn_addr, ragn_uri)


def infoagent_search_message(addr, ragn_uri):
    """
    Envia una accion a un agente de informacion
    """
    global mss_cnt
    # logger.info('Hacemos una peticion al servicio de informacion')

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
    # logger.info('Recibimos respuesta a la peticion al servicio de informacion')

    return gr


if __name__ == '__main__':
    # Ponemos en marcha los behaviors
    ab1 = Process(target=buscarAllotjament)
    ab1.start()

    # Ponemos en marcha el servidor Flask
    app.run(host=hostname, port=port, debug=True, use_reloader=False)

    # Esperamos a que acaben los behaviors
    ab1.join()


"""
.. module:: Client

Client
*************

:Description: Client

    Cliente del resolvedor distribuido

:Authors:
    Carles Llongueras Aparicio
    Alexandre Fló Cuesta
    Marc González Moratona


:Version:

:Created on: 18/05/2021 17:06

:Created on: 19/05/2021 10:27

"""

from Util import gethostname
import argparse
from FlaskServer import shutdown_server
import requests
from flask import Flask, request, render_template, url_for, redirect
import logging
import socket

__author__ = 'bejar'

app = Flask(__name__)

problems = {}
probcounter = 0
clientid = ''
diraddress = ''


@app.route("/message", methods=['GET', 'POST'])
def message():
    """
    Entrypoint para todas las comunicaciones

    :return:
    """
    global problems

    # if request.form.has_key('message'):
    if 'message' in request.form:
        send_message("REQALLOTJAMENT", request.form['trip-start'], request.form['trip-end'], '', request.form['destination-city'])
        send_message("REQTRANSPORT", request.form['trip-start'], request.form['trip-end'], request.form['origin-city'], request.form['destination-city'])
        return redirect(url_for('.iface'))
    else:
        # Respuesta del solver SOLVED|PROBID,SOLUTION
        mess = request.args['message'].split('|')
        if len(mess) == 2:
            messtype, messparam = mess
            if messtype == 'SOLVED':
                solution = messparam.split(',')
                if len(solution) == 2:
                    probid, sol = solution
                    print(sol)
                    if probid in problems:
                        if problems[probid][0] in ['REQALLOTJAMENT']:
                            a = sol.split(':')
                            problems[probid][11] = a[0]
                            problems[probid][12] = a[1]
                        elif problems[probid][0] in ['REQTRANSPORT']:
                            a = sol.split('/')
                            problems[probid][13] = a[0]
                            problems[probid][14] = a[1]

                        problems[probid][10] = 'SOLVED'
                    else:  # Para el script de test de stress
                        problems[probid] = ['DUMMY', 'DUMMY', sol]

        return 'OK'


@app.route('/info')
def info():
    """
    Entrada que da informacion sobre el agente a traves de una pagina web
    """
    global problems

    return render_template('clientproblems.html', probs=problems)


@app.route('/iface')
def iface():
    """
    Interfaz con el cliente a traves de una pagina de web
    """
    global problems

    citylist = ['Barcelona', 'Madrid', 'Paris', 'Milan', 'Londres', 'Munich', 'NuevaYork', 'Berlin']
    activity = ['Nada', 'Algo', 'Normal', 'Mucho']
    return render_template('iface.html', cities=citylist, activitytype=activity, probs=problems)


@app.route("/stop")
def stop():
    """
    Entrada que para el agente
    """
    shutdown_server()
    return "Parando Servidor"


def send_message(problem, start, end, origin, destination):
    """
    Envia un request a un solver

    mensaje:

    SOLVE|TYPE,PROBLEM,PROBID,CLIENTID

    :param probid:
    :param cityname:
    :param problem:
    :return:
    """
    global probcounter
    global clientid
    global diraddress
    global port
    global problems

    probid = f'{clientid}-{probcounter:03}'
    probcounter += 1

    # Busca un solver en el servicio de directorio
    solveradd = requests.get(diraddress + '/message', params={'message': f'SEARCH|SOLVER'}).text
    # Solver encontrado
    minp = ''
    maxp = ''
    ludic = ''
    cultural = ''
    party = ''
    priceHot = ''
    nameHot = ''
    priceTrans = ''
    aerop = ''
    if 'OK' in solveradd:
        # Le quitamos el OK de la respuesta
        solveradd = solveradd[4:]

        problems[probid] = [problem, start, end, origin, destination, minp, maxp, ludic, cultural, party, 'PENDING', priceHot, nameHot, priceTrans, aerop]
        mess = f'SOLVE|{problem},{clientadd},{probid},{start},{end},{origin},{destination}'
        resp = requests.get(solveradd + '/message', params={'message': mess}).text
        if 'ERROR' not in resp:
            problems[probid] = [problem, start, end, origin, destination, minp, maxp, ludic, cultural, party, 'PENDING', priceHot, nameHot, priceTrans, aerop]
        else:
            problems[probid] = [problem, start, end, origin, destination, minp, maxp, ludic, cultural, party, 'FAILED SOLVER', priceHot, nameHot, priceTrans, aerop]
    # Solver no encontrado
    else:
        problems[probid] = [problem, start, end, origin, destination, minp, maxp, ludic, cultural, party, 'FAILED DS', priceHot, nameHot]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--open', help="Define si el servidor esta abierto al exterior o no", action='store_true',
                        default=False)
    parser.add_argument('--verbose', help="Genera un log de la comunicacion del servidor web", action='store_true',
                        default=False)
    parser.add_argument('--port', default=None, type=int, help="Puerto de comunicacion del agente")
    parser.add_argument('--dir', default=None, help="Direccion del servicio de directorio")

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

    if args.open:
        hostname = '0.0.0.0'
        hostaddr = gethostname()
    else:
        hostaddr = hostname = socket.gethostname()

    print('DS Hostname =', hostaddr)

    clientadd = f'http://{hostaddr}:{port}'
    clientid = hostaddr.split('.')[0] + '-' + str(port)

    if args.dir is None:
        raise NameError('A Directory Service addess is needed')
    else:
        diraddress = args.dir

    # Ponemos en marcha el servidor Flask
    app.run(host=hostname, port=port, debug=True, use_reloader=False)

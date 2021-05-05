from flask import Flask, request
import requests

app = Flask(__name__)

url = 'http://127.0.0.1:5000/'

array = ["pepito","a"]


@app.route('/')
def hello():
    numeros = {'x': 'olaktal'}
    requests.post(url + '/agente', params=numeros)
    return "Hello, World!"


@app.route('/agente', methods=['GET', 'POST'])
def peticion_objeto():
    if request.method == 'GET':
        #peticion = {'x': 22, 'y': 65}
        #r = requests.get(url + '/sumador', params=peticion)
        print(array)
        return array[5]
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

import requests
from flask import Flask, request

app = Flask(__name__)

url = 'http://127.0.0.1:5000/'


@app.route('/')
def hello():
    return "Hello, World!"


@app.route('/agente', methods=['GET', 'POST'])
def peticion_objeto():
    if request.method == 'GET':
        return 'Hola, soy un agente'
    else:
        

        return 'POST recibido'


@app.route('/sumador')
def sumador():
    x = int(request.args['x'])
    y = int(request.args['y'])
    return str(x+y)


if __name__ == '__main__':
    app.run()
    
   

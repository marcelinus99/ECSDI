DistributedSolverOpen
=====================

Sistema distribuido para resolucion de problemas simples.

El sistema esta formado por:

  * Un servicio de directorio
  * Solver generico que recibe las peticiones y las distribuye
  * Solver para problemas ARITH
  * Solver para problemas MFREQ
  * Un logger de la actividad de los solvers genericos
  * Un cliente que manda peticiones a los solver genericos

El servicio de directorio hace de servicio de descubrimiento y es utilizado por los agentes cada vez que tienen que
asignar una tarea a otros agentes

 * DirectoryService.py

    Mantiene un registro de los agentes en el sistema

    Parametros
      --open = permite conexiones desde hosts remotos (no por defecto)
      --verbose = va escribiendo por terminal las peticiones que recibe el servidor http
      --port = port de comunicacion (9000 por defecto)
      --schedule = Algoritmo para el reparto de carga entre agentes
                  (equaljobs = todos los agentes registrados son asignados el mismo numero de veces,
                   random = los agentes registrados actualmente se asignan al azar
                   random por defecto)

    Entradas Web:
       /info = Registro de agentes

 * Client.py

    Cliente que lanza peticiones a los solver genericos

    Parametros:
      --open = permite conexiones desde hosts remotos (no por defecto)
      --verbose = va escribiendo por terminal las peticiones que recibe el servidor http
      --port = port de comunicacion (9001 por defecto)
      --dir = Direccion completa del servicio de directorio

    Entradas Web:
       /iface = Formulario para enviar problemas
       /info = Lista de problemas enviados

 * Solver.py

    Solver generico que hace de front-end al sistema de resolucion de problemas

    Parametros:
      --open = permite conexiones desde hosts remotos (no por defecto)
      --verbose = va escribiendo por terminal las peticiones que recibe el servidor http
      --port = port de comunicacion (9010 por defecto)
      --dir = Direccion completa del servicio de directorio


    Entradas Web:
       /info = Lista de problemas recibidos

 * Arithmetic.py

    Solver de problemas ARITH (evalua una expresion aritmetica)

    Parametros:
      --open = permite conexiones desde hosts remotos (no por defecto)
      --verbose = va escribiendo por terminal las peticiones que recibe el servidor http
      --port = port de comunicacion (9020 por defecto)
      --dir = Direccion completa del servicio de directorio

 * LetterCounter.py

    Solver de problemas MFREQ (calcula las 10 letras mas frecuentes de un texto)

    Parametros:
      --open = permite conexiones desde hosts remotos (no por defecto)
      --verbose = va escribiendo por terminal las peticiones que recibe el servidor http
      --port = port de comunicacion (9030 por defecto)
      --dir = Direccion completa del servicio de directorio

 * Logger.py

    Registra la actividad de los Solvers genericos

      --open = permite conexiones desde hosts remotos (no por defecto)
      --verbose = va escribiendo por terminal las peticiones que recibe el servidor http
      --port = port de comunicacion (9100 por defecto)
      --dir = Direccion completa del servicio de directorio

    Entradas Web:
       /info = Grafica de la actividad de los solvers

----------------------------

Ejecucion del sistema
=====================

Pasos:

 1- Iniciar un DirectoryService y abrir el navegador en la pagina /info del agente (pcera:9000/info)

  $ python DirectoryService.py --port 9000

 2- Iniciar un Logger y esperar a que se registre y abrir el navegador en la pagina /info del agente

  $ python Logger.py --port 9040 --dir http://pcera:9000
  $ python Logger.py --port 9040 --dir http://DESKTOP-5IGN934:9000

 3- Iniciar una o mas copias de Solver, Arithmetic y LetterCounter (los agentes Solver tambien tienen una pagina /info
     que se puede monitorizar)

  $ python Solver.py --port 9010 --dir http://pcera:9000
  $ python Solver.py --port 9010 --dir http://DESKTOP-5IGN934:9000

  $ python AllotjamentAgent.py --port 9020 --dir http://pcera:9000
  $ python AllotjamentAgent.py --port 9020 --dir http://DESKTOP-5IGN934:9000


  $ python TransportAgent.py --port 9030 --dir http://pcera:9000
  $ python TransportAgent.py --port 9030 --dir http://DESKTOP-5IGN934:9000

 4- Iniciar Client y abrir en el navegador las paginas /iface y /info

  $ python Client.py --port 9001 --dir http://pcera:9000
  $ python Client.py --port 9001 --dir http://DESKTOP-5IGN934:9000

 5- Ejecutar problemas desde la pagina /iface del cliente

Si se va a iniciar el sistema desde varias maquinas se han de ejecutar los agentes con el parametro --open



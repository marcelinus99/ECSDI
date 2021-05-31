## ECSDI QP 2020-21

### Práctica de Ingeniería del Conocimiento y Sistemas Inteligentes Distribuidos de la Facultad de Informática de Barcelona (FIB)

### Universidad Politécnica de Cataluña (UPC)

Alumnos:

* Carles Llongueras Aparicio
* Alexandre Fló Cuesta
* Marc González Moratona

TravelPack
=====================

Sistema distribuido para búsqueda de viajes.

El sistema esta formado por:

  * Un servicio de directorio
  * Solver que recibe las peticiones y las distribuye
  * Solver para problemas alojamiento
  * Solver para problemas transporte
  * Solver para problemas actividades

El servicio de directorio hace de servicio de descubrimiento y es utilizado por los agentes cada vez que tienen que
asignar una tarea a otros agentes

 * DirectoryService.py

    Mantiene un registro de los agentes en el sistema

    Parametros
      --open = permite conexiones desde hosts remotos (no por defecto)
      --verbose = va escribiendo por terminal las peticiones que recibe el servidor http
      --port = port de comunicacion (9000 por defecto)

    Entradas Web:
       /info = Registro de agentes

 * Solver.py

    Solver generico que hace de front-end al sistema de resolucion de problemas

    Parametros:
      --open = permite conexiones desde hosts remotos (no por defecto)
      --verbose = va escribiendo por terminal las peticiones que recibe el servidor http
      --port = port de comunicacion (9010 por defecto)
      --dir = Direccion completa del servicio de directorio


    Entradas Web:
       /iface = Formulario para enviar problemas
       /info = Lista de problemas enviados


----------------------------

Ejecucion del sistema
=====================

Pasos:

 1- Iniciar un DirectoryService y abrir el navegador en la pagina /info del agente (pcera:9000/info)

  $ python DirectoryService.py

 2- Iniciar una o mas copias de Solver (puerto 9001), Allotjament (puerto 9010), Activitats (puerto 9030) y Transport (puerto 9020) (los agentes Solver tambien tienen una pagina /info
     que se puede monitorizar)

  $ python Solver.py --dhost pcera
  $ python Solver.py --dhost http://DESKTOP-5IGN934:9000
  $ python Solver.py --dhost DESKTOP-53V8IFQ

  $ python AllotjamentAgent.py --dhost pcera
  $ python AllotjamentAgent.py --dhost http://DESKTOP-5IGN934:9000
  $ python AllotjamentAgent.py --dhost DESKTOP-53V8IFQ

  $ python TransportAgent.py --dhost pcera
  $ python TransportAgent.py --dhost http://DESKTOP-5IGN934:9000
  $ python TransportAgent.py --dhost DESKTOP-53V8IFQ

  $ python ActivitiesAgent.py --dhost pcera
  $ python ActivitiesAgent.py --dhost http://DESKTOP-5IGN934:9000
  $ python ActivitiesAgent.py --dhost DESKTOP-53V8IFQ



 3- Ejecutar problemas desde la pagina /iface del solver

Si se va a iniciar el sistema desde varias maquinas se han de ejecutar los agentes con el parametro --open



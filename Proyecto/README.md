# CONSEJOS Y PRACTICAS DESARROLLO
Todo lo que escribo aqui es basado en las librerias que se han incorporado y las buenas practicas para no confundir espacios de nombres.

1. Importar siempre todas las funciones de un fichero (from Util.fichero import *)
2. Los espacios de nombres **importante** hay que obtenerlos del fichero Util/Namespaces. Ahí dentro hay una funcion llamada **getNamespace(nombre)** que es bastante autoexplicatoria. **NUNCA** generar los espacios de nombres mediante strings, utilizad estas funciones. 
3. La libereria anterior retorna objetos del tipo namespace, que no son **URIS** Para convertir-las en URIS, hay que utilizar el punto (ns.sujeto) o el operador de índice (ns['sujeto'])
4. Cuando se quiere obtener el tipo de un agente, utilizad **getNamespace(nombre agente).type** Esto es lo que las funciones de search (all,one,specific) aceptan UNICAMENTE.
5. No hagais push de los ficheros .turtle En principio ya estan en el .gitignore
6. Respetad los nombres de las ontologias al maximo posible para los objetos del dominio. Esto sera util para no tener que corregir errores de nombres.


Instrucciones para poner vuestros agentes en marcha:

1. ejecutad python DirectorioAgentes.py en una consola. Esto inicia el directorio. Podeis consultar la informacion de este normalemente en http://localhost:9000/Info
2. Hardcodead la direccion del directorio en vuestros ficheros agente. Teneis un ejemplo en AgenteVendedorExterno
3. Cuando se inicia un agente, enviad un mensaje de registro al directorio. Esto se hace mediante la libreria **Directorio** con la funcion register_message
4. Utilizad las funciones de la libreria **Directorio** que envian mensajes automaticamente. No os teneis que preocupar sobre como enviar el mensaje, solo de generar los parametros necesarios para la comunicacion
5. El debug=True hace que el fichero se **recargue** en consola cada vez que lo editeis. Pero si recargais el **DirectorioAgentes.py** el grafo se pierde y por lo tanto tendreis que registrar todos los agentes de nuevo. Recargar un agente

# -*- coding: utf-8 -*-

"""
LibreDTE
Copyright (C) SASCO SpA (https://sasco.cl)

Este programa es software libre: usted puede redistribuirlo y/o modificarlo bajo
los términos de la Licencia Pública General Affero de GNU publicada por la
Fundación para el Software Libre, ya sea la versión 3 de la Licencia, o (a su
elección) cualquier versión posterior de la misma.

Este programa se distribuye con la esperanza de que sea útil, pero SIN GARANTÍA
ALGUNA; ni siquiera la garantía implícita MERCANTIL o de APTITUD PARA UN
PROPÓSITO DETERMINADO. Consulte los detalles de la Licencia Pública General
Affero de GNU para obtener una información más detallada.

Debería haber recibido una copia de la Licencia Pública General Affero de GNU
junto a este programa.
En caso contrario, consulte <http://www.gnu.org/licenses/agpl.html>.
"""

"""
Comando para monitorear un directorio por archivos con cierto formato e ir creando
los DTE asociados y sus PDF
@author Esteban De La Fuente Rubio, DeLaF (esteban[at]sasco.cl)
@version 2018-01-19
"""

# módulos usados
import os, os.path
import time
import shutil
import subprocess
from json import dumps as json_encode

# opciones en formato largo
long_options = ['emisor=', 'formato=', 'encoding=', 'dir_entrada=', 'dir_salida=', 'normalizar=', 'papel=', 'email', 'imprimir']

# función principal del comando
def main(Cliente, args, config) :
    emisor, formato, encoding, dir_entrada, dir_salida, normalizar, papel, email, imprimir = parseArgs(args)
    if emisor == None :
        print('Debe especificar el emisor que creará los documentos')
        return 1
    if not dir_entrada or not os.path.exists(dir_entrada) :
        print('Debe especificar un directorio de entrada válido para los archivos a generar')
        return 1
    if not dir_salida :
        print('Debe especificar un directorio de salida para los archivos a generar')
        return 1
    # crear directorio para archivos si no existen
    if not os.path.exists(dir_salida) :
        os.makedirs(dir_salida)
    # directorio del comando principal
    cmd_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    # comando de python según OS
    if os.name == 'posix':
        libredte_exec = "python3"
    elif os.name == 'nt' :
        libredte_exec = "python.exe"
    libredte_exec += " "+cmd_dir+"/libredte-cliente.py"
    # lanzar monitor en el directorio
    print('Iniciando monitor en el directorio:', dir_entrada)
    print('Para finalizar el monitoreo utilizar Ctrl+C')
    try :
        while True :
            files = os.scandir(dir_entrada)
            for f in files :
                if not f.is_dir() :
                    # crear directorio y mover archivo de entrada al directorio que corresponde
                    dir_dte = os.path.abspath(dir_salida)+'/'+f.name
                    print('Procesando archivo:', f.name, end='... ')
                    if os.path.exists(dir_dte) :
                        shutil.rmtree(dir_dte)
                    os.makedirs(dir_dte)
                    archivo_solicitud = dir_dte+'/solicitud_'+f.name
                    while True :
                        try :
                            os.rename(f.path, archivo_solicitud)
                            break
                        except PermissionError :
                            time.sleep(1)
                    # generar DTE
                    cmd = libredte_exec+" dte_generar --url="+config["auth"]["url"]+" --hash="+config["auth"]["hash"]
                    if formato in ('json', 'xml') :
                        cmd += " --"+formato+"="+archivo_solicitud
                    else :
                        cmd += " --archivo="+archivo_solicitud+" --formato="+formato
                    cmd += " --encoding="+encoding
                    cmd += " --dir="+dir_dte
                    cmd += " --normalizar="+str(normalizar)
                    if papel :
                        cmd += " --papel="+str(papel)
                    if email :
                        cmd += " --email"
                    try :
                        subprocess.check_output(cmd.split(" "))
                        print("[Ok]")
                    except subprocess.CalledProcessError as e :
                        print("[Mal]")
                        with open(dir_dte+'/dte_generar.log', 'w') as f :
                            f.write(e.output.decode('utf-8'))
                    # imprimir el DTE
                    if imprimir :
                        cmd = libredte_exec+" imprimir --pdf="+dir_dte+"/emitido.pdf"
                        try :
                            subprocess.check_output(cmd.split(" "))
                            print("  Se ha enviado a imprimir el DTE")
                        except subprocess.CalledProcessError as e :
                            print("No fue posible enviar a imprimir el DTE")
                            with open(dir_dte+'/dte_generar.log', 'w') as f :
                                f.write(e.output.decode('utf-8'))
            time.sleep(1)
    except KeyboardInterrupt :
        print()
        return 0

# función que procesa los argumentos del comando
def parseArgs(args) :
    emisor = None
    formato = 'json'
    encoding = 'UTF-8'
    dir_entrada = ''
    dir_salida = ''
    normalizar = 1
    papel = 0
    email = 0
    imprimir = 0
    for var, val in args:
        if var == '--emisor' :
            emisor = val
        elif var == '--formato' :
            formato = val
        elif var == '--encoding' :
            encoding = val
        elif var == '--dir_entrada' :
            dir_entrada = val
        elif var == '--dir_salida' :
            dir_salida = val
        elif var == '--normalizar' :
            normalizar = val
        elif var == '--papel' :
            papel = val
        elif var == '--email' :
            email = 1
        elif var == '--imprimir' :
            imprimir = 1
    return emisor, formato, encoding, dir_entrada, dir_salida, normalizar, papel, email, imprimir

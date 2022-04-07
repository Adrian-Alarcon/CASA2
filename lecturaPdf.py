import slate3k #La libreria para sacar la capa texto.
import re
import openpyxl
import os
import time
import rutas #importacion de modulo donde defino las rutas.



# Limpiar y unir los datos que vienen el tuplas.
def limpiar_grupos(lista_medicacion, lista_cantidades):
    """LA FUNCION SE ENCARGA DE LIMPIAR Y ARMAR LAS LISTAS FINALES DE CANTIDADES
    Y DE CADA POSICION DE MATERIAL"""
    lista = []
    lista_final_cantidades = []
    lista_codigo_troquel = []

    
    # DESARMAR TUPLAS Y ARMAR LISTAS PARA PODER MODIFICARLAS Y LIMPIAR LOS ESPACIOS EN BLANCO.
    k = 1
    for grupo in lista_medicacion:
        palabras = []
        if k < len(lista_medicacion):
            for elem in grupo:
                if elem != "" and elem != "Productos " and elem != "Observ: ":
                    palabras.append(elem.rstrip())
            lista.append(palabras)
            # print(palabras)
            
        k = k + 1

    # MANIPULAR LA LISTA DE LAS CANTIDADES EXTRAIDAS CON REGEX
    pos_cant = len(lista) #cantidad de posiciones de cantidad que deberia haber
    inicio = len(lista_cantidades) - pos_cant #para controlar el slicing
    if len(lista_cantidades) - inicio < len(lista):
        print("----------- ¡¡ALERTA!! -------------")
        print("\tLA CANTIDAD DE POSICIONES NO COINCIDE CON LA CANTIDAD DE POSICIONES DE CANTIDAD")
        return #termino la funcion si esto se cumple
    else:
        lista_final_cantidades = lista_cantidades[inicio:] # lista ordenada de cantidades por posicion
        lista_cantidades.clear()



    # EXTRAER CODIGO DE TROQUEL SI EXISTIESE Y MOSTRAR RESULTADO FINAL
    for t in range(len(lista)):
        codigo_troquel = lista[t][0]
        try:
            lista_codigo_troquel.append(int(codigo_troquel))
            lista[t].pop(lista[t].index(codigo_troquel))
        except:
            lista_codigo_troquel.append(999999)
        finally:
            print(f"MEDICACION: {' '.join(lista[t])} | CANTIDAD: {lista_final_cantidades[t]} | CODIGO TROQUEL: {lista_codigo_troquel[t]}")

    return lista, lista_final_cantidades, lista_codigo_troquel


# Funcion que limpia los caracteres "\n" del texto del pdf:
def limpiar_caracteres(texto_lista):
    if texto_lista != []:
        lista = texto_lista.split("\n")
        nueva_lista = [x for x in lista if x != '']
        return " ".join(nueva_lista)
    else:
        return False


# Pegar datos a Excel
def excel(ruta_excel, afiliado, medicacion_lista, cantidades, cod_troquel, pedido_externo):
    global fila
    print(f"\t\t# INTENTANDO ACCEDER AL EXCEL...")
    excel = openpyxl.load_workbook(ruta_excel)
    hoja = excel["inicio"]
    
    codigo_afiliado = afiliado[0][0] + afiliado[0][1]
    ultima_fila = len(hoja["B"])

    try:
        print(f"\t\t> Se accedio correctamente.")
        for i in range(len(medicacion_lista)):
            hoja[f"A{fila}"].value = " ".join(medicacion_lista[i])
            hoja[f"B{fila}"].value = codigo_afiliado.rstrip()
            hoja[f"C{fila}"].value = cod_troquel[i]
            hoja[f"D{fila}"].value = " ".join(cantidades[i])
            hoja[f"E{fila}"].value = pedido_externo
            fila += 1


    except Exception as e:
        print(f"Ha ocurrido una excepcion. Posiblemente hay un error con el EXCEL. {e}")
    # Guardamos y cerramos el excel.
    finally:
        excel.save(ruta_excel)
        excel.close()


# Leer pdf y sacar medicacion
def leer_pdf(ruta_pdfs):

    # -- VARIABLES - LISTAS -- #
    juego_tuplas_medicamentos = []
    lista_afiliado = []
    cantidades = []
    pedidos_ext = []
    

    # Usamos la libreria Slate3k para extraer el texto del pdf.
    with open(ruta_pdfs, "rb") as archivo:
        print(f"\t\t> Leyendo capa texto del pdf...")
        lectura = slate3k.PDF(archivo)  # Se devuelve el texto como un string dentro de una lista.  
    
    nuevo_texto = limpiar_caracteres(lectura[0])
    # print(nuevo_texto)
    
    # == EXPRESIONES REGULARES == #
    regex_codigo_medicacion = r'(Productos\s)([0-9]*\s*)([A-Z]*\s*)([a-zA-Z0-9./+]*\s*)([(a-zA-Z0-9/+).+]*\s*)([(a-z0-9/+).+]*\s*)([a-z0-9./+ ]*)|(Observ:\s)([0-9]*\s*)([A-Z]*\s*)([a-zA-Z0-9.]*\s*)([(a-zA-Z).+]*\s*)([(a-zA-z0-9).+]*\s*)([a-z0-9 +.]*)'
    regex_afiliado = r'([0-9]{5,13})([\/]\d{1,2}\s)([A-Z, ]+)'
    regex_cantidades = r'(\s[0-9]{1,2})'
    regex_ped_ext = r'(Nro.:\s)([0-9]{2,9})'
    try:
        # AFILIADO
        for a in re.findall(regex_afiliado, nuevo_texto):
            lista_afiliado.append(a)

        # MEDICACION
        for m in re.findall(regex_codigo_medicacion, nuevo_texto):
            juego_tuplas_medicamentos.append(m)
        
        for c in re.findall(regex_cantidades, nuevo_texto):
            cantidades.append(c)

        # PED EXT
        for p in re.findall(regex_ped_ext, nuevo_texto):
            pedidos_ext.append(p)

    except Exception as e:
        return False, False
    
    # Validamos afiliado y medicacion.
    if lista_afiliado != []:
        return lista_afiliado, juego_tuplas_medicamentos, cantidades, pedidos_ext[0][1]
    else:
        return False, False



# --- ARRANQUE DEL PROCESO PRINCIPAL --- #
fila = 9
def lectorPdf():
    try:
        # Se recorre la carpeta de los pdf y se envia la lectura.
        print(">>> Ingresando a la carpeta de PDFS.")
        for pdf in os.listdir(rutas.carpeta_pdfs):
            print("---------------------------------------------------")
            print("\tListando PDF:")
            if pdf.endswith(".pdf"):
                print(f"\t\t* {pdf}")
                lista_afiliado, lista_tuplas_medicacion, tupla_cantidades, pedido_externo = leer_pdf(os.path.join(rutas.carpeta_pdfs, pdf))
                
                if lista_afiliado != False and lista_tuplas_medicacion != False:
                    lista_materiales, lista_cantidades, lista_codigos_troquel = limpiar_grupos(lista_tuplas_medicacion, tupla_cantidades)
                    excel(rutas.archivo_excel, lista_afiliado, lista_materiales, lista_cantidades, lista_codigos_troquel, pedido_externo)
                else:
                    print(f"\t\t No se pudo encontrar medicacion para el PDF {pdf}")
        return True
    except Exception as e:
        print("***** Nada que listar en la carpeta de PDFS! *****")
        print(e)
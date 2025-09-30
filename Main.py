import requests
from bs4 import BeautifulSoup
import sys
import re # Para limpiar el texto extraído

def consultar_placa_ecuador(placa):
    """
    Intenta automatizar la consulta de información vehicular básica (gratuita)
    en el portal 'https://tramites.ecuadorlegalonline.com/sri/consultar-dueno-de-carro/'

    Argumentos:
        placa (str): El número de placa del vehículo (ej: 'ABC1234').
    """
    
    # URL de destino de la petición POST. Se asume que es la misma página.
    URL = 'https://tramites.ecuadorlegalonline.com/sri/consultar-dueno-de-carro/'

    # 1. Definición de Headers
    # Simula un navegador móvil (común en Termux) para evitar bloqueos.
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Termux) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36',
        'Referer': URL,
        # Importante: Content-Type indica el formato de los datos que se envían.
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    # 2. Definición del Payload (Datos a enviar)
    # >>> ATENCIÓN: AJUSTAR ESTOS NOMBRES SI EL SCRIPT NO FUNCIONA <<<
    # Deben coincidir con los campos 'name' del formulario HTML de la web.
    payload = {
        'placa': placa.upper(),       # <--- AJUSTAR AQUÍ (Nombre del campo de texto de la placa)
        'btn_consultar': 'Consultar'  # <--- AJUSTAR AQUÍ (Nombre del botón de consulta)
    }

    print(f"\n[🔍] Consultando información pública para la placa: {placa.upper()}...")
    print("-" * 50)
    
    try:
        # Enviar la petición POST con los datos del formulario
        response = requests.post(URL, data=payload, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"[❌] Error de conexión. Código HTTP: {response.status_code}")
            return

        # 3. Procesar la respuesta HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 4. Lógica de Extracción (Scraping)
        # >>> ATENCIÓN: AJUSTAR ESTAS CLASES/IDs SI EL SCRIPT NO FUNCIONA <<<
        
        # Buscar el contenedor principal que tiene la información de resultados
        # Se busca un <div> que contenga la información vehicular
        contenedor_info = soup.find('div', class_='resultado-consulta') # <--- AJUSTAR AQUÍ (Clase o ID del contenedor)

        if not contenedor_info:
            # Si no se encuentra el contenedor, puede que la placa no exista o el scraping esté roto.
            print("[⚠️] No se pudo encontrar el bloque de resultados.")
            print("Posibles causas: Placa no registrada, o la estructura HTML ha cambiado.")
            return

        # --- Extracción de Campos Específicos ---
        
        datos_encontrados = {}
        
        # Estos sitios a menudo usan etiquetas <strong>, <b> o <span> para etiquetar datos.
        # Buscaremos todos los pares de etiquetas dentro del contenedor
        
        # Ejemplo de extracción para Marca, Modelo, Color, etc. (Puede variar)
        campos = contenedor_info.find_all(['b', 'strong', 'span']) 

        for i in range(0, len(campos) - 1, 2):
            etiqueta = campos[i].text.strip().replace(':', '')
            valor = campos[i+1].text.strip()
            
            # Limpiar el valor de posibles saltos de línea y espacios excesivos
            valor = re.sub(r'\s+', ' ', valor)
            
            # Solo guardamos si la etiqueta es relevante y el valor no es vacío
            if etiqueta and valor and etiqueta not in ['Nombre', 'Cédula', 'Email']: # Excluir datos privados
                datos_encontrados[etiqueta] = valor

        # 5. Mostrar Resultados
        
        if datos_encontrados:
            print("[✅] Información de la Placa Obtenida:")
            for key, value in datos_encontrados.items():
                print(f"  {key:<20}: {value}")
        else:
            print("[⚠️] El contenedor se encontró, pero no se extrajo información útil.")
            
    except requests.exceptions.RequestException as e:
        print(f"[❌] Error en la solicitud de red: {e}")
    except Exception as e:
        print(f"[❌] Error inesperado durante el procesamiento: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python placa_ec_completo.py [NUMERO_DE_PLACA]")
        print("Ejemplo: python placa_ec_completo.py PBR1234")
        sys.exit(1)
    
    placa_a_consultar = sys.argv[1]
    consultar_placa_ecuador(placa_a_consultar)

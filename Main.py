import requests
from bs4 import BeautifulSoup
import sys

def consultar_placa_ecuador(placa):
    """
    Intenta automatizar la consulta de información vehicular básica y gratuita 
    en la web ecuadorlegalonline.com.

    Argumentos:
        placa (str): El número de placa del vehículo (ej: 'ABC1234').
    """
    # URL de la página que contiene el formulario de consulta. 
    # A menudo, la URL de envío es la misma o una subpágina.
    URL = 'https://tramites.ecuadorlegalonline.com/sri/consultar-dueno-de-carro/'
    
    # 1. Definición de Headers y Payload (los datos a enviar)
    # Los headers simulan un navegador real.
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Termux) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36',
        'Referer': URL,
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    # El 'payload' o 'data' debe coincidir con los campos del formulario de la web.
    # Los nombres de los campos ('placa', 'btn_consultar') son una suposición y podrían variar.
    payload = {
        'placa': placa,
        'btn_consultar': 'Consultar' # Nombre del botón si lo hay
    }

    print(f"\n[🔍] Consultando información pública para la placa: {placa}...")
    
    try:
        # 2. Enviar la petición POST al servidor
        response = requests.post(URL, data=payload, headers=headers, timeout=10)
        
        # 3. Verificar si la consulta fue exitosa
        if response.status_code != 200:
            print(f"[❌] Error al conectar. Código de estado HTTP: {response.status_code}")
            return

        # 4. Procesar la respuesta HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # --- Lógica de Extracción (Web Scraping) ---
        # ATENCIÓN: Esta parte es la más inestable. Debes inspeccionar el código
        # HTML de la página de resultados para encontrar la clase o ID correcta
        # donde se muestran los datos (Marca, Modelo, Año, etc.).

        # Intentaremos buscar un elemento común que contenga el resultado (ej: una tabla o div de resultados)
        
        # Aquí se asume que los datos están en una tabla o lista de detalles.
        # EJEMPLO DE EXTRACCIÓN (ajusta estas etiquetas a lo que veas en el HTML real):
        
        # Buscar la tabla de detalles del vehículo (si existe un ID o clase específica)
        info_gratuita = soup.find('div', class_='resultado_vehiculo') 
        
        if info_gratuita:
            print("\n[✅] Información Vehicular Básica (Gratuita):")
            
            # Intenta imprimir el texto dentro del div de resultados
            # Esto puede necesitar refinamiento para extraer datos específicos (Marca, Modelo)
            print("---------------------------------------------")
            
            # --- Intento de extracción detallada (ejemplo teórico) ---
            
            # Simular la búsqueda de la marca
            marca_tag = info_gratuita.find('span', string='Marca:')
            marca = marca_tag.find_next_sibling('span').text if marca_tag and marca_tag.find_next_sibling('span') else "No encontrada"

            # Simular la búsqueda del modelo
            modelo_tag = info_gratuita.find('span', string='Modelo:')
            modelo = modelo_tag.find_next_sibling('span').text if modelo_tag and modelo_tag.find_next_sibling('span') else "No encontrado"
            
            # Simular la búsqueda del año
            anio_tag = info_gratuita.find('span', string='Año:')
            anio = anio_tag.find_next_sibling('span').text if anio_tag and anio_tag.find_next_sibling('span') else "No encontrado"
            
            print(f"  Placa: {placa}")
            print(f"  Marca: {marca}")
            print(f"  Modelo: {modelo}")
            print(f"  Año:   {anio}")
            
            print("\n[⚠️] Recordatorio: Los datos sensibles (nombre, cédula) están ocultos o son de pago.")
            
        else:
            # Si no encuentra el div de resultados, puede que la placa no exista o la estructura HTML haya cambiado.
            print("[🧐] No se pudo encontrar el bloque de resultados. La placa no existe o el código HTML de la web ha cambiado.")
            
    except requests.exceptions.RequestException as e:
        print(f"[❌] Ocurrió un error en la solicitud: {e}")
    except Exception as e:
        print(f"[❌] Ocurrió un error en el procesamiento: {e}")

if __name__ == '__main__':
    # Verifica que se haya pasado la placa como argumento
    if len(sys.argv) < 2:
        print("Uso: python placa_ec.py [NUMERO_DE_PLACA]")
        print("Ejemplo: python placa_ec.py ABC1234")
        sys.exit(1)
    
    placa_a_consultar = sys.argv[1]
    consultar_placa_ecuador(placa_a_consultar)

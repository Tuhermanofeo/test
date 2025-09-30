import sys
import re

def analizar_telefono_ecuador(numero):
    """
    Analiza un número de teléfono celular ecuatoriano (09XXXXXX) para verificar 
    su formato y determinar la operadora original por prefijo (antes de la portabilidad).
    """
    print(f"\n[🔍] Analizando número: {numero}")
    print("-" * 50)
    
    # Limpiar el número de espacios, guiones y otros caracteres no numéricos
    numero_limpio = re.sub(r'[\s\-\+\(\)]', '', numero)
    
    # 1. Validar la estructura básica del celular ecuatoriano (9 o 10 dígitos, debe empezar por 09)
    patron_celular = r'^(09|5939)\d{8}$'
    
    if not re.match(patron_celular, numero_limpio):
        print(f"[❌] Error de formato: '{numero}' no parece ser un celular válido de Ecuador.")
        print("   Debe tener 10 dígitos y comenzar con 09 (ej: 0991234567).")
        return

    # Normalizar a 10 dígitos, empezando con 0
    if numero_limpio.startswith('593'):
        numero_normalizado = '0' + numero_limpio[3:]
    else:
        numero_normalizado = numero_limpio
        
    prefijo = numero_normalizado[2:4] # Extrae los dos dígitos después del '09'
    
    # 2. Determinar operadora original por prefijo (antes de la portabilidad numérica)
    operadoras = {
        '98': 'Movistar (Original)',
        '99': 'Claro (Original)',
        '97': 'Claro (Original)',
        '96': 'CNT (Original)',
        '95': 'Tuenti/Movistar (Original)',
        '93': 'CNT (Original)'
        # 99, 98 y 97 eran los prefijos más grandes y se dividieron en el tiempo
    }
    
    operadora_original = operadoras.get(prefijo, 'Operadora Indefinida o Portado')

    # 3. Mostrar la información básica
    print("[✅] Análisis de Formato Completado:")
    print(f"  Número Normalizado: {numero_normalizado}")
    print(f"  Prefijo del Número: 09{prefijo}...")
    print(f"  Operadora Original: {operadora_original}")
    print("\n[⚠️] La portabilidad numérica puede haber cambiado la operadora actual.")
    print("   No se puede obtener el nombre del dueño por medios públicos.")
    
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python telefono_info.py [NUMERO_DE_CELULAR]")
        print("Ejemplo: python telefono_info.py 0991234567")
        sys.exit(1)
    
    numero_a_consultar = sys.argv[1]
    analizar_telefono_ecuador(numero_a_consultar)

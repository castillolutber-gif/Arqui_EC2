"""
Explorador de representación de datos  (Proyecto 11 - Arquitectura de Computadoras)

Muestra cómo se representan valores en registros y memoria:
  - Enteros sin signo de 8 bits (0 a 255)
  - Enteros con signo de 8 bits en complemento a dos (-128 a 127)
  - Palabras de 16 bits (0 a 65535) con orden Big-Endian / Little-Endian

Uso:
    python explorador.py            -> menú interactivo
    python explorador.py pruebas    -> ejecuta los casos de prueba del proyecto

Solo usa la biblioteca estándar de Python 3.8 o superior.
El código está dividido en secciones que corresponden a los módulos
del diseño (Tabla 5 del informe).
"""

import sys

# ======================================================================
# MÓDULO 2: VALIDACIÓN Y SELECCIÓN DEL FORMATO
# ======================================================================

# formato: (mínimo, máximo, ancho en bits, descripción)
FORMATOS = {
    "u8":  (0,    255,   8,  "Entero sin signo de 8 bits"),
    "s8":  (-128, 127,   8,  "Entero con signo de 8 bits (complemento a dos)"),
    "u16": (0,    65535, 16, "Palabra de 16 bits sin signo"),
}


class ErrorEntrada(Exception):
    """La entrada no es un número válido."""


class ErrorRango(Exception):
    """El número es válido pero no cabe en el formato elegido."""


def validar_rango(valor, formato):
    """Rechaza el valor si está fuera del rango (NO trunca bits)."""
    minimo, maximo, _, _ = FORMATOS[formato]
    if valor < minimo or valor > maximo:
        raise ErrorRango(
            f"Error de rango: {valor} no cabe en {formato}. "
            f"El rango permitido es {minimo} a {maximo}."
        )


# ======================================================================
# MÓDULO 1: INGRESO DE DATOS
# ======================================================================

def parsear_entrada(texto):
    """Convierte el texto del usuario a entero. Acepta decimal o 0x... (hex)."""
    texto = texto.strip().lower()
    try:
        if texto.startswith("0x"):
            return int(texto, 16)
        return int(texto)
    except ValueError:
        raise ErrorEntrada(f"Error de entrada: '{texto}' no es un número válido.")


# ======================================================================
# MÓDULO 3: CONVERSIÓN Y REPRESENTACIÓN
# ======================================================================

def a_patron(valor, bits):
    """Valor decimal -> patrón de bits (entero sin signo de 'bits' bits).
    Para negativos aplica complemento a dos: patrón = 2^n + valor."""
    if valor >= 0:
        return valor
    return (1 << bits) + valor


def a_binario(patron, bits):
    """Patrón -> cadena binaria por divisiones sucesivas entre 2."""
    cadena = ""
    for _ in range(bits):
        cadena = str(patron % 2) + cadena
        patron //= 2
    return cadena


def a_hexadecimal(binario):
    """Cadena binaria -> hexadecimal agrupando de 4 en 4 bits (nibbles)."""
    digitos = "0123456789ABCDEF"
    resultado = ""
    for i in range(0, len(binario), 4):
        nibble = int(binario[i:i + 4], 2)
        resultado += digitos[nibble]
    return "0x" + resultado


def hex_a_binario(texto_hex):
    """Hexadecimal -> binario (conversión inversa, dígito a dígito)."""
    digitos = "0123456789ABCDEF"
    cuerpo = texto_hex.upper().replace("0X", "")
    return "".join(a_binario(digitos.index(d), 4) for d in cuerpo)


def interpretar_8bits(patron):
    """Un MISMO patrón de 8 bits leído de dos formas distintas."""
    sin_signo = patron
    con_signo = patron - 256 if patron >= 128 else patron
    return sin_signo, con_signo


def procesar(valor, formato):
    """Valida y convierte. Devuelve un diccionario con todas las representaciones."""
    validar_rango(valor, formato)
    _, _, bits, _ = FORMATOS[formato]
    patron = a_patron(valor, bits)
    binario = a_binario(patron, bits)
    resultado = {
        "valor": valor,
        "formato": formato,
        "bits": bits,
        "patron": patron,
        "binario": binario,
        "hex": a_hexadecimal(binario),
    }
    if bits == 8:
        resultado["como_sin_signo"], resultado["como_con_signo"] = interpretar_8bits(patron)
    return resultado


# ======================================================================
# MÓDULO 4: ORGANIZACIÓN DE BYTES EN MEMORIA (memoria simulada)
# ======================================================================

class MemoriaSimulada:
    """Memoria direccionable por bytes (cada dirección guarda 8 bits)."""

    def __init__(self, tamano=16):
        self.celdas = bytearray(tamano)

    def escribir_palabra16(self, direccion, patron, orden):
        """Guarda una palabra de 16 bits en dos direcciones consecutivas."""
        msb = (patron >> 8) & 0xFF   # byte alto
        lsb = patron & 0xFF          # byte bajo
        if orden == "big":
            self.celdas[direccion] = msb
            self.celdas[direccion + 1] = lsb
        else:  # little
            self.celdas[direccion] = lsb
            self.celdas[direccion + 1] = msb

    def leer_palabra16(self, direccion, orden):
        """Reconstruye la palabra de 16 bits leyendo con el orden indicado."""
        a = self.celdas[direccion]
        b = self.celdas[direccion + 1]
        if orden == "big":
            return (a << 8) | b
        return (b << 8) | a


# ======================================================================
# ALU: SUMA MODULAR DE 8 BITS (apoya el análisis de desbordamiento)
# ======================================================================

def sumar8(a, b):
    """Suma de dos patrones de 8 bits. Devuelve (resultado, acarreo, desbordamiento).
    Opera módulo 256: el bit 9 se descarta y se guarda en la bandera de acarreo."""
    total = a + b
    resultado = total & 0xFF
    acarreo = total > 0xFF
    # desbordamiento con signo: mismo signo en los operandos, signo distinto en el resultado
    desbordamiento = ((a ^ resultado) & (b ^ resultado) & 0x80) != 0
    return resultado, acarreo, desbordamiento


# ======================================================================
# MÓDULO 5: PRESENTACIÓN DE RESULTADOS
# ======================================================================

def mostrar_resultado(r):
    _, _, _, descripcion = FORMATOS[r["formato"]]
    print(f"\nFormato:         {descripcion}")
    print(f"Valor ingresado: {r['valor']}")
    print(f"Binario:         {r['binario']}")
    print(f"Hexadecimal:     {r['hex']}")
    if r["bits"] == 8:
        print(f"Leído sin signo: {r['como_sin_signo']}")
        print(f"Leído con signo: {r['como_con_signo']}")


def volcado_memoria(patron, direccion_base=0x0000):
    """Imprime el volcado de memoria de una palabra en ambos órdenes."""
    mem_big, mem_little = MemoriaSimulada(), MemoriaSimulada()
    mem_big.escribir_palabra16(direccion_base, patron, "big")
    mem_little.escribir_palabra16(direccion_base, patron, "little")

    print(f"\nVolcado de memoria de la palabra 0x{patron:04X} ({patron} decimal)")
    print(f"{'Dirección':<12}{'Big-Endian':<26}{'Little-Endian':<26}")
    for i in range(2):
        d = direccion_base + i
        b, l = mem_big.celdas[d], mem_little.celdas[d]
        print(f"0x{d:04X}      "
              f"0x{b:02X} ({a_binario(b, 8)})   "
              f"0x{l:02X} ({a_binario(l, 8)})")

    # lectura con el orden equivocado
    mal = mem_little.leer_palabra16(direccion_base, "big")
    print(f"\nSi se escribe en Little-Endian y se lee como Big-Endian: "
          f"0x{mal:04X} ({mal} decimal)")


# ======================================================================
# PRUEBAS (casos definidos en el alcance del proyecto)
# ======================================================================

def ejecutar_pruebas():
    casos = [
        # (descripción, valor, formato, binario esperado o None si debe rechazarse, hex esperado)
        ("0 como sin signo",        0,    "u8", "00000000", "0x00"),
        ("255 como sin signo",      255,  "u8", "11111111", "0xFF"),
        ("-128 con signo",          -128, "s8", "10000000", "0x80"),
        ("127 con signo",           127,  "s8", "01111111", "0x7F"),
        ("256 sin signo (rechazo)", 256,  "u8", None, None),
        ("-129 con signo (rechazo)", -129, "s8", None, None),
    ]
    print("=== PRUEBAS DE CONVERSIÓN Y RANGO ===")
    print(f"{'Caso':<28}{'Esperado':<22}{'Observado':<22}{'Resultado'}")
    for desc, valor, fmt, bin_esp, hex_esp in casos:
        esperado = "ErrorRango" if bin_esp is None else f"{bin_esp} {hex_esp}"
        try:
            r = procesar(valor, fmt)
            observado = f"{r['binario']} {r['hex']}"
        except ErrorRango:
            observado = "ErrorRango"
        print(f"{desc:<28}{esperado:<22}{observado:<22}{'OK' if esperado == observado else 'FALLA'}")

    print("\n=== PRUEBA DE ENDIANIDAD: palabra 0x1234 ===")
    for orden, esperado in (("big", [0x12, 0x34]), ("little", [0x34, 0x12])):
        mem = MemoriaSimulada()
        mem.escribir_palabra16(0, 0x1234, orden)
        observado = [mem.celdas[0], mem.celdas[1]]
        print(f"{orden:<7} esperado={[hex(x) for x in esperado]} "
              f"observado={[hex(x) for x in observado]} "
              f"{'OK' if observado == esperado else 'FALLA'}")
    volcado_memoria(0x1234)

    print("\n=== PRUEBA DE SUMA MODULAR (8 bits) ===")
    for a, b in ((255, 1), (127, 1)):
        res, c, v = sumar8(a, b)
        print(f"{a:>3} + {b} = {a_binario(res, 8)} ({res} sin signo / "
              f"{interpretar_8bits(res)[1]} con signo)  acarreo={int(c)}  desbordamiento={int(v)}")


# ======================================================================
# MÓDULO 1 (control): MENÚ INTERACTIVO
# ======================================================================

def pedir_valor(formato):
    texto = input("Valor (decimal o 0x...): ")
    valor = parsear_entrada(texto)
    return procesar(valor, formato)


def menu():
    print("=== Explorador de representación de datos ===")
    while True:
        print("\n1) Entero sin signo de 8 bits")
        print("2) Entero con signo de 8 bits (complemento a dos)")
        print("3) Palabra de 16 bits + memoria (Big/Little-Endian)")
        print("4) Suma modular de 8 bits")
        print("5) Ejecutar pruebas del proyecto")
        print("0) Salir")
        opcion = input("Opción: ").strip()
        try:
            if opcion == "1":
                mostrar_resultado(pedir_valor("u8"))
            elif opcion == "2":
                mostrar_resultado(pedir_valor("s8"))
            elif opcion == "3":
                r = pedir_valor("u16")
                mostrar_resultado(r)
                volcado_memoria(r["patron"])
            elif opcion == "4":
                a = parsear_entrada(input("Primer valor (-128 a 255): "))
                b = parsear_entrada(input("Segundo valor (-128 a 255): "))
                for x in (a, b):
                    if x < -128 or x > 255:
                        raise ErrorRango(f"Error de rango: {x} no cabe en 8 bits.")
                pa, pb = a_patron(a, 8), a_patron(b, 8)
                res, c, v = sumar8(pa, pb)
                print(f"\n{a_binario(pa, 8)} + {a_binario(pb, 8)} = {a_binario(res, 8)}")
                print(f"Resultado: {res} sin signo / {interpretar_8bits(res)[1]} con signo")
                print(f"Acarreo (C) = {int(c)}   Desbordamiento con signo (V) = {int(v)}")
            elif opcion == "5":
                ejecutar_pruebas()
            elif opcion == "0":
                print("Fin del programa.")
                break
            else:
                print("Opción no válida.")
        except (ErrorEntrada, ErrorRango) as e:
            print(e)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "pruebas":
        ejecutar_pruebas()
    else:
        menu()

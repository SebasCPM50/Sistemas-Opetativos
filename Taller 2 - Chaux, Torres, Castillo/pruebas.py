"""
Pruebas simples del cruce. Usa las mismas funciones de banquero_trafico.py
(no repite nada, solo las llama y verifica que el resultado sea correcto).
"""

import threading
import time
from banquero_trafico import pedir_paso, liberar_paso, EJE

resultados = []          # aqui guardamos (nombre, movimiento, t_entra, t_sale)
lock_resultados = threading.Lock()


def carro_prueba(nombre, movimiento, retraso=0.0):
    if retraso:
        time.sleep(retraso)
    pedir_paso(movimiento)
    t_entra = time.time()
    time.sleep(0.4)             # tiempo fijo cruzando, para que las pruebas sean estables
    liberar_paso()
    t_sale = time.time()
    with lock_resultados:
        resultados.append((nombre, movimiento, t_entra, t_sale))


def se_solapan(r1, r2):
    """True si el rango de tiempo [t_entra, t_sale] de r1 y r2 se cruzan."""
    _, _, e1, s1 = r1
    _, _, e2, s2 = r2
    return e1 < s2 and e2 < s1


# ---------------------------------------------------------------------------
# Prueba 1: tráfico horizontal (A->B y B->A deben poder ir juntos)
# ---------------------------------------------------------------------------
def prueba_horizontal():
    global resultados
    resultados = []
    hilos = [
        threading.Thread(target=carro_prueba, args=("H1", "A->B")),
        threading.Thread(target=carro_prueba, args=("H2", "B->A")),
    ]
    for h in hilos: h.start()
    for h in hilos: h.join()

    h1 = next(r for r in resultados if r[0] == "H1")
    h2 = next(r for r in resultados if r[0] == "H2")
    assert se_solapan(h1, h2), "H1 y H2 debieron poder pasar al mismo tiempo"
    print("✅ Prueba HORIZONTAL: A->B y B->A pasaron juntos. OK")


# ---------------------------------------------------------------------------
# Prueba 2: tráfico vertical (C->D y D->C deben poder ir juntos)
# ---------------------------------------------------------------------------
def prueba_vertical():
    global resultados
    resultados = []
    hilos = [
        threading.Thread(target=carro_prueba, args=("V1", "C->D")),
        threading.Thread(target=carro_prueba, args=("V2", "D->C")),
    ]
    for h in hilos: h.start()
    for h in hilos: h.join()

    v1 = next(r for r in resultados if r[0] == "V1")
    v2 = next(r for r in resultados if r[0] == "V2")
    assert se_solapan(v1, v2), "V1 y V2 debieron poder pasar al mismo tiempo"
    print("✅ Prueba VERTICAL: C->D y D->C pasaron juntos. OK")


# ---------------------------------------------------------------------------
# Prueba 3: horizontal vs vertical NUNCA deben solaparse
# ---------------------------------------------------------------------------
def prueba_conflicto():
    global resultados
    resultados = []
    hilos = [
        threading.Thread(target=carro_prueba, args=("H1", "A->B")),
        threading.Thread(target=carro_prueba, args=("H2", "B->A")),
        threading.Thread(target=carro_prueba, args=("V1", "C->D")),
        threading.Thread(target=carro_prueba, args=("V2", "D->C")),
    ]
    for h in hilos: h.start()
    for h in hilos: h.join()

    horizontales = [r for r in resultados if EJE[r[1]] == "HORIZONTAL"]
    verticales = [r for r in resultados if EJE[r[1]] == "VERTICAL"]

    for h in horizontales:
        for v in verticales:
            assert not se_solapan(h, v), f"{h[0]} y {v[0]} NO debían coincidir"
    print("✅ Prueba CONFLICTO: horizontal y vertical nunca coincidieron. OK")


# ---------------------------------------------------------------------------
# Prueba 4: estado seguro / inseguro
# Un carro vertical debe esperar a que el horizontal termine.
# ---------------------------------------------------------------------------
def prueba_estado_seguro():
    global resultados
    resultados = []
    h1 = threading.Thread(target=carro_prueba, args=("H1", "A->B"))
    h1.start()
    time.sleep(0.1)   # H1 ya está usando el eje horizontal

    v1 = threading.Thread(target=carro_prueba, args=("V1", "C->D"))
    v1.start()

    h1.join()
    v1.join()

    reg_h1 = next(r for r in resultados if r[0] == "H1")
    reg_v1 = next(r for r in resultados if r[0] == "V1")
    t_sale_h1 = reg_h1[3]
    t_entra_v1 = reg_v1[2]

    assert t_entra_v1 >= t_sale_h1, "V1 no debía entrar antes de que H1 saliera"
    print("✅ Prueba ESTADO SEGURO/INSEGURO: V1 esperó a que H1 liberara la zona. OK")


if __name__ == "__main__":
    prueba_horizontal()
    prueba_vertical()
    prueba_conflicto()
    prueba_estado_seguro()
    print("\nTodas las pruebas pasaron correctamente.")

"""
Cruce de dos autopistas (sin giros) con el Algoritmo del Banquero.

  Autopista horizontal:  A -> B   y   B -> A
  Autopista vertical  :  C -> D   y   D -> C

Regla simple:
  - Los dos sentidos de la MISMA autopista pueden pasar juntos.
  - Las dos autopistas NUNCA pasan al mismo tiempo (eso lo cuida el Banquero).
"""

import threading
import time
import random

MOVIMIENTOS = ["A->B", "B->A", "C->D", "D->C"]

EJE = {
    "A->B": "HORIZONTAL",
    "B->A": "HORIZONTAL",
    "C->D": "VERTICAL",
    "D->C": "VERTICAL",
}

# ---------------- "Banquero": quién tiene la zona del cruce ----------------
lock = threading.Lock()
cond = threading.Condition(lock)
eje_activo = None      # None, "HORIZONTAL" o "VERTICAL"
carros_activos = 0     # cuántos carros hay ahora mismo cruzando

# ---------------- estadísticas por semáforo ----------------
semaforos = {m: {"pasaron": 0, "espera_total": 0.0, "cruce_total": 0.0} for m in MOVIMIENTOS}
lock_stats = threading.Lock()


def pedir_paso(movimiento):
    """Un carro pide permiso para entrar al cruce (esto es el Banquero)."""
    global eje_activo, carros_activos
    mi_eje = EJE[movimiento]

    with cond:
        # Espero mientras el OTRO eje esté usando el cruce (estado inseguro)
        while eje_activo is not None and eje_activo != mi_eje:
            cond.wait()

        # Aquí ya es seguro: nadie del otro eje está pasando
        eje_activo = mi_eje
        carros_activos += 1


def liberar_paso():
    """El carro ya cruzó y libera el recurso."""
    global eje_activo, carros_activos
    with cond:
        carros_activos -= 1
        if carros_activos == 0:
            eje_activo = None     # el cruce queda libre para cualquier eje
        cond.notify_all()


def carro(nombre, movimiento):
    t_llegada = time.time()

    pedir_paso(movimiento)
    t_entra = time.time()
    espera = t_entra - t_llegada
    print(f"🟢 {nombre:6s} {movimiento}  entra al cruce (esperó {espera:.2f}s)")

    tiempo_cruce = random.uniform(0.5, 1.2)
    time.sleep(tiempo_cruce)     # el carro está cruzando

    liberar_paso()
    print(f"🔴 {nombre:6s} {movimiento}  sale del cruce (tardó {tiempo_cruce:.2f}s)")

    with lock_stats:
        s = semaforos[movimiento]
        s["pasaron"] += 1
        s["espera_total"] += espera
        s["cruce_total"] += tiempo_cruce


def reporte():
    print("\n----- REPORTE POR SEMÁFORO -----")
    for movimiento in MOVIMIENTOS:
        s = semaforos[movimiento]
        n = s["pasaron"]
        if n == 0:
            continue
        print(f"\nSemáforo {movimiento[0]}  (sentido {movimiento}, eje {EJE[movimiento]})")
        print(f"  Carros que pasaron : {n}")
        print(f"  Espera promedio    : {s['espera_total']/n:.2f} s")
        print(f"  Cruce promedio     : {s['cruce_total']/n:.2f} s")


# ------------------------- simulación principal -------------------------

if __name__ == "__main__":
    random.seed(1)
    hilos = []

    for i in range(12):
        movimiento = random.choice(MOVIMIENTOS)   # solo genera de los 4 permitidos
        nombre = f"Carro{i+1}"
        t = threading.Thread(target=carro, args=(nombre, movimiento))
        hilos.append(t)
        t.start()
        time.sleep(random.uniform(0.05, 0.2))     # llegan uno tras otro

    for t in hilos:
        t.join()

    reporte()

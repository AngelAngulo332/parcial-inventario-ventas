"""Demuestra el ROLLBACK: provoca un error controlado y verifica que los datos queden intactos."""
import os
import db

RUTA = "demo_rollback.db"
if os.path.exists(RUTA):
    os.remove(RUTA)
conn = db.conectar(RUTA)
pid = db.agregar_producto(conn, "Arduino UNO", 85000, 10)


def estado(titulo):
    p = db.obtener_producto(conn, pid)
    n = conn.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]
    print(f"[{titulo}] stock = {p['cantidad']} | ventas registradas = {n}")
    return p["cantidad"], n


print("=== DEMOSTRACIÓN DE TRANSACCIÓN ===")
antes = estado("ANTES   ")

print("\n-> Venta de 3 unidades con error simulado (después del INSERT, antes del UPDATE)")
try:
    db.registrar_venta(conn, pid, 3, simular_error=True)
except db.ErrorSimulado as e:
    print(f"   Excepción capturada: {e}\n   Se ejecutó ROLLBACK.")

despues = estado("DESPUÉS ")
print("\nRESULTADO:", "✓ Datos intactos (rollback correcto)" if antes == despues else "✗ INCONSISTENCIA")

print("\n-> Venta normal de 3 unidades (COMMIT)")
db.registrar_venta(conn, pid, 3)
estado("FINAL   ")

print("\n-> Validaciones")
for args in [(999, 1), (pid, 100)]:
    try:
        db.registrar_venta(conn, *args)
    except ValueError as e:
        print("   ✗", e)
estado("TRAS VALIDACIONES")

print("\n-> Eliminar producto con ventas (FK RESTRICT)")
try:
    db.eliminar_producto(conn, pid)
except Exception as e:
    print(f"   ✗ {type(e).__name__}: {e}")
conn.close()
os.remove(RUTA)

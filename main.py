"""Aplicación de consola - Tienda de componentes electrónicos."""
import sqlite3
import db


def pedir_float(msg):
    while True:
        try:
            v = float(input(msg))
            if v < 0:
                print("  ✗ No puede ser negativo.")
                continue
            return v
        except ValueError:
            print("  ✗ Ingresa un número válido.")


def pedir_int(msg, minimo=0):
    while True:
        try:
            v = int(input(msg))
            if v < minimo:
                print(f"  ✗ Debe ser >= {minimo}.")
                continue
            return v
        except ValueError:
            print("  ✗ Ingresa un número entero válido.")


def mostrar_productos(conn):
    filas = db.listar_productos(conn)
    if not filas:
        print("  (No hay productos registrados)")
        return
    print(f"\n{'ID':<4}{'Nombre':<28}{'Precio':>12}{'Cantidad':>10}")
    print("-" * 54)
    for f in filas:
        print(f"{f['id']:<4}{f['nombre']:<28}{f['precio']:>12,.2f}{f['cantidad']:>10}")


def op_agregar(conn):
    nombre = input("Nombre: ").strip()
    if not nombre:
        print("  ✗ El nombre no puede estar vacío.")
        return
    try:
        pid = db.agregar_producto(conn, nombre, pedir_float("Precio: "), pedir_int("Cantidad: "))
        print(f"  ✓ Producto registrado con id {pid}.")
    except sqlite3.IntegrityError:
        print("  ✗ Ya existe un producto con ese nombre.")


def op_actualizar(conn):
    mostrar_productos(conn)
    pid = pedir_int("ID del producto a actualizar: ", 1)
    if db.obtener_producto(conn, pid) is None:
        print("  ✗ El producto no existe.")
        return
    op = input("¿Actualizar (1) precio, (2) cantidad o (3) ambos? ").strip()
    precio = pedir_float("Nuevo precio: ") if op in ("1", "3") else None
    cant = pedir_int("Nueva cantidad: ") if op in ("2", "3") else None
    if precio is None and cant is None:
        print("  ✗ Opción inválida.")
        return
    db.actualizar_producto(conn, pid, precio, cant)
    print("  ✓ Producto actualizado.")


def op_eliminar(conn):
    mostrar_productos(conn)
    pid = pedir_int("ID del producto a eliminar: ", 1)
    try:
        if db.eliminar_producto(conn, pid):
            print("  ✓ Producto eliminado.")
        else:
            print("  ✗ El producto no existe.")
    except sqlite3.IntegrityError:
        print("  ✗ No se puede eliminar: el producto tiene ventas registradas (integridad referencial).")


def op_vender(conn, simular=False):
    mostrar_productos(conn)
    pid = pedir_int("ID del producto: ", 1)
    cant = pedir_int("Cantidad a vender: ", 1)
    try:
        total = db.registrar_venta(conn, pid, cant, simular_error=simular)
        print(f"  ✓ Venta registrada. Total: ${total:,.2f}")
    except db.ErrorSimulado as e:
        print(f"  ⚠ {e}\n  ↩ ROLLBACK ejecutado: no se guardó la venta ni se modificó el inventario.")
    except ValueError as e:
        print(f"  ✗ {e}")


def op_historial(conn):
    filas = db.historial_ventas(conn)
    if not filas:
        print("  (No hay ventas registradas)")
        return
    print(f"\n{'ID':<4}{'Producto':<26}{'Cant':>5}{'P.Unit':>12}{'Total':>14}  Fecha")
    print("-" * 78)
    for f in filas:
        print(f"{f['id']:<4}{f['nombre']:<26}{f['cantidad']:>5}{f['precio_unitario']:>12,.2f}"
              f"{f['total']:>14,.2f}  {f['fecha']}")


MENU = """
===== TIENDA DE COMPONENTES ELECTRÓNICOS =====
1. Registrar producto
2. Consultar productos
3. Actualizar precio/cantidad
4. Eliminar producto
5. Registrar venta
6. Historial de ventas
7. Registrar venta con ERROR SIMULADO (demo rollback)
0. Salir
"""


def main():
    conn = db.conectar()
    acciones = {"1": op_agregar, "2": mostrar_productos, "3": op_actualizar,
                "4": op_eliminar, "5": op_vender, "6": op_historial,
                "7": lambda c: op_vender(c, simular=True)}
    while True:
        print(MENU)
        op = input("Opción: ").strip()
        if op == "0":
            break
        accion = acciones.get(op)
        if accion:
            accion(conn)
        else:
            print("  ✗ Opción inválida.")
    conn.close()
    print("¡Hasta luego!")


if __name__ == "__main__":
    main()

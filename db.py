"""Capa de acceso a datos: conexión, esquema y operaciones CRUD + ventas."""
import sqlite3

DB_NAME = "tienda.db"


class ErrorSimulado(Exception):
    """Error controlado para demostrar el rollback."""


def conectar(ruta=DB_NAME):
    # isolation_level=None -> controlamos las transacciones manualmente (BEGIN/COMMIT/ROLLBACK)
    conn = sqlite3.connect(ruta, isolation_level=None)
    conn.execute("PRAGMA foreign_keys = ON")  # SQLite las desactiva por defecto
    conn.row_factory = sqlite3.Row
    crear_tablas(conn)
    return conn


def crear_tablas(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS productos (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre   TEXT    NOT NULL UNIQUE,
            precio   REAL    NOT NULL CHECK (precio >= 0),
            cantidad INTEGER NOT NULL CHECK (cantidad >= 0)
        );
        CREATE TABLE IF NOT EXISTS ventas (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id     INTEGER NOT NULL,
            cantidad        INTEGER NOT NULL CHECK (cantidad > 0),
            precio_unitario REAL    NOT NULL,
            total           REAL    NOT NULL,
            fecha           TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE RESTRICT
        );
    """)


# ---------- CRUD de productos ----------
def agregar_producto(conn, nombre, precio, cantidad):
    cur = conn.execute(
        "INSERT INTO productos (nombre, precio, cantidad) VALUES (?, ?, ?)",
        (nombre, precio, cantidad))
    return cur.lastrowid


def listar_productos(conn):
    return conn.execute(
        "SELECT id, nombre, precio, cantidad FROM productos ORDER BY id").fetchall()


def obtener_producto(conn, producto_id):
    return conn.execute(
        "SELECT id, nombre, precio, cantidad FROM productos WHERE id = ?",
        (producto_id,)).fetchone()


def actualizar_producto(conn, producto_id, precio=None, cantidad=None):
    if precio is not None:
        conn.execute("UPDATE productos SET precio = ? WHERE id = ?", (precio, producto_id))
    if cantidad is not None:
        conn.execute("UPDATE productos SET cantidad = ? WHERE id = ?", (cantidad, producto_id))
    return conn.total_changes


def eliminar_producto(conn, producto_id):
    """Respeta la FK: si el producto tiene ventas, SQLite lanza IntegrityError (RESTRICT)."""
    cur = conn.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
    return cur.rowcount


# ---------- Ventas ----------
def registrar_venta(conn, producto_id, cantidad, simular_error=False):
    """Registra una venta de forma atómica.

    1. BEGIN  2. verificar existencia  3. verificar stock
    4. INSERT venta  5. (error simulado opcional)  6. UPDATE inventario  7. COMMIT
    Cualquier excepción -> ROLLBACK (se cancela TODO, incluida la venta insertada).
    """
    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor que cero.")
    conn.execute("BEGIN IMMEDIATE")
    try:
        prod = conn.execute(
            "SELECT id, nombre, precio, cantidad FROM productos WHERE id = ?",
            (producto_id,)).fetchone()
        if prod is None:
            raise ValueError(f"El producto con id {producto_id} no existe.")
        if prod["cantidad"] < cantidad:
            raise ValueError(
                f"Stock insuficiente de '{prod['nombre']}': hay {prod['cantidad']}, se pidieron {cantidad}.")

        total = prod["precio"] * cantidad
        conn.execute(
            "INSERT INTO ventas (producto_id, cantidad, precio_unitario, total) VALUES (?, ?, ?, ?)",
            (producto_id, cantidad, prod["precio"], total))

        if simular_error:  # falla DESPUÉS de insertar la venta y ANTES de descontar stock
            raise ErrorSimulado("Fallo simulado entre el INSERT de la venta y el UPDATE del inventario.")

        conn.execute(
            "UPDATE productos SET cantidad = cantidad - ? WHERE id = ?",
            (cantidad, producto_id))
        conn.execute("COMMIT")
        return total
    except Exception:
        conn.execute("ROLLBACK")
        raise


def historial_ventas(conn):
    return conn.execute("""
        SELECT v.id, p.nombre, v.cantidad, v.precio_unitario, v.total, v.fecha
        FROM ventas v
        JOIN productos p ON p.id = v.producto_id
        ORDER BY v.id
    """).fetchall()

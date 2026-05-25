import sqlite3
import bcrypt
import os
import sys

db_path = r'data\value_analyst.db'
if not os.path.exists(db_path):
    print("Base de datos no encontrada en el directorio actual.")
    sys.exit(1)

conn = sqlite3.connect(db_path)
c = conn.cursor()

new_pass = "WarrenBuffett#2026"
hashed = bcrypt.hashpw(new_pass.encode('utf-8'), bcrypt.gensalt(rounds=10)).decode('utf-8')

c.execute("UPDATE users SET password_hash = ? WHERE username = ?", (hashed, 'garias'))
if c.rowcount == 0:
    print("No se ha encontrado al usuario 'garias'.")
else:
    print("Contraseña de 'garias' actualizada correctamente a WarrenBuffett#2026!")

conn.commit()
conn.close()

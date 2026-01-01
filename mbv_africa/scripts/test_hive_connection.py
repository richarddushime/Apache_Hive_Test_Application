from pyhive import hive
import sys

try:
    print("Attempting to connect to Hive at hive-server:10000 with NOSASL...")
    conn = hive.Connection(host='hive-server', port=10000, username='hive', auth='NOSASL')
    cursor = conn.cursor()
    cursor.execute("SHOW DATABASES")
    print("Databases found:", cursor.fetchall())
    conn.close()
    print("Success!")
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)
EOF

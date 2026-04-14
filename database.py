import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor

class DeviceDB:
    def __init__(self, init_tables=False):
        self.host = os.getenv("DB_HOST")
        self.database = os.getenv("DB_NAME")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.port = os.getenv("DB_PORT")
        self.gateway_id = os.getenv("GATEWAY_ID")
        
        if init_tables:
            self.initialize_tables()

    def initialize_tables(self):
        """Standardizes database migrations by ensuring all required schema tables natively exist on boot."""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS devices (
                id SERIAL PRIMARY KEY,
                gateway_id VARCHAR(50) NOT NULL,
                device_id_from VARCHAR(50) NOT NULL,
                device_id_to VARCHAR(50) NOT NULL,
                device_secret VARCHAR(100) NOT NULL,
                ok_channel INT NOT NULL,
                ng_channel INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS inspection_devices (
                id SERIAL PRIMARY KEY,
                gateway_id VARCHAR(50) NOT NULL,
                device_id_from VARCHAR(50) NOT NULL,
                device_id_to VARCHAR(50) NOT NULL,
                device_secret VARCHAR(100) NOT NULL,
                total_sensor INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        ]
        
        # Use a localized quick connection loop for startup
        retries = 3
        conn = None
        while retries > 0:
            try:
                conn = psycopg2.connect(
                    host=self.host, database=self.database,
                    user=self.user, password=self.password, port=self.port
                )
                with conn.cursor() as cur:
                    for q in queries:
                        cur.execute(q)
                conn.commit()
                print("[DATABASE] Auto-Migrations applied successfully! Application ready.")
                break
            except psycopg2.OperationalError:
                retries -= 1
                time.sleep(2)
            except Exception as e:
                print(f"[DATABASE] Auto-Migration Error: {e}")
                break
        if conn:
            conn.close()

    def get_connection(self):
        """Attempts to connect to the DB with retries."""
        retries = 5
        while retries > 0:
            try:
                conn = psycopg2.connect(
                    host=self.host,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                    port=self.port
                )
                return conn
            except Exception as e:
                print(f"[DB] Connection failed, retrying... ({retries} left): {e}")
                retries -= 1
                time.sleep(5)
        raise Exception("Could not connect to the database after several attempts.")

    def load_mappings(self):
        """Fetches all device mappings assigned to this gateway."""
        query = """
            SELECT device_id_from, device_id_to, device_secret, ok_channel, ng_channel 
            FROM devices 
            WHERE gateway_id = %s;
        """
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (self.gateway_id,))
                rows = cur.fetchall()
                print(f"[DB] Successfully loaded {len(rows)} device mappings.")
                return rows
        finally:
            conn.close()

    def get_all_devices(self):
        """Fetches all devices for the UI."""
        query = "SELECT id, gateway_id, device_id_from, device_id_to, device_secret, ok_channel, ng_channel FROM devices;"
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                return cur.fetchall()
        finally:
            conn.close()

    def add_device(self, data):
        """Adds a new device mapping."""
        query = """
            INSERT INTO devices (gateway_id, device_id_from, device_id_to, device_secret, ok_channel, ng_channel)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;
        """
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, (
                    data.get('gateway_id', self.gateway_id),
                    data['device_id_from'],
                    data['device_id_to'],
                    data['device_secret'],
                    data['ok_channel'],
                    data['ng_channel']
                ))
                new_id = cur.fetchone()[0]
                conn.commit()
                return new_id
        finally:
            conn.close()

    def update_device(self, device_id, data):
        """Updates an existing device mapping."""
        query = """
            UPDATE devices 
            SET gateway_id = %s, device_id_from = %s, device_id_to = %s, device_secret = %s, ok_channel = %s, ng_channel = %s
            WHERE id = %s;
        """
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, (
                    data.get('gateway_id', self.gateway_id),
                    data['device_id_from'],
                    data['device_id_to'],
                    data['device_secret'],
                    data['ok_channel'],
                    data['ng_channel'],
                    device_id
                ))
                conn.commit()
                return cur.rowcount > 0
        finally:
            conn.close()

    def delete_device(self, device_id):
        """Deletes a device mapping."""
        query = "DELETE FROM devices WHERE id = %s;"
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, (device_id,))
                conn.commit()
                return cur.rowcount > 0
        finally:
            conn.close()

    # ================= INSPECTION DEVICES =================
    
    def load_inspection_mappings(self):
        """Loads mappings specifically for the current gateway_id."""
        query = """
            SELECT device_id_from, device_id_to, device_secret, total_sensor
            FROM inspection_devices
            WHERE gateway_id = %s;
        """
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (self.gateway_id,))
                return cur.fetchall()
        finally:
            conn.close()

    def get_all_inspection_devices(self):
        query = "SELECT * FROM inspection_devices ORDER BY created_at DESC;"
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                return cur.fetchall()
        finally:
            conn.close()

    def add_inspection_device(self, data):
        query = """
            INSERT INTO inspection_devices (gateway_id, device_id_from, device_id_to, device_secret, total_sensor)
            VALUES (%s, %s, %s, %s, %s) RETURNING id;
        """
        conn = self.get_connection()
        idx = None
        try:
            with conn.cursor() as cur:
                cur.execute(query, (
                    data.get('gateway_id', self.gateway_id),
                    data['device_id_from'],
                    data['device_id_to'],
                    data['device_secret'],
                    data['total_sensor']
                ))
                idx = cur.fetchone()[0]
                conn.commit()
            return idx
        finally:
            conn.close()

    def update_inspection_device(self, device_id, data):
        query = """
            UPDATE inspection_devices 
            SET gateway_id = %s, device_id_from = %s, device_id_to = %s, device_secret = %s, total_sensor = %s
            WHERE id = %s;
        """
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, (
                    data.get('gateway_id', self.gateway_id),
                    data['device_id_from'],
                    data['device_id_to'],
                    data['device_secret'],
                    data['total_sensor'],
                    device_id
                ))
                conn.commit()
                return cur.rowcount > 0
        finally:
            conn.close()

    def delete_inspection_device(self, device_id):
        query = "DELETE FROM inspection_devices WHERE id = %s;"
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, (device_id,))
                conn.commit()
                return cur.rowcount > 0
        finally:
            conn.close()

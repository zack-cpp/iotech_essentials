import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor

class DeviceDB:
    def __init__(self):
        self.host = os.getenv("DB_HOST")
        self.database = os.getenv("DB_NAME")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.port = os.getenv("DB_PORT")
        self.gateway_id = os.getenv("GATEWAY_ID")

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

import time
from cassandra.cluster import Cluster
from cassandra.cluster import NoHostAvailable

for attempt in range(1, 11):  # try up to 10 times
    print(f"🔍 Attempt {attempt}: connecting to ScyllaDB on 127.0.0.1:9042...")
    try:
        cluster = Cluster(['127.0.0.1'], port=9042, connect_timeout=10)
        session = cluster.connect()
        print("✅ Connected to ScyllaDB")

        rows = session.execute("SELECT release_version FROM system.local")
        for row in rows:
            print("ScyllaDB release version:", row.release_version)
        break
    except NoHostAvailable as e:
        print("❌ Still not ready, retrying in 10s...")
        time.sleep(10)
else:
    print("❌ Could not connect after 10 attempts.")

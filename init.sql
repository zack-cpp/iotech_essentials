-- ============================================
-- OEE IoT Gateway — Database Bootstrap
-- ============================================

CREATE TABLE IF NOT EXISTS counting_devices (
    id SERIAL PRIMARY KEY,
    gateway_id VARCHAR(50) NOT NULL,
    node_id VARCHAR(50) NOT NULL,
    cloud_uid VARCHAR(100) NOT NULL,
    device_secret VARCHAR(150) NOT NULL,
    ok_channel INT NOT NULL DEFAULT 0,
    ng_channel INT NOT NULL DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS inspection_devices (
    id SERIAL PRIMARY KEY,
    gateway_id VARCHAR(50) NOT NULL,
    node_id VARCHAR(50) NOT NULL,
    cloud_uid VARCHAR(100) NOT NULL,
    device_secret VARCHAR(150) NOT NULL,
    total_sensor INT NOT NULL DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed: Example counting device
INSERT INTO counting_devices (gateway_id, node_id, cloud_uid, device_secret, ok_channel, ng_channel)
VALUES ('GATEWAY_01', 'C071', 'dd880e00-example-uid', 'N0Tlslo-example-secret', 0, 1);

-- Seed: Example inspection device
INSERT INTO inspection_devices (gateway_id, node_id, cloud_uid, device_secret, total_sensor)
VALUES ('GATEWAY_01', 'Q005', 'dd880e00-example-uid-2', 'N0Tlslo-example-secret-2', 12);

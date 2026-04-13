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

CREATE TABLE IF NOT EXISTS inspection_devices (
    id SERIAL PRIMARY KEY,
    gateway_id VARCHAR(50) NOT NULL,
    device_id_from VARCHAR(50) NOT NULL,
    device_id_to VARCHAR(50) NOT NULL,
    device_secret VARCHAR(100) NOT NULL,
    total_sensor INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert dummy mapping data based on the .env values (ZaCK_PC)
INSERT INTO devices (gateway_id, device_id_from, device_id_to, device_secret, ok_channel, ng_channel)
VALUES ('ZaCK_PC', 'C071', '3507fb75-3180-4e30-8681-5d10b6545ea0', 'kLnGTMm64iagkKcpZ5a-XgP9OSLOLEBwWq72gzdG6SU', 0, 1);

INSERT INTO inspection_devices (gateway_id, device_id_from, device_id_to, device_secret, total_sensor)
VALUES ('ZaCK_PC', 'HAS-AI-0002', '0bd548e2-1833-408d-a7f2-45166edaa80d', 'dummytestsecret', 24);

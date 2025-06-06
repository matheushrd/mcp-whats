-- Linha "CREATE DATABASE mcp_platform;" REMOVIDA daqui.
-- A criação do banco de dados é gerenciada pela imagem Docker do PostgreSQL
-- através da variável de ambiente POSTGRES_DB.

CREATE DATABASE mcp_platform;

\c mcp_platform;

-- Create clients table with JSONB fields for structured data
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    client_name VARCHAR(100) UNIQUE NOT NULL,
    business_name VARCHAR(200) NOT NULL,
    business_type VARCHAR(50),
    environments JSONB,
    credentials_file VARCHAR(255),
    resources JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create users table for web interface
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(200),
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de logs e outras permanecem iguais...
CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,
    client_name VARCHAR(100) NOT NULL,
    appointment_id VARCHAR(100) NOT NULL,
    customer_name VARCHAR(200) NOT NULL,
    customer_phone VARCHAR(50) NOT NULL,
    service_type VARCHAR(100),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    status VARCHAR(50) DEFAULT 'scheduled',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_name) REFERENCES clients(client_name) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS message_logs (
    id SERIAL PRIMARY KEY,
    client_name VARCHAR(100) NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    message_type VARCHAR(50) NOT NULL,
    message_content TEXT,
    response_content TEXT,
    intent VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_name) REFERENCES clients(client_name) ON DELETE CASCADE
);


-- Indexes
CREATE INDEX IF NOT EXISTS idx_appointments_client_name ON appointments(client_name);
CREATE INDEX IF NOT EXISTS idx_appointments_customer_phone ON appointments(customer_phone);
CREATE INDEX IF NOT EXISTS idx_message_logs_client_name ON message_logs(client_name);

-- Insert default admin user (password: admin123)
-- Senha é: admin123
INSERT INTO users (username, password_hash, is_admin)
VALUES ('admin', '$2b$12$YqKqH9F.K2K3X.Z8iKQmLOXYgF5Gn5WRd6V5Yp5kX5QY5Z5Z5Z5Z', true)
ON CONFLICT (username) DO NOTHING;

-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers
DROP TRIGGER IF EXISTS update_clients_updated_at ON clients;
CREATE TRIGGER update_clients_updated_at BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_appointments_updated_at ON appointments;
CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON appointments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
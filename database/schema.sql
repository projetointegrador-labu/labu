-- LABU - Esquema do banco de dados (MySQL 8+, InnoDB, utf8mb4)
-- Idempotente: pode ser executado várias vezes (CREATE TABLE IF NOT EXISTS).
-- Aplicado automaticamente por:  flask --app wsgi init-db

CREATE TABLE IF NOT EXISTS usuarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(120) NOT NULL,
  email VARCHAR(190) NOT NULL UNIQUE,
  senha_hash VARCHAR(255) NOT NULL,
  telefone VARCHAR(20) NULL,
  perfil VARCHAR(20) NOT NULL DEFAULT 'contratante',
  ativo TINYINT(1) NOT NULL DEFAULT 1,
  consentimento_lgpd TINYINT(1) NOT NULL DEFAULT 0,
  consentimento_em DATETIME NULL,
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS categorias (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(80) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS prestadores (
  usuario_id INT PRIMARY KEY,
  categoria_id INT NOT NULL,
  descricao TEXT NULL,
  anos_experiencia INT NOT NULL DEFAULT 0,
  disponibilidade VARCHAR(20) NOT NULL DEFAULT 'imediata',
  whatsapp VARCHAR(20) NULL,
  cep VARCHAR(8) NULL,
  bairro VARCHAR(100) NULL,
  cidade VARCHAR(100) NOT NULL,
  estado CHAR(2) NOT NULL,
  latitude DECIMAL(9,6) NULL,
  longitude DECIMAL(9,6) NULL,
  raio_km INT NOT NULL DEFAULT 10,
  visivel TINYINT(1) NOT NULL DEFAULT 1,
  atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
  FOREIGN KEY (categoria_id) REFERENCES categorias(id),
  INDEX idx_prest_cidade (cidade),
  INDEX idx_prest_bairro (bairro),
  INDEX idx_prest_estado (estado),
  INDEX idx_prest_geo (latitude, longitude)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS servicos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  prestador_id INT NOT NULL,
  contratante_id INT NOT NULL,
  categoria_id INT NOT NULL,
  descricao TEXT NOT NULL,
  data_prevista DATE NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'solicitado',
  avaliacao TINYINT NULL,
  comentario TEXT NULL,
  criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  concluido_em DATETIME NULL,
  FOREIGN KEY (prestador_id) REFERENCES usuarios(id) ON DELETE CASCADE,
  FOREIGN KEY (contratante_id) REFERENCES usuarios(id) ON DELETE CASCADE,
  FOREIGN KEY (categoria_id) REFERENCES categorias(id),
  INDEX idx_serv_prestador (prestador_id),
  INDEX idx_serv_contratante (contratante_id),
  INDEX idx_serv_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

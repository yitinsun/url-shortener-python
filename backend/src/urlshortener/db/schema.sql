CREATE DATABASE IF NOT EXISTS shortener_dev
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE url_mappings (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    long_url VARCHAR(2048) NOT NULL,
    short_code VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    UNIQUE KEY idx_short_code (short_code),
    INDEX idx_long_url (long_url(255))
) ENGINE=InnoDB
  AUTO_INCREMENT=56800235
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

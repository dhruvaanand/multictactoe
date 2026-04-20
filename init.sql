CREATE DATABASE IF NOT EXISTS multictactoe;
USE multictactoe;

CREATE TABLE IF NOT EXISTS users (
    uid VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    elo_rating INT DEFAULT 1200,
    is_online BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS match_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    game_id VARCHAR(64) NOT NULL UNIQUE,
    p1_uid VARCHAR(50) NOT NULL,
    p2_uid VARCHAR(50) NOT NULL,
    winner_uid VARCHAR(50) NULL,
    is_draw BOOLEAN NOT NULL DEFAULT FALSE,
    forfeit BOOLEAN NOT NULL DEFAULT FALSE,
    p1_rating_before INT NOT NULL,
    p2_rating_before INT NOT NULL,
    p1_rating_after INT NOT NULL,
    p2_rating_after INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_match_history_p1 FOREIGN KEY (p1_uid) REFERENCES users(uid),
    CONSTRAINT fk_match_history_p2 FOREIGN KEY (p2_uid) REFERENCES users(uid),
    CONSTRAINT fk_match_history_winner FOREIGN KEY (winner_uid) REFERENCES users(uid)
);
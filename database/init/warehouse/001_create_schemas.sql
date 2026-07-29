CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS intermediate;
CREATE SCHEMA IF NOT EXISTS analytics;

COMMENT ON SCHEMA raw IS
    'Cópia dos dados de origem com o mínimo de transformação.';
COMMENT ON SCHEMA staging IS
    'Padronização de nomes, tipos e regras básicas de qualidade.';
COMMENT ON SCHEMA intermediate IS
    'Transformações reutilizáveis e integração entre entidades.';
COMMENT ON SCHEMA analytics IS
    'Tabelas dimensionais prontas para consumo analítico.';

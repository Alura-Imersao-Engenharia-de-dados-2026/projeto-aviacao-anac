-- Execute em um ambiente de estudos com permissao para criar estes objetos.
CREATE CATALOG IF NOT EXISTS voebem;
CREATE SCHEMA IF NOT EXISTS voebem.bronze;
CREATE SCHEMA IF NOT EXISTS voebem.silver;
CREATE SCHEMA IF NOT EXISTS voebem.gold;
CREATE VOLUME IF NOT EXISTS voebem.bronze.arquivos;

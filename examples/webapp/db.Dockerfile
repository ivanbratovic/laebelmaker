FROM postgres:lts

COPY init.sql /docker-entrypoint-initdb.d/
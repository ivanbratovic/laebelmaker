FROM postgres:14.6

COPY init.sql /docker-entrypoint-initdb.d/
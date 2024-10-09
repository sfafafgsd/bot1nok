FROM postgres:15.6

RUN mkdir -p /etc/postgresql/
RUN chown postgres:postgres -R /var/lib/postgresql/data
RUN chmod 750 -R /var/lib/postgresql/data

ENTRYPOINT ["bash", "-c", "echo \"listen_addresses = '*'\" >> /etc/postgresql/postgresql.conf && echo \"port = 5432\" >> /etc/postgresql/postgresql.conf &&\
rm -rf /var/lib/postgresql/data/* && sleep 5 && export PGPASSWORD=${DB_REPL_PASSWORD} && echo $PGPASSWORD && pg_basebackup -v -R -h ${DB_HOST} -p ${DB_PORT} -U ${DB_REPL_USER} -W -P -D \
/var/lib/postgresql/data && chown postgres:postgres -R /var/lib/postgresql/data && chmod 750 -R /var/lib/postgresql/data; sleep 10; postgres -c config_file=/etc/postgresql/postgresql.conf"]

USER postgres

EXPOSE 5432

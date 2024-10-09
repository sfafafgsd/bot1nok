FROM postgres:15.6

RUN chmod 750 -R /var/lib/postgresql/data
RUN chown -R postgres:postgres /var/log/postgresql
RUN chmod 750 -R /var/log/postgresql/
RUN touch /var/log/postgresql/postgresql.log
RUN chown postgres:postgres /var/log/postgresql/postgresql.log
RUN chmod 750 /var/log/postgresql/postgresql.log
USER postgres

ENTRYPOINT ["bash", "-c", "rm -rf /var/log/postgresql/* && rm -rf /var/lib/postgresql/data/* ; initdb; echo \"host all  all    0.0.0.0/0  md5\" >> /etc/postgresql/pg_hba.conf &&\
    echo \"listen_addresses='*'\" >> /etc/postgresql/postgresql.conf &&\
    echo \"archive_mode=on\" >> /etc/postgresql/postgresql.conf &&\
    echo \"archive_command = 'cp %p /oracle/pg_data/archive/%f'\" >> /etc/postgresql/postgresql.conf &&\
    echo \"max_wal_senders = 10\" >> /etc/postgresql/postgresql.conf &&\
    echo \"wal_level = replica\" >> /etc/postgresql/postgresql.conf &&\
    echo \"wal_log_hints = on\" >> /etc/postgresql/postgresql.conf &&\
    echo \"host replication $DB_REPL_USER $DB_REPL_HOST/32 scram-sha-256\" >> /etc/postgresql/pg_hba.conf &&\
    echo \"log_destination = 'stderr'\" >> /etc/postgresql/postgresql.conf &&\
    echo \"logging_collector = on\" >> /etc/postgresql/postgresql.conf &&\
    echo \"log_directory = '/var/log/postgresql'\" >> /etc/postgresql/postgresql.conf &&\
    echo \"log_filename = 'postgresql.log'\" >> /etc/postgresql/postgresql.conf &&\
    echo \"log_replication_commands = on\" >> /etc/postgresql/postgresql.conf && cat /etc/postgresql/postgresql.conf && pg_ctl start &&\
    psql -c \"CREATE ROLE $DB_REPL_USER WITH REPLICATION LOGIN PASSWORD '$DB_REPL_PASSWORD';\" ;\
    psql -c \"CREATE DATABASE $DB_DATABASE;\" ;\
    psql -d $DB_DATABASE -c \"CREATE TABLE IF NOT EXISTS second(ID SERIAL PRIMARY KEY NOT NULL, phone varchar(50) NOT NULL);\" &&\
    psql -d $DB_DATABASE -c \"CREATE TABLE IF NOT EXISTS first(ID SERIAL PRIMARY KEY NOT NULL, email varchar(50) NOT NULL);\" &&\
    psql -c \"ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';\" &&\
    pg_ctl stop && postgres -c config_file=/etc/postgresql/postgresql.conf -c hba_file=/etc/postgresql/pg_hba.conf"]


EXPOSE 5432

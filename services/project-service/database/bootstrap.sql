CREATE ROLE acadence_project_owner NOLOGIN;
CREATE ROLE acadence_project_migrator LOGIN NOINHERIT;
CREATE ROLE acadence_project_runtime LOGIN NOINHERIT;

GRANT acadence_project_owner TO acadence_project_migrator;

CREATE SCHEMA project AUTHORIZATION acadence_project_owner;
GRANT USAGE ON SCHEMA project TO acadence_project_runtime;
REVOKE ALL ON SCHEMA project FROM PUBLIC;

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM acadence_project_runtime;

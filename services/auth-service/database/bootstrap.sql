CREATE ROLE acadence_auth_owner NOLOGIN;
CREATE ROLE acadence_auth_migrator LOGIN NOINHERIT;
CREATE ROLE acadence_auth_runtime LOGIN NOINHERIT;

GRANT acadence_auth_owner TO acadence_auth_migrator;

CREATE SCHEMA auth AUTHORIZATION acadence_auth_owner;
GRANT USAGE ON SCHEMA auth TO acadence_auth_runtime;
REVOKE ALL ON SCHEMA auth FROM PUBLIC;

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM acadence_auth_runtime;

CREATE ROLE acadence_auth_owner NOLOGIN;
CREATE ROLE acadence_auth_migrator LOGIN NOINHERIT;
CREATE ROLE acadence_auth_runtime LOGIN NOINHERIT;

GRANT acadence_auth_owner TO acadence_auth_migrator;
GRANT acadence_auth_owner TO CURRENT_USER WITH INHERIT FALSE, SET TRUE;

CREATE SCHEMA auth AUTHORIZATION acadence_auth_owner;
SET ROLE acadence_auth_owner;
GRANT USAGE ON SCHEMA auth TO acadence_auth_runtime;
REVOKE ALL ON SCHEMA auth FROM PUBLIC;
RESET ROLE;

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM acadence_auth_runtime;

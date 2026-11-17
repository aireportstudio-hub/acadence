CREATE ROLE acadence_orchestration_owner NOLOGIN;
CREATE ROLE acadence_orchestration_migrator LOGIN NOINHERIT;
CREATE ROLE acadence_orchestration_runtime LOGIN NOINHERIT;

GRANT acadence_orchestration_owner TO acadence_orchestration_migrator;
GRANT acadence_orchestration_owner TO CURRENT_USER WITH INHERIT FALSE, SET TRUE;

CREATE SCHEMA orchestration AUTHORIZATION acadence_orchestration_owner;
SET ROLE acadence_orchestration_owner;
GRANT USAGE ON SCHEMA orchestration TO acadence_orchestration_runtime;
REVOKE ALL ON SCHEMA orchestration FROM PUBLIC;
RESET ROLE;

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM acadence_orchestration_runtime;

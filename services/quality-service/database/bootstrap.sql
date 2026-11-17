CREATE ROLE acadence_quality_owner NOLOGIN;
CREATE ROLE acadence_quality_migrator LOGIN NOINHERIT;
CREATE ROLE acadence_quality_runtime LOGIN NOINHERIT;

GRANT acadence_quality_owner TO acadence_quality_migrator;
GRANT acadence_quality_owner TO CURRENT_USER WITH INHERIT FALSE, SET TRUE;

CREATE SCHEMA quality AUTHORIZATION acadence_quality_owner;
SET ROLE acadence_quality_owner;
GRANT USAGE ON SCHEMA quality TO acadence_quality_runtime;
REVOKE ALL ON SCHEMA quality FROM PUBLIC;
RESET ROLE;

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM acadence_quality_runtime;

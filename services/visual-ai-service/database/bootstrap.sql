CREATE ROLE acadence_visual_owner NOLOGIN;
CREATE ROLE acadence_visual_migrator LOGIN NOINHERIT;
CREATE ROLE acadence_visual_runtime LOGIN NOINHERIT;

GRANT acadence_visual_owner TO acadence_visual_migrator;

CREATE SCHEMA visual AUTHORIZATION acadence_visual_owner;
GRANT USAGE ON SCHEMA visual TO acadence_visual_runtime;
REVOKE ALL ON SCHEMA visual FROM PUBLIC;

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM acadence_visual_runtime;

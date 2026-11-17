CREATE ROLE acadence_visual_owner NOLOGIN;
CREATE ROLE acadence_visual_migrator LOGIN NOINHERIT;
CREATE ROLE acadence_visual_runtime LOGIN NOINHERIT;

GRANT acadence_visual_owner TO acadence_visual_migrator;
GRANT acadence_visual_owner TO CURRENT_USER WITH INHERIT FALSE, SET TRUE;

CREATE SCHEMA visual AUTHORIZATION acadence_visual_owner;
SET ROLE acadence_visual_owner;
GRANT USAGE ON SCHEMA visual TO acadence_visual_runtime;
REVOKE ALL ON SCHEMA visual FROM PUBLIC;
RESET ROLE;

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM acadence_visual_runtime;

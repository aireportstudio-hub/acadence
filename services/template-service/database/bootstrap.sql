CREATE ROLE acadence_template_owner NOLOGIN;
CREATE ROLE acadence_template_migrator LOGIN NOINHERIT;
CREATE ROLE acadence_template_runtime LOGIN NOINHERIT;

GRANT acadence_template_owner TO acadence_template_migrator;

CREATE SCHEMA template AUTHORIZATION acadence_template_owner;
GRANT USAGE ON SCHEMA template TO acadence_template_runtime;
REVOKE ALL ON SCHEMA template FROM PUBLIC;

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM acadence_template_runtime;

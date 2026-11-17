CREATE ROLE acadence_billing_owner NOLOGIN;
CREATE ROLE acadence_billing_migrator LOGIN NOINHERIT;
CREATE ROLE acadence_billing_runtime LOGIN NOINHERIT;

GRANT acadence_billing_owner TO acadence_billing_migrator;
GRANT acadence_billing_owner TO CURRENT_USER WITH INHERIT FALSE, SET TRUE;

CREATE SCHEMA billing AUTHORIZATION acadence_billing_owner;
SET ROLE acadence_billing_owner;
GRANT USAGE ON SCHEMA billing TO acadence_billing_runtime;
REVOKE ALL ON SCHEMA billing FROM PUBLIC;
RESET ROLE;

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM acadence_billing_runtime;

CREATE ROLE acadence_billing_owner NOLOGIN;
CREATE ROLE acadence_billing_migrator LOGIN NOINHERIT;
CREATE ROLE acadence_billing_runtime LOGIN NOINHERIT;

GRANT acadence_billing_owner TO acadence_billing_migrator;

CREATE SCHEMA billing AUTHORIZATION acadence_billing_owner;
GRANT USAGE ON SCHEMA billing TO acadence_billing_runtime;
REVOKE ALL ON SCHEMA billing FROM PUBLIC;

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM acadence_billing_runtime;

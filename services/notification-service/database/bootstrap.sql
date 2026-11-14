CREATE ROLE acadence_notification_owner NOLOGIN;
CREATE ROLE acadence_notification_migrator LOGIN NOINHERIT;
CREATE ROLE acadence_notification_runtime LOGIN NOINHERIT;

GRANT acadence_notification_owner TO acadence_notification_migrator;

CREATE SCHEMA notification AUTHORIZATION acadence_notification_owner;
GRANT USAGE ON SCHEMA notification TO acadence_notification_runtime;
REVOKE ALL ON SCHEMA notification FROM PUBLIC;

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM acadence_notification_runtime;

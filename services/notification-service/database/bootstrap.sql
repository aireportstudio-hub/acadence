CREATE ROLE acadence_notification_owner NOLOGIN;
CREATE ROLE acadence_notification_migrator LOGIN NOINHERIT;
CREATE ROLE acadence_notification_runtime LOGIN NOINHERIT;

GRANT acadence_notification_owner TO acadence_notification_migrator;
GRANT acadence_notification_owner TO CURRENT_USER WITH INHERIT FALSE, SET TRUE;

CREATE SCHEMA notification AUTHORIZATION acadence_notification_owner;
SET ROLE acadence_notification_owner;
GRANT USAGE ON SCHEMA notification TO acadence_notification_runtime;
REVOKE ALL ON SCHEMA notification FROM PUBLIC;
RESET ROLE;

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM acadence_notification_runtime;

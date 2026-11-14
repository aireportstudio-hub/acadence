CREATE ROLE acadence_document_owner NOLOGIN;
CREATE ROLE acadence_document_migrator LOGIN NOINHERIT;
CREATE ROLE acadence_document_runtime LOGIN NOINHERIT;

GRANT acadence_document_owner TO acadence_document_migrator;

CREATE SCHEMA document AUTHORIZATION acadence_document_owner;
GRANT USAGE ON SCHEMA document TO acadence_document_runtime;
REVOKE ALL ON SCHEMA document FROM PUBLIC;

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM acadence_document_runtime;

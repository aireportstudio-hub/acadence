import { spawn } from "node:child_process";
import { createServer } from "node:net";
import { fileURLToPath } from "node:url";
import path from "node:path";

import { PGlite } from "@electric-sql/pglite";
import { PGLiteSocketServer } from "@electric-sql/pglite-socket";

const toolingDirectory = path.dirname(fileURLToPath(import.meta.url));
const repositoryRoot = path.resolve(toolingDirectory, "../..");
const serviceDirectory = path.join(repositoryRoot, "services", "auth-service");
const python = process.env.PYTHON || "python";

const portProbe = createServer();
await new Promise((resolve, reject) => {
  portProbe.once("error", reject);
  portProbe.listen(0, "127.0.0.1", resolve);
});
const port = portProbe.address().port;
await new Promise((resolve, reject) => {
  portProbe.close((error) => (error ? reject(error) : resolve()));
});

const database = await PGlite.create();
const server = new PGLiteSocketServer({ db: database, host: "127.0.0.1", port });

try {
  await server.start();
  const databaseUrl = `postgresql://postgres:postgres@127.0.0.1:${port}/postgres`;
  const child = spawn(
    python,
    ["-m", "unittest", "test_database_permissions.AuthDatabaseMigrationTest", "-v"],
    {
      cwd: serviceDirectory,
      env: {
        ...process.env,
        AUTH_TEST_ADMIN_DATABASE_URL: databaseUrl,
        AUTH_TEST_RUNTIME_DATABASE_URL: databaseUrl.replace(
          "postgres:postgres@",
          "acadence_auth_runtime:postgres@",
        ),
        MIGRATION_DATABASE_URL: databaseUrl
          .replace("postgresql://", "postgresql+psycopg://")
          .replace("postgres:postgres@", "acadence_auth_migrator:postgres@"),
      },
      stdio: "inherit",
    },
  );
  const exitCode = await new Promise((resolve, reject) => {
    child.once("error", reject);
    child.once("exit", resolve);
  });
  if (exitCode !== 0) process.exitCode = exitCode ?? 1;
} finally {
  await server.stop();
  await database.close();
}

import assert from "node:assert/strict";
import { arrayMove } from "@dnd-kit/sortable";
import { PGlite } from "@electric-sql/pglite";
import { generateHTML, generateJSON } from "@tiptap/html";
import StarterKit from "@tiptap/starter-kit";
import { JSDOM } from "jsdom";

const pages = ["Cover page", "Declaration", "Abstract"];
assert.deepEqual(arrayMove(pages, 0, 2), ["Declaration", "Abstract", "Cover page"]);
assert.deepEqual(pages, ["Cover page", "Declaration", "Abstract"]);
const editorInput = '<h2>Methodology</h2><p>The student used a <strong>reading diary</strong>.</p>';
assert.equal(generateHTML(generateJSON(editorInput, [StarterKit]), [StarterKit]), editorInput);
console.log("PASS: Tiptap/ProseMirror HTML round-trip and dnd-kit immutable page order.");

const { window } = new JSDOM("");
globalThis.window = window;
globalThis.document = window.document;
const { default: mermaid } = await import("mermaid");
const { default: createDOMPurify } = await import("dompurify");
mermaid.initialize({ startOnLoad: false, securityLevel: "strict", flowchart: { htmlLabels: false } });
const parsed = await mermaid.parse('flowchart TD\n  A["Select template"] --> B["Confirm facts"]');
assert.match(parsed.diagramType, /flowchart/);
assert.equal(await mermaid.parse("flowchart TD\n A -->", { suppressErrors: true }), false);
const sanitize = createDOMPurify(window);
const clean = sanitize.sanitize('<svg xmlns="http://www.w3.org/2000/svg"><title>Sample</title><rect width="10" height="10" onload="fixture()"/></svg>', {
  USE_PROFILES: { svg: true, svgFilters: true },
  FORBID_TAGS: ["foreignObject", "script", "a", "image"],
  FORBID_ATTR: ["href", "xlink:href"],
});
assert.match(clean, /<rect/);
assert.doesNotMatch(clean, /onload/);
window.close();
console.log("PASS: Mermaid strict configuration and valid/invalid parsing; fixture SVG sanitizer.");

const db = await PGlite.create();
try {
  await db.exec(`
    CREATE ROLE p00_auth;
    CREATE ROLE p00_project;
    CREATE SCHEMA auth AUTHORIZATION p00_auth;
    CREATE SCHEMA project AUTHORIZATION p00_project;
    SET ROLE p00_auth;
    CREATE TABLE auth.users (id int PRIMARY KEY);
    INSERT INTO auth.users VALUES (1);
    RESET ROLE;
    SET ROLE p00_project;
    CREATE TABLE project.facts (id int PRIMARY KEY);
    INSERT INTO project.facts VALUES (2);
  `);
  assert.deepEqual((await db.query("SELECT * FROM project.facts")).rows, [{ id: 2 }]);
  await assert.rejects(db.query("SELECT * FROM auth.users"), { code: "42501" });
  await assert.rejects(db.query("INSERT INTO auth.users VALUES (3)"), { code: "42501" });
  await db.exec("RESET ROLE; SET ROLE p00_auth");
  assert.deepEqual((await db.query("SELECT * FROM auth.users")).rows, [{ id: 1 }]);
  await assert.rejects(db.query("SELECT * FROM project.facts"), { code: "42501" });
} finally {
  await db.close();
}
console.log("PASS: PostgreSQL roles in PGlite can read/write their own schemas; cross-schema access denied.");

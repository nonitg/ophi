#!/usr/bin/env node
// Render the waitlist welcome note to outputs/site-email/ for review; sends nothing.
import { createRequire } from "node:module";
import { mkdirSync, writeFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";

const site = fileURLToPath(new URL("../site/", import.meta.url));
// jiti is a transitive dependency; pnpm keeps those in its hidden hoist folder.
const jitiPath = createRequire(`${site}node_modules/.pnpm/node_modules/`).resolve("jiti");
const { createJiti } = await import(pathToFileURL(jitiPath).href);
const jiti = createJiti(import.meta.url, { alias: { "@": site } });
const { confirmationEmail } = await jiti.import(`${site}lib/confirmation-email.ts`);
const email = confirmationEmail("preview@example.com");
const out = fileURLToPath(new URL("../outputs/site-email/", import.meta.url));
mkdirSync(out, { recursive: true });
writeFileSync(`${out}welcome.html`, email.html);
writeFileSync(`${out}welcome.txt`, `Subject: ${email.subject}\n\n${email.text}`);
console.log(`${out}welcome.html`);

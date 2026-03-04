// @ts-expect-error Bun resolves HTML imports
import indexHtml from "../public/index.html";

const server = Bun.serve({
  port: 5173,
  routes: { "/": indexHtml },
  development: true,
});

console.log(`Frontend dev server: http://localhost:${server.port}`);

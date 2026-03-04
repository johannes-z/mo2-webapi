export type HttpMethod = "GET" | "POST" | "PATCH" | "PUT" | "DELETE";

export interface DocBlock {
  title: string;
  content: string;
}

export interface EndpointDef {
  method: HttpMethod;
  path: string;
  body?: string;
  docs: (string | DocBlock)[];
}

export interface SectionDef {
  title: string;
  endpoints: EndpointDef[];
}

export const sections: SectionDef[] = [
  {
    title: "Health",
    endpoints: [
      {
        method: "GET",
        path: "/health",
        body: "",
        docs: [
          {
            title: "Response",
            content: '{"status": "ok", "version": "1.0.0"}',
          },
        ],
      },
    ],
  },
  {
    title: "Mods – List & query",
    endpoints: [
      {
        method: "GET",
        path: "/mods",
        docs: [
          "All installed mods with full info.",
          {
            title: "Response",
            content:
              '[{ "name", "isEnabled", "version", "priority", "nexusId", "categories", "conflicts", "meta", ... }]',
          },
        ],
      },
      {
        method: "GET",
        path: "/mods/list",
        docs: [
          "Lightweight list: name, isEnabled, priority only.",
          {
            title: "Response",
            content: '[{ "name", "isEnabled", "priority" }]',
          },
        ],
      },
      { method: "GET", path: "/mods/enabled", docs: ["Enabled mods only."] },
      { method: "GET", path: "/mods/disabled", docs: ["Disabled mods only."] },
      {
        method: "GET",
        path: "/mods/priority",
        docs: [{ title: "Response", content: '[{ "name", "priority" }]' }],
      },
      {
        method: "GET",
        path: "/mods/search?q=skyui",
        docs: [
          "Search by name (case-insensitive).",
          { title: "Query", content: "q (required): string" },
        ],
      },
      {
        method: "GET",
        path: "/mods/:modname",
        docs: [
          "Single mod info.",
          {
            title: "Response",
            content: '{ "name", "isEnabled", "version", "priority", "conflicts", "meta", ... }',
          },
          { title: "Error 404", content: '{"error": "Mod \'...\' not found"}' },
        ],
      },
      {
        method: "GET",
        path: "/mods/meta",
        docs: [
          "All mods' custom metadata (key-value).",
          {
            title: "Response",
            content: '{"ModName": {"key": "value", ...}, ...}',
          },
        ],
      },
    ],
  },
  {
    title: "Mods – Conflicts",
    endpoints: [
      {
        method: "GET",
        path: "/mods/conflicts",
        docs: [
          "Conflict summaries for all mods. Use ?refresh=true to force recompute.",
          { title: "Query", content: "refresh (optional): true | 1" },
          {
            title: "Response",
            content:
              '{"ModName": { "overwriting", "overridden", "overwritingMods", "overriddenByMods" }, ...}',
          },
        ],
      },
      {
        method: "GET",
        path: "/mods/:modname/conflicts",
        docs: [
          "File-level conflicts for one mod. ?refresh=true to recompute cache.",
          {
            title: "Response",
            content:
              '{ "winning": [{ "file", "overwriting" }], "losing": [{ "file", "overwrittenBy" }], "winningCount", "losingCount" }',
          },
        ],
      },
    ],
  },
  {
    title: "Mods – State",
    endpoints: [
      {
        method: "PATCH",
        path: "/mods/enable",
        body: '{"name": "ModName"}',
        docs: [{ title: "Request", content: '{"name": "ModName"}' }],
      },
      {
        method: "PATCH",
        path: "/mods/disable",
        body: '{"name": "ModName"}',
        docs: [{ title: "Request", content: '{"name": "ModName"}' }],
      },
      {
        method: "PATCH",
        path: "/mods/toggle",
        body: '{"name": "ModName"}',
        docs: [{ title: "Request", content: '{"name": "ModName"}' }],
      },
      {
        method: "PATCH",
        path: "/mods/state",
        body: '[{"name": "ModA", "state": true}]',
        docs: [
          {
            title: "Request",
            content: '[{"name": "ModA", "state": true}, {"name": "ModB", "state": false}]',
          },
        ],
      },
      {
        method: "PATCH",
        path: "/mods/set-priority",
        body: '{"name": "ModName", "priority": 0}',
        docs: [{ title: "Request", content: '{"name": "ModName", "priority": 0}' }],
      },
      {
        method: "PATCH",
        path: "/mods/:modname/rename",
        body: '{"newName": "NewModName"}',
        docs: [{ title: "Request", content: '{"newName": "NewModName"}' }],
      },
      {
        method: "DELETE",
        path: "/mods/:modname",
        docs: ["Uninstall/remove mod. 200 empty body."],
      },
      {
        method: "PATCH",
        path: "/mods/enable-batch",
        body: '{"names": ["ModA", "ModB"]}',
        docs: [{ title: "Request", content: '{"names": ["ModA", "ModB"]}' }],
      },
      {
        method: "PATCH",
        path: "/mods/disable-batch",
        body: '{"names": ["ModA", "ModB"]}',
        docs: [{ title: "Request", content: '{"names": ["ModA", "ModB"]}' }],
      },
    ],
  },
  {
    title: "Mods – Metadata",
    endpoints: [
      {
        method: "GET",
        path: "/mods/:modname/meta",
        docs: [{ title: "Response", content: '{"key": "value", ...}' }],
      },
      {
        method: "GET",
        path: "/mods/:modname/meta/:key",
        docs: [{ title: "Response", content: '{"mod", "key", "value"}' }],
      },
      {
        method: "PATCH",
        path: "/mods/:modname/meta",
        body: '{"data": {"key1": "value1"}}',
        docs: [
          {
            title: "Request",
            content: '{"data": {"key1": "value1", "key2": "value2"}}',
          },
        ],
      },
      {
        method: "PUT",
        path: "/mods/:modname/meta/:key",
        body: '{"value": "value1"}',
        docs: [{ title: "Request", content: '{"value": "string or number"}' }],
      },
      {
        method: "DELETE",
        path: "/mods/:modname/meta/:key",
        docs: ["Remove one key. 200 empty body."],
      },
    ],
  },
  {
    title: "Profile",
    endpoints: [
      {
        method: "GET",
        path: "/profile",
        docs: [{ title: "Response", content: '{"name": "Default"}' }],
      },
      {
        method: "GET",
        path: "/profiles",
        docs: [
          {
            title: "Response",
            content: '{"current": "Default", "profiles": ["Default", "Other"]}',
          },
        ],
      },
      {
        method: "GET",
        path: "/profiles/:profile_name",
        docs: [
          "Mod list for that profile (from modlist.txt).",
          {
            title: "Response",
            content: '{"name", "isCurrent", "mods": [{ "name", "isEnabled", "priority" }]}',
          },
        ],
      },
      {
        method: "POST",
        path: "/profiles/:profile_name/activate",
        docs: [
          "Not supported by mobase API. Returns 501.",
          {
            title: "Response 501",
            content: '{"error": "...", "hint": "Profile changes must be made through the MO2 UI"}',
          },
        ],
      },
    ],
  },
];

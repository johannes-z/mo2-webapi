import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
	plugins: [react()],
	base: "/api-docs/",
	build: {
		outDir: "dist",
	},
});

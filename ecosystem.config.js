const path = require("path");
const ROOT = __dirname;

const BACKEND_PORT = process.env.BACKEND_PORT || "8000";
const FRONTEND_PORT = process.env.FRONTEND_PORT || "3000";
const ADMIN_PORT = process.env.ADMIN_PORT || "3001";
const OLLAMA_MODEL = process.env.OLLAMA_MODEL || "qwen2.5:7b";

module.exports = {
  apps: [
    {
      name: "uzum-frontend",
      cwd: path.join(ROOT, "frontend"),
      script: "node_modules/next/dist/bin/next",
      args: `dev -p ${FRONTEND_PORT}`,
      interpreter: "node",
    },
    {
      name: "uzum-admin",
      cwd: path.join(ROOT, "admin"),
      script: "node_modules/next/dist/bin/next",
      args: `dev -p ${ADMIN_PORT}`,
      interpreter: "node",
    },
    {
      name: "uzum-backend",
      cwd: path.join(ROOT, "backend"),
      script: process.platform === "win32" ? "venv/Scripts/python.exe" : "venv/bin/python",
      args: `-m uvicorn app.main:app --reload --host 0.0.0.0 --port ${BACKEND_PORT}`,
      interpreter: "none",
      env: {
        OLLAMA_MODEL: OLLAMA_MODEL,
        PYTHONIOENCODING: "utf-8",
      },
    },
  ],
};

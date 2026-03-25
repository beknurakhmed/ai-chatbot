module.exports = {
  apps: [
    {
      name: "aut-frontend",
      cwd: "C:/Users/Victus/Desktop/ai-chatbot/frontend",
      script: "node_modules/next/dist/bin/next",
      args: "dev",
      interpreter: "node",
      env: {
        NEXT_PUBLIC_API_URL: "http://localhost:8000",
      },
    },
    {
      name: "aut-backend",
      cwd: "C:/Users/Victus/Desktop/ai-chatbot/backend",
      script: "venv/Scripts/python.exe",
      args: "-m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000",
      interpreter: "none",
      env: {
        OLLAMA_MODEL: "qwen2.5:7b",
        PYTHONIOENCODING: "utf-8",
      },
    },
  ],
};

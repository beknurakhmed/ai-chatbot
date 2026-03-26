"use client";

import { useEffect, useRef, useCallback } from "react";
import { useAppStore } from "@/lib/store";

const WS_URL = process.env.NEXT_PUBLIC_API_URL
  ? process.env.NEXT_PUBLIC_API_URL.replace(/^http/, "ws") + "/ws/face"
  : "ws://localhost:8000/ws/face";

const FRAME_INTERVAL = 1000; // send a frame every 1s (GPU)

export interface FaceResult {
  detected: boolean;
  name: string | null;
  age: number | null;
  gender: string | null;
  expression: string | null;
  lookalike: string | null;
  bbox: number[] | null;
}

export function useFaceWS(videoRef: React.RefObject<HTMLVideoElement | null>) {
  const wsRef = useRef<WebSocket | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const setFaceAttributes = useAppStore((s) => s.setFaceAttributes);
  const lastResultRef = useRef<FaceResult>({ detected: false, name: null, age: null, gender: null, expression: null, lookalike: null, bbox: null });
  const lastFaceSeenRef = useRef(0); // timestamp of last positive detection

  // Capture frame from video as base64 JPEG
  const captureFrame = useCallback((): string | null => {
    const video = videoRef.current;
    if (!video || video.readyState < 2) return null;

    if (!canvasRef.current) {
      canvasRef.current = document.createElement("canvas");
    }
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;
    ctx.drawImage(video, 0, 0);
    return canvas.toDataURL("image/jpeg", 0.7);
  }, [videoRef]);

  // Connect WebSocket
  useEffect(() => {
    let ws: WebSocket;
    let reconnectTimeout: ReturnType<typeof setTimeout>;

    function connect() {
      ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        // Start sending frames
        if (intervalRef.current) clearInterval(intervalRef.current);
        intervalRef.current = setInterval(() => {
          if (ws.readyState !== WebSocket.OPEN) return;
          const frame = captureFrame();
          if (frame) {
            ws.send(JSON.stringify({ action: "analyze", frame }));
          }
        }, FRAME_INTERVAL);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as FaceResult;

          if (data.detected) {
            lastFaceSeenRef.current = Date.now();
            lastResultRef.current = data;
            setFaceAttributes({
              age: data.age,
              gender: data.gender,
              expression: data.expression,
              expressionScore: data.expression && data.expression !== "neutral" ? 0.9 : 0,
              lookalike: data.lookalike,
            });
          } else {
            // Still consider face "present" if seen within last 5 seconds
            // (InsightFace on CPU can be slow, avoid false negatives)
            const recentlySeen = Date.now() - lastFaceSeenRef.current < 2000;
            lastResultRef.current = { ...data, detected: recentlySeen };
            if (!recentlySeen) {
              setFaceAttributes({ age: null, gender: null, expression: null, expressionScore: 0 });
            }
          }
        } catch { /* ignore */ }
      };

      ws.onclose = () => {
        if (intervalRef.current) clearInterval(intervalRef.current);
        // Reconnect after 3s
        reconnectTimeout = setTimeout(connect, 3000);
      };

      ws.onerror = () => {
        ws.close();
      };
    }

    connect();

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      clearTimeout(reconnectTimeout);
      if (wsRef.current) wsRef.current.close();
    };
  }, [captureFrame, setFaceAttributes]);

  // Register a new face
  const registerFace = useCallback(async (name: string): Promise<boolean> => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return false;
    const frame = captureFrame();
    if (!frame) return false;

    return new Promise((resolve) => {
      const handler = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          if ("registered" in data) {
            ws.removeEventListener("message", handler);
            resolve(!!data.registered);
          }
        } catch {
          resolve(false);
        }
      };
      ws.addEventListener("message", handler);
      ws.send(JSON.stringify({ action: "register", frame, name }));

      // Timeout after 5s
      setTimeout(() => {
        ws.removeEventListener("message", handler);
        resolve(false);
      }, 5000);
    });
  }, [captureFrame]);

  return { lastResult: lastResultRef, registerFace };
}

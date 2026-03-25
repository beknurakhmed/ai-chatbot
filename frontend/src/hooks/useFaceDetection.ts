import { useRef, useState, useCallback, useEffect } from "react";
import { useAppStore } from "@/lib/store";
import { t } from "@/i18n";

interface KnownFace {
  name: string;
  descriptor: Float32Array;
}

// Store known faces in memory (in production, save to backend)
const knownFaces: KnownFace[] = [];

let faceapi: typeof import("@vladmandic/face-api") | null = null;
let modelsLoaded = false;

async function loadFaceApi() {
  if (faceapi) return faceapi;
  faceapi = await import("@vladmandic/face-api");

  if (!modelsLoaded) {
    const MODEL_URL = "/models";
    await Promise.all([
      faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
      faceapi.nets.faceLandmark68TinyNet.loadFromUri(MODEL_URL),
      faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL),
    ]);
    modelsLoaded = true;
  }

  return faceapi;
}

export function useFaceDetection() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [isActive, setIsActive] = useState(false);
  const [detectedName, setDetectedName] = useState<string | null>(null);
  const setUserName = useAppStore((s) => s.setUserName);
  const setMood = useAppStore((s) => s.setMood);
  const addMessage = useAppStore((s) => s.addMessage);
  const locale = useAppStore((s) => s.locale);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: "user" },
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      await loadFaceApi();
      setIsActive(true);
    } catch (err) {
      console.error("Camera error:", err);
    }
  }, []);

  const stopCamera = useCallback(() => {
    if (videoRef.current?.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach((track) => track.stop());
      videoRef.current.srcObject = null;
    }
    if (intervalRef.current) clearInterval(intervalRef.current);
    setIsActive(false);
  }, []);

  const detectFace = useCallback(async () => {
    if (!videoRef.current || !faceapi || !isActive) return;

    const detection = await faceapi
      .detectSingleFace(videoRef.current, new faceapi.TinyFaceDetectorOptions())
      .withFaceLandmarks(true)
      .withFaceDescriptor();

    if (!detection) return;

    const descriptor = detection.descriptor;

    // Check against known faces
    let bestMatch: { name: string; distance: number } | null = null;

    for (const known of knownFaces) {
      const distance = faceapi.euclideanDistance(descriptor, known.descriptor);
      if (distance < 0.5 && (!bestMatch || distance < bestMatch.distance)) {
        bestMatch = { name: known.name, distance };
      }
    }

    if (bestMatch) {
      setDetectedName(bestMatch.name);
      setUserName(bestMatch.name);
      setMood("greeting");
      addMessage({
        role: "assistant",
        content: t(locale, "face.recognized", {
          name: bestMatch.name,
          count: "3",
        }),
        mood: "greeting",
      });
    }

    return detection;
  }, [isActive, setUserName, setMood, addMessage, locale]);

  const registerFace = useCallback(
    async (name: string) => {
      if (!videoRef.current || !faceapi) return false;

      const detection = await faceapi
        .detectSingleFace(videoRef.current, new faceapi.TinyFaceDetectorOptions())
        .withFaceLandmarks(true)
        .withFaceDescriptor();

      if (!detection) return false;

      knownFaces.push({ name, descriptor: detection.descriptor });
      setDetectedName(name);
      setUserName(name);
      return true;
    },
    [setUserName]
  );

  // Auto-detect every 3 seconds when camera is active
  useEffect(() => {
    if (isActive) {
      intervalRef.current = setInterval(detectFace, 3000);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isActive, detectFace]);

  return {
    videoRef,
    isActive,
    detectedName,
    startCamera,
    stopCamera,
    detectFace,
    registerFace,
  };
}

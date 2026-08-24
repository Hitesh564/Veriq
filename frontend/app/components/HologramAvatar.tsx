"use client";

import React, { useEffect, useRef } from "react";
import * as THREE from "three";

export type VoiceState =
  | "DISCONNECTED"
  | "CONNECTING"
  | "AI_SPEAKING"
  | "LISTENING"
  | "TRANSCRIBING"
  | "THINKING"
  | "ENDED";

interface HologramAvatarProps {
  voiceState: VoiceState;
  className?: string;
}

export default function HologramAvatar({ voiceState, className }: HologramAvatarProps) {
  const mountRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth || 320;
    const height = container.clientHeight || 320;

    // 1. THREE.JS SCENE SETUP
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 0, 4.2);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.3;

    container.innerHTML = "";
    container.appendChild(renderer.domElement);

    // 2. LIGHTING
    const ambientLight = new THREE.AmbientLight(0x061124, 2.5);
    scene.add(ambientLight);

    const mainLight = new THREE.PointLight(0x00f2fe, 6.0, 15);
    mainLight.position.set(2, 3, 4);
    scene.add(mainLight);

    const subLight = new THREE.PointLight(0xa855f7, 4.0, 15);
    subLight.position.set(-3, -2, 2);
    scene.add(subLight);

    // 3. CENTRAL GLOWING CORE SPHERE
    const coreGroup = new THREE.Group();
    scene.add(coreGroup);

    const coreGeo = new THREE.SphereGeometry(0.72, 48, 48);
    const coreMat = new THREE.MeshStandardMaterial({
      color: 0x030712,
      emissive: 0x00f2fe,
      emissiveIntensity: 0.65,
      roughness: 0.1,
      metalness: 0.9,
    });
    const coreMesh = new THREE.Mesh(coreGeo, coreMat);
    coreGroup.add(coreMesh);

    // Glass Refraction Shell
    const shellGeo = new THREE.SphereGeometry(0.82, 32, 32);
    const shellMat = new THREE.MeshPhysicalMaterial({
      color: 0x00f2fe,
      transparent: true,
      opacity: 0.35,
      roughness: 0.1,
      transmission: 0.85,
      ior: 1.4,
    });
    const shellMesh = new THREE.Mesh(shellGeo, shellMat);
    coreGroup.add(shellMesh);

    // 4. 3D OPTICAL ILLUSION PARTICLE SPHERE SYSTEM (1200+ Particles)
    const particleCount = 1200;
    const particleGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const basePositions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    const scales = new Float32Array(particleCount);

    const colorCyan = new THREE.Color(0x00f2fe);

    for (let i = 0; i < particleCount; i++) {
      // Golden spiral distribution over a 3D sphere surface
      const phi = Math.acos(1 - 2 * (i / particleCount));
      const theta = Math.PI * (1 + Math.sqrt(5)) * i;
      const radius = 1.1 + Math.random() * 0.15;

      const x = radius * Math.sin(phi) * Math.cos(theta);
      const y = radius * Math.sin(phi) * Math.sin(theta);
      const z = radius * Math.cos(phi);

      positions[i * 3] = x;
      positions[i * 3 + 1] = y;
      positions[i * 3 + 2] = z;

      basePositions[i * 3] = x;
      basePositions[i * 3 + 1] = y;
      basePositions[i * 3 + 2] = z;

      colors[i * 3] = colorCyan.r;
      colors[i * 3 + 1] = colorCyan.g;
      colors[i * 3 + 2] = colorCyan.b;

      scales[i] = Math.random() * 0.04 + 0.02;
    }

    particleGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    particleGeo.setAttribute("color", new THREE.BufferAttribute(colors, 3));

    // Particle Texture Generator
    const createParticleTexture = () => {
      const pCanvas = document.createElement("canvas");
      pCanvas.width = 64;
      pCanvas.height = 64;
      const pCtx = pCanvas.getContext("2d")!;
      const grad = pCtx.createRadialGradient(32, 32, 0, 32, 32, 32);
      grad.addColorStop(0, "rgba(255, 255, 255, 1)");
      grad.addColorStop(0.4, "rgba(0, 242, 254, 0.8)");
      grad.addColorStop(1, "rgba(0, 0, 0, 0)");
      pCtx.fillStyle = grad;
      pCtx.fillRect(0, 0, 64, 64);
      return new THREE.CanvasTexture(pCanvas);
    };

    const particleMat = new THREE.PointsMaterial({
      size: 0.06,
      map: createParticleTexture(),
      transparent: true,
      blending: THREE.AdditiveBlending,
      vertexColors: true,
      depthWrite: false,
    });

    const particleSystem = new THREE.Points(particleGeo, particleMat);
    coreGroup.add(particleSystem);

    // 5. VOLUMETRIC SOUNDWAVE ENERGY RINGS
    const shockwaveRings: THREE.Mesh[] = [];
    for (let r = 0; r < 3; r++) {
      const ringGeo = new THREE.TorusGeometry(1.0 + r * 0.25, 0.015, 16, 80);
      const ringMat = new THREE.MeshBasicMaterial({
        color: 0x00f2fe,
        transparent: true,
        opacity: 0.5 - r * 0.12,
        blending: THREE.AdditiveBlending,
      });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.rotation.x = Math.PI / 3;
      scene.add(ring);
      shockwaveRings.push(ring);
    }

    // Outer Cyber Orbital Ring
    const orbitGeo = new THREE.TorusGeometry(1.65, 0.012, 16, 100);
    const orbitMat = new THREE.MeshBasicMaterial({
      color: 0x00f2fe,
      transparent: true,
      opacity: 0.6,
      blending: THREE.AdditiveBlending,
    });
    const orbitRing = new THREE.Mesh(orbitGeo, orbitMat);
    scene.add(orbitRing);

    // 6. ANIMATION LOOP WITH 3D OPTICAL MOTION & AUDIO WAVES
    let time = 0;
    let animId: number;

    const animate = () => {
      time += 0.025;

      const isSpeaking = voiceState === "AI_SPEAKING";
      const isThinking = voiceState === "THINKING" || voiceState === "TRANSCRIBING";
      const isListening = voiceState === "LISTENING";

      // Core 3D Group Rotation & Wobble
      coreGroup.rotation.y = time * (isSpeaking ? 0.8 : 0.4);
      coreGroup.rotation.x = Math.sin(time * 0.6) * 0.15;
      coreGroup.rotation.z = Math.cos(time * 0.4) * 0.1;

      // Orbit Ring Rotation
      orbitRing.rotation.z = isThinking ? time * 2.5 : time * 0.6;
      orbitRing.rotation.y = Math.sin(time * 0.5) * 0.3;

      // Dynamic Particle Morphing & Noise Waves
      const posArr = particleGeo.attributes.position.array as Float32Array;
      const speechAmp = isSpeaking ? Math.sin(time * 12) * 0.18 + Math.cos(time * 18) * 0.1 + 0.15 : 0.02;

      for (let i = 0; i < particleCount; i++) {
        const bx = basePositions[i * 3];
        const by = basePositions[i * 3 + 1];
        const bz = basePositions[i * 3 + 2];

        // Harmonic wave displacement
        const wave = Math.sin(time * 4 + bx * 3 + by * 2) * (0.08 + speechAmp);
        const factor = 1.0 + wave;

        posArr[i * 3] = bx * factor;
        posArr[i * 3 + 1] = by * factor;
        posArr[i * 3 + 2] = bz * factor;
      }
      particleGeo.attributes.position.needsUpdate = true;

      // Expand & Pulse Volumetric Shockwave Rings when AI is Speaking
      shockwaveRings.forEach((ring, idx) => {
        if (isSpeaking) {
          const ringScale = 1.0 + ((time * 2 + idx * 0.6) % 1.5) * 0.4;
          ring.scale.set(ringScale, ringScale, ringScale);
          (ring.material as THREE.MeshBasicMaterial).opacity = Math.max(0, 0.8 - (ringScale - 1.0) * 1.5);
        } else {
          ring.scale.set(1.0, 1.0, 1.0);
          (ring.material as THREE.MeshBasicMaterial).opacity = 0.3 - idx * 0.08;
        }
      });

      // State-Based Theme Colors
      let targetHex = 0x00f2fe; // Cyan default
      if (isListening) {
        targetHex = 0x10b981; // Emerald Green
      } else if (isThinking) {
        targetHex = 0xa855f7; // Deep Purple
      }

      coreMat.emissive.setHex(targetHex);
      shellMat.color.setHex(targetHex);
      orbitMat.color.setHex(targetHex);
      mainLight.color.setHex(targetHex);

      renderer.render(scene, camera);
      animId = requestAnimationFrame(animate);
    };

    animate();

    // Cleanup on unmount
    return () => {
      cancelAnimationFrame(animId);
      renderer.dispose();
      coreGeo.dispose();
      coreMat.dispose();
      shellGeo.dispose();
      shellMat.dispose();
      particleGeo.dispose();
      particleMat.dispose();
      orbitGeo.dispose();
      orbitMat.dispose();
      container.innerHTML = "";
    };
  }, [voiceState]);

  return (
    <div className={`w-full h-full flex items-center justify-center ${className || ""}`}>
      <div
        ref={mountRef}
        className="w-[300px] h-[300px] max-w-full max-h-full drop-shadow-[0_0_35px_rgba(0,242,254,0.5)] transition-all duration-500"
      />
    </div>
  );
}

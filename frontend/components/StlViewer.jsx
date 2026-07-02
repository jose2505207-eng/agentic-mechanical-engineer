"use client";

import { Suspense } from "react";
import { Canvas, useLoader } from "@react-three/fiber";
import { OrbitControls, Center, Grid } from "@react-three/drei";
import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";

function Model({ url }) {
  const geometry = useLoader(STLLoader, url);
  return (
    <Center>
      {/* CAD is z-up; three.js is y-up */}
      <mesh geometry={geometry} rotation={[-Math.PI / 2, 0, 0]}>
        <meshStandardMaterial color="#7aa2c4" metalness={0.35} roughness={0.45} />
      </mesh>
    </Center>
  );
}

export default function StlViewer({ url }) {
  return (
    <div className="viewer">
      <Canvas camera={{ position: [450, 350, 450], fov: 45, near: 1, far: 5000 }}>
        <ambientLight intensity={0.5} />
        <directionalLight position={[400, 600, 300]} intensity={1.2} />
        <directionalLight position={[-300, 200, -300]} intensity={0.4} />
        <Suspense fallback={null}>
          <Model url={url} />
        </Suspense>
        <Grid args={[2000, 2000]} cellSize={50} sectionSize={250}
          cellColor="#22272e" sectionColor="#30363d" position={[0, -80, 0]}
          fadeDistance={1800} infiniteGrid />
        <OrbitControls makeDefault />
      </Canvas>
    </div>
  );
}

import * as THREE from "three";
import { useEffect, useRef } from "react";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls";

export default function VolumeBox({ volume }) {
  const ref = useRef();
  useEffect(() => {
    if (!ref.current) return;
    const width = 600, depth = 600;
    const height = Math.max(Math.abs(volume) * 0.1, 1);
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf0f0f0);
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 2000);
    camera.position.set(0, 400, 800);
    camera.lookAt(0, height / 2, 0);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setClearColor(0xf0f0f0);
    renderer.setSize(width, width);
    ref.current.innerHTML = "";
    ref.current.appendChild(renderer.domElement);

    const color = volume >= 0 ? 0x44aa44 : 0xaa4444;
    const geometry = new THREE.BoxGeometry(width, height, depth);
    const material = new THREE.MeshStandardMaterial({ color });

    const box = new THREE.Mesh(geometry, material);
    box.position.y = height / 2;
    scene.add(box);

    // Stronger lighting
    scene.add(new THREE.AmbientLight(0xffffff, 1.5));
    const light = new THREE.DirectionalLight(0xffffff, 1.5);
    light.position.set(100, 200, 100);
    scene.add(light);

    // Add orbit controls for interactive rotation
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.1;
    controls.target.set(0, height / 2, 0);
    controls.update();

    // Animate for controls
    function animate() {
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    }
    animate();
  }, [volume]);
  return <div ref={ref} style={{ width: 600, height: 600, marginTop: 20 }} />;
}

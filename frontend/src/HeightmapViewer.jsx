import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";

export default function HeightmapViewer({ heightmapUrl, metaUrl }){
  const mountRef = useRef();
  const [meta, setMeta] = useState(null);

  useEffect(() => {
    let mounted = true;
    if(metaUrl){
      fetch(metaUrl).then(r=>r.json()).then(j=>{ if(mounted) setMeta(j); }).catch(()=>{});
    }
    return ()=>{ mounted=false; }
  }, [metaUrl]);

  useEffect(() => {
    if(!heightmapUrl) return;
    const width = mountRef.current.clientWidth;
    const height = mountRef.current.clientHeight;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width/height, 0.1, 10000);
    camera.position.set(0, 200, 400);
    const renderer = new THREE.WebGLRenderer({antialias:true});
    renderer.setSize(width, height);
    mountRef.current.innerHTML = "";
    mountRef.current.appendChild(renderer.domElement);

    const light = new THREE.DirectionalLight(0xffffff, 1);
    light.position.set(100,200,100);
    scene.add(light);
    scene.add(new THREE.AmbientLight(0x666666));

    const loader = new THREE.TextureLoader();
    loader.setCrossOrigin("");
    loader.load(heightmapUrl, (tex) => {
      tex.wrapS = tex.wrapT = THREE.ClampToEdgeWrapping;
      const segs = meta && meta.width ? Math.max(meta.width - 1, 1) : 10;
      const planeWidth = meta && meta.width ? meta.width : 100;
      const planeHeight = meta && meta.height ? meta.height : 100;
      const geometry = new THREE.PlaneGeometry(planeWidth, planeHeight, segs, segs);
      // Use a more visible displacement scale for small DEMs
      const displacementScale = meta && meta.vmax !== undefined && meta.vmin !== undefined ? (meta.vmax - meta.vmin) * 0.5 : 20;
      const material = new THREE.MeshStandardMaterial({
        color: 0x999999,
        displacementMap: tex,
        displacementScale,
        side: THREE.DoubleSide,
      });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.rotation.x = -Math.PI/2;
      scene.add(mesh);

      const animate = function(){
        requestAnimationFrame(animate);
        renderer.render(scene, camera);
      }
      animate();
    });

    // cleanup
    return () => {
      renderer.dispose();
      mountRef.current.innerHTML = "";
    }
  }, [heightmapUrl, meta]);

  return <div ref={mountRef} style={{width:'100%', height:'100%'}} />;
}

import React, { useState } from "react";
import axios from "axios";
import HeightmapViewer from "./HeightmapViewer";
import VolumeBox from "./VolumeBox";

export default function App(){
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const upload = async () => {
    if(!file) return alert("Please select a GeoTIFF (.tif) file first.");
    setLoading(true);
    const fd = new FormData();
    fd.append("file", file);
    try{
      const res = await axios.post("http://localhost:8000/upload-dem/", fd, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setResult(res.data);
    }catch(err){
      alert("Upload failed: " + (err?.response?.data?.detail || err.message));
    }finally{
      setLoading(false);
    }
  }

  return (
    <div style={{padding:20, fontFamily:'sans-serif'}}>
      <h1>DEM Compare (MVP)</h1>
      <p>Upload a GeoTIFF DEM file. Backend will fetch a current DEM from OpenTopography and compute differences.</p>
      <input type="file" accept=".tif,.tiff" onChange={e=>setFile(e.target.files[0])} />
      <button onClick={upload} disabled={loading} style={{marginLeft:10}}>Upload & Analyze</button>
      {loading && <p>Processing... this may take a while for large files.</p>}
      {result && (
        <div style={{marginTop:20}}>
          <VolumeBox volume={result.volume_m3} />
        </div>
      )}
    </div>
  );
}

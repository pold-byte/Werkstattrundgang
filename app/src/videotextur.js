import * as THREE from 'three';

// Legt das 720p-Video als Textur auf das Mesh "Monitor_Bildschirm" (Namens-Vertrag
// mit Platzhalterszene und Blender-Export). Liefert false, wenn das Mesh fehlt.
export function verbindeVideoTextur(szene, videoEl) {
  const ziel = szene.getObjectByName('Monitor_Bildschirm');
  if (!ziel) return false;
  const textur = new THREE.VideoTexture(videoEl);
  textur.colorSpace = THREE.SRGBColorSpace; // Spec §5: sonst ausgewaschen
  textur.flipY = false; // glTF-UV-Konvention (V-Ursprung oben) — sonst steht das Video ab Task 11 kopf
  ziel.material = new THREE.MeshBasicMaterial({ map: textur });
  return true;
}

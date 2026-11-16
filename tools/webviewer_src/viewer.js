import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const manifest = JSON.parse(document.getElementById("pulmoslicer-manifest").textContent);
const canvas = document.getElementById("viewport");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, powerPreference: "high-performance" });
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.localClippingEnabled = true;
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.setClearColor(0x111820, 1);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 10000);
camera.position.set(350, 220, 420);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.screenSpacePanning = true;
controls.zoomToCursor = true;
scene.add(new THREE.HemisphereLight(0xffffff, 0x26384a, 2.2));
const keyLight = new THREE.DirectionalLight(0xffffff, 2.8);
keyLight.position.set(1, 2, 3);
scene.add(keyLight);
const fillLight = new THREE.DirectionalLight(0x9bc5ff, 1.2);
fillLight.position.set(-2, 0, -1);
scene.add(fillLight);

const root = new THREE.Group();
scene.add(root);
const meshes = new Map();
const nodeById = new Map(manifest.meshes.map(node => [node.id, node]));
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
const clippingPlanes = [
  new THREE.Plane(new THREE.Vector3(-1, 0, 0), 10000),
  new THREE.Plane(new THREE.Vector3(0, -1, 0), 10000),
  new THREE.Plane(new THREE.Vector3(0, 0, -1), 10000),
];
let selected = null;
let measureMode = false;
let measurePoints = [];
let orthographicCamera = null;
let activeCamera = camera;
let loadedTriangles = 0;
let startedAt = performance.now();

function toast(message, error = false) {
  const element = document.getElementById("toast");
  element.textContent = message;
  element.className = error ? "show error" : "show";
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => element.className = "", 4200);
}

function decodeBase64(value) {
  const text = atob(value.trim());
  const bytes = new Uint8Array(text.length);
  for (let index = 0; index < text.length; index += 1) bytes[index] = text.charCodeAt(index);
  return bytes;
}

const workerSource = `
self.onmessage = async event => {
  try {
    const text = atob(event.data.payload);
    const compressed = new Uint8Array(text.length);
    for (let i = 0; i < text.length; i += 1) compressed[i] = text.charCodeAt(i);
    if (event.data.expectedHash && self.crypto?.subtle) {
      const hash = new Uint8Array(await self.crypto.subtle.digest("SHA-256", compressed));
      const hex = [...hash].map(value => value.toString(16).padStart(2, "0")).join("");
      if (hex !== event.data.expectedHash) throw new Error("SHA-256 payload mismatch");
    }
    const stream = new Blob([compressed]).stream().pipeThrough(new DecompressionStream("gzip"));
    const buffer = await new Response(stream).arrayBuffer();
    self.postMessage({ id: event.data.id, buffer }, [buffer]);
  } catch (error) { self.postMessage({ id: event.data.id, error: error.message }); }
};`;
let decoderWorker = null;
const workerRequests = new Map();
try {
  decoderWorker = new Worker(URL.createObjectURL(new Blob([workerSource], { type: "text/javascript" })));
  decoderWorker.onmessage = event => {
    const request = workerRequests.get(event.data.id);
    if (!request) return;
    workerRequests.delete(event.data.id);
    if (event.data.error) request.reject(new Error(event.data.error));
    else request.resolve(new Uint8Array(event.data.buffer));
  };
  decoderWorker.onerror = error => {
    console.warn("Decoder worker failed; pending chunks will use main thread", error);
    decoderWorker = null;
  };
} catch (error) { console.warn("Worker unavailable; using main-thread decoder", error); }

async function gunzip(bytes) {
  if (!("DecompressionStream" in window)) throw new Error("Trình duyệt không hỗ trợ giải nén gzip");
  const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));
  return new Uint8Array(await new Response(stream).arrayBuffer());
}

async function verifyHash(bytes, expectedHash) {
  if (!expectedHash || !crypto?.subtle) return;
  const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
  const hex = [...digest].map(value => value.toString(16).padStart(2, "0")).join("");
  if (hex !== expectedHash) throw new Error("SHA-256 payload mismatch");
}

async function decodePayload(id, payload, expectedHash) {
  if (!decoderWorker) {
    const compressed = decodeBase64(payload);
    await verifyHash(compressed, expectedHash);
    return gunzip(compressed);
  }
  return new Promise((resolve, reject) => {
    const timer = setTimeout(async () => {
      if (!workerRequests.has(id)) return;
      workerRequests.delete(id);
      try {
        const compressed = decodeBase64(payload);
        await verifyHash(compressed, expectedHash);
        resolve(await gunzip(compressed));
      }
      catch (error) { reject(error); }
    }, 2500);
    workerRequests.set(id, {
      resolve: value => { clearTimeout(timer); resolve(value); },
      reject: error => { clearTimeout(timer); reject(error); },
    });
    decoderWorker.postMessage({ id, payload, expectedHash });
  });
}

async function decodeMesh(node) {
  const payload = document.getElementById(node.payloadId);
  if (!payload) throw new Error(`Thiếu payload ${node.id}`);
  const bytes = await decodePayload(node.id, payload.textContent.trim(), node.payloadSha256);
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const magic = new TextDecoder().decode(bytes.subarray(0, 5));
  if (magic !== "PS3D1") throw new Error(`Payload không hợp lệ: ${node.id}`);
  const vertexCount = view.getUint32(8, true);
  const indexCount = view.getUint32(12, true);
  const positionStart = 16;
  const indexStart = positionStart + vertexCount * 12;
  if (indexStart + indexCount * 4 !== bytes.byteLength) throw new Error(`Sai kích thước payload: ${node.id}`);
  const positions = new Float32Array(vertexCount * 3);
  for (let i = 0; i < positions.length; i += 1) positions[i] = view.getFloat32(positionStart + i * 4, true);
  const indices = new Uint32Array(indexCount);
  for (let i = 0; i < indices.length; i += 1) indices[i] = view.getUint32(indexStart + i * 4, true);
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setIndex(new THREE.BufferAttribute(indices, 1));
  geometry.computeVertexNormals();
  geometry.computeBoundingSphere();
  return geometry;
}

function createMaterial(node) {
  return new THREE.MeshStandardMaterial({
    color: new THREE.Color(...node.color),
    roughness: 0.68,
    metalness: 0.02,
    transparent: node.opacity < 0.999,
    opacity: node.opacity,
    side: THREE.DoubleSide,
    clippingPlanes,
    clipIntersection: false,
  });
}

function templateColor(templateId, anatomyClass) {
  const template = manifest.colorTemplates[templateId];
  if (!template) return null;
  const family = anatomyClass.startsWith("lobe_") ? "lung" : anatomyClass.split("_")[0];
  return template.colors[anatomyClass] || template.colors[family] || template.colors.other;
}

function applyTemplate(templateId) {
  manifest.colorTemplateId = templateId;
  manifest.meshes.forEach(node => {
    const rgba = templateColor(templateId, node.class);
    if (!rgba) return;
    node.color = rgba.slice(0, 3);
    node.opacity = rgba[3];
    const mesh = meshes.get(node.id);
    if (!mesh) return;
    mesh.material.color.setRGB(...node.color);
    mesh.material.opacity = node.opacity;
    mesh.material.transparent = node.opacity < 0.999;
    mesh.material.needsUpdate = true;
  });
  if (selected) selectById(selected.userData.nodeId);
}

async function loadNode(node) {
  if (meshes.has(node.id)) return meshes.get(node.id);
  updateBadge(node.id, "loading");
  try {
    const geometry = await decodeMesh(node);
    const mesh = new THREE.Mesh(geometry, createMaterial(node));
    mesh.name = node.name;
    mesh.userData.nodeId = node.id;
    mesh.visible = node.visible;
    root.add(mesh);
    meshes.set(node.id, mesh);
    loadedTriangles += node.triangleCount;
    updateBadge(node.id, "ready");
    updateDiagnostics();
    return mesh;
  } catch (error) {
    updateBadge(node.id, "error");
    console.error(error);
    toast(`${node.name}: ${error.message}`, true);
    return null;
  }
}

function setVisibility(id, visible) {
  const node = nodeById.get(id);
  if (!node) return;
  node.visible = visible;
  const mesh = meshes.get(id);
  if (mesh) mesh.visible = visible;
  else if (visible) loadNode(node);
  const checkbox = document.querySelector(`input[data-node-id="${CSS.escape(id)}"]`);
  if (checkbox) checkbox.checked = visible;
}

function setAll(mode) {
  manifest.meshes.forEach(node => setVisibility(node.id, mode === "invert" ? !node.visible : mode));
}

function isolate(id) {
  manifest.meshes.forEach(node => setVisibility(node.id, node.id === id));
  fitSelection(id);
}

function hierarchyModel() {
  const rootNode = { name: manifest.caseTitle, children: new Map(), nodes: [] };
  manifest.meshes.forEach(node => {
    let cursor = rootNode;
    node.path.forEach(part => {
      if (!cursor.children.has(part)) cursor.children.set(part, { name: part, children: new Map(), nodes: [] });
      cursor = cursor.children.get(part);
    });
    cursor.nodes.push(node);
  });
  return rootNode;
}

function renderTreeBranch(model, container) {
  model.children.forEach(child => {
    const details = document.createElement("details");
    details.open = true;
    const summary = document.createElement("summary");
    summary.textContent = child.name;
    details.appendChild(summary);
    const body = document.createElement("div");
    body.className = "tree-children";
    details.appendChild(body);
    renderTreeBranch(child, body);
    container.appendChild(details);
  });
  model.nodes.forEach(node => {
    const row = document.createElement("div");
    row.className = "tree-row";
    row.dataset.search = `${node.name} ${node.id} ${node.path.join(" ")}`.toLowerCase();
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = node.visible;
    checkbox.dataset.nodeId = node.id;
    checkbox.addEventListener("change", () => setVisibility(node.id, checkbox.checked));
    const label = document.createElement("button");
    label.className = "node-label";
    label.textContent = node.name;
    label.title = "Chọn; nhấp đúp để cô lập";
    label.addEventListener("click", () => selectById(node.id));
    label.addEventListener("dblclick", () => isolate(node.id));
    const badge = document.createElement("span");
    badge.id = `badge-${node.id}`;
    badge.className = "badge queued";
    badge.textContent = "queued";
    row.append(checkbox, label, badge);
    container.appendChild(row);
  });
}

function updateBadge(id, state) {
  const badge = document.getElementById(`badge-${id}`);
  if (!badge) return;
  badge.className = `badge ${state}`;
  badge.textContent = state;
}

function selectById(id) {
  if (selected?.material?.emissive) selected.material.emissive.setHex(0x000000);
  selected = meshes.get(id) || null;
  if (!selected) {
    loadNode(nodeById.get(id)).then(mesh => { if (mesh) selectById(id); });
    return;
  }
  if (selected.material.emissive) selected.material.emissive.setHex(0x302400);
  const node = nodeById.get(id);
  document.getElementById("selection-name").textContent = node.name;
  document.getElementById("selection-meta").textContent = `${node.path.join(" › ")} · ${node.triangleCount.toLocaleString()} triangles`;
  document.getElementById("opacity").value = Math.round(selected.material.opacity * 100);
  document.getElementById("node-color").value = `#${selected.material.color.getHexString()}`;
}

function fitObject(object) {
  const box = new THREE.Box3().setFromObject(object);
  if (box.isEmpty()) return;
  const sphere = box.getBoundingSphere(new THREE.Sphere());
  const direction = new THREE.Vector3().subVectors(activeCamera.position, controls.target).normalize();
  const distance = Math.max(sphere.radius * 2.7, 10);
  controls.target.copy(sphere.center);
  activeCamera.position.copy(sphere.center).addScaledVector(direction, distance);
  activeCamera.near = Math.max(distance / 1000, 0.05);
  activeCamera.far = distance * 20;
  activeCamera.updateProjectionMatrix();
  controls.update();
}

function fitSelection(id) {
  const mesh = meshes.get(id);
  if (mesh) fitObject(mesh);
}

function viewDirection(axis) {
  const box = new THREE.Box3().setFromObject(root);
  const sphere = box.getBoundingSphere(new THREE.Sphere());
  const directions = {
    A: [0, 0, 1], P: [0, 0, -1], L: [-1, 0, 0], R: [1, 0, 0], S: [0, 1, 0], I: [0, -1, 0],
  };
  const vector = new THREE.Vector3(...directions[axis]);
  controls.target.copy(sphere.center);
  activeCamera.position.copy(sphere.center).addScaledVector(vector, Math.max(sphere.radius * 2.8, 10));
  activeCamera.up.set(0, axis === "S" || axis === "I" ? 0 : 1, axis === "S" ? -1 : axis === "I" ? 1 : 0);
  activeCamera.lookAt(sphere.center);
  activeCamera.updateProjectionMatrix();
  controls.update();
}

function toggleProjection() {
  if (activeCamera.isPerspectiveCamera) {
    const distance = activeCamera.position.distanceTo(controls.target);
    const halfHeight = Math.max(distance * Math.tan(THREE.MathUtils.degToRad(camera.fov * 0.5)), 1);
    const aspect = canvas.clientWidth / Math.max(canvas.clientHeight, 1);
    orthographicCamera = new THREE.OrthographicCamera(-halfHeight * aspect, halfHeight * aspect, halfHeight, -halfHeight, 0.05, 10000);
    orthographicCamera.position.copy(camera.position);
    orthographicCamera.quaternion.copy(camera.quaternion);
    orthographicCamera.up.copy(camera.up);
    activeCamera = orthographicCamera;
  } else {
    camera.position.copy(activeCamera.position);
    camera.quaternion.copy(activeCamera.quaternion);
    camera.up.copy(activeCamera.up);
    activeCamera = camera;
  }
  controls.object = activeCamera;
  controls.update();
  document.getElementById("projection").textContent = activeCamera.isPerspectiveCamera ? "Perspective" : "Orthographic";
}

function pick(event) {
  const rect = canvas.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, activeCamera);
  return raycaster.intersectObjects([...meshes.values()].filter(mesh => mesh.visible), false)[0] || null;
}

function addMeasurePoint(point) {
  measurePoints.push(point.clone());
  if (measurePoints.length < 2) return;
  const [start, end] = measurePoints;
  const geometry = new THREE.BufferGeometry().setFromPoints([start, end]);
  const line = new THREE.Line(geometry, new THREE.LineBasicMaterial({ color: 0xffff33, depthTest: false }));
  line.renderOrder = 999;
  root.add(line);
  const distance = start.distanceTo(end);
  document.getElementById("measurement").textContent = `${distance.toFixed(1)} mm · exported surface, research/reference only`;
  measurePoints = [];
}

canvas.addEventListener("click", event => {
  const hit = pick(event);
  if (!hit) return;
  if (measureMode) addMeasurePoint(hit.point);
  else selectById(hit.object.userData.nodeId);
});

function bindUi() {
  renderTreeBranch(hierarchyModel(), document.getElementById("tree"));
  document.getElementById("show-all").onclick = () => setAll(true);
  document.getElementById("hide-all").onclick = () => setAll(false);
  document.getElementById("invert").onclick = () => setAll("invert");
  document.getElementById("fit-all").onclick = () => fitObject(root);
  document.getElementById("isolate").onclick = () => selected && isolate(selected.userData.nodeId);
  const templateSelect = document.getElementById("color-template");
  Object.entries(manifest.colorTemplates).forEach(([id, template]) => {
    const option = document.createElement("option");
    option.value = id;
    option.textContent = template.name;
    option.selected = id === manifest.colorTemplateId;
    templateSelect.appendChild(option);
  });
  templateSelect.onchange = () => applyTemplate(templateSelect.value);
  document.getElementById("reset-colors").onclick = () => applyTemplate(templateSelect.value);
  document.getElementById("projection").onclick = toggleProjection;
  document.querySelectorAll("[data-view]").forEach(button => button.onclick = () => viewDirection(button.dataset.view));
  document.getElementById("search").addEventListener("input", event => {
    const query = event.target.value.toLowerCase();
    document.querySelectorAll(".tree-row").forEach(row => row.hidden = !row.dataset.search.includes(query));
  });
  document.getElementById("opacity").addEventListener("input", event => {
    if (!selected) return;
    selected.material.opacity = Number(event.target.value) / 100;
    selected.material.transparent = selected.material.opacity < 0.999;
    selected.material.needsUpdate = true;
  });
  document.getElementById("node-color").addEventListener("input", event => selected?.material.color.set(event.target.value));
  document.getElementById("wireframe").addEventListener("change", event => meshes.forEach(mesh => mesh.material.wireframe = event.target.checked));
  document.getElementById("flat-shading").addEventListener("change", event => meshes.forEach(mesh => { mesh.material.flatShading = event.target.checked; mesh.material.needsUpdate = true; }));
  document.getElementById("autorotate").addEventListener("change", event => controls.autoRotate = event.target.checked);
  document.getElementById("measure").addEventListener("change", event => { measureMode = event.target.checked; measurePoints = []; });
  document.getElementById("theme").onclick = () => {
    document.body.classList.toggle("light");
    renderer.setClearColor(document.body.classList.contains("light") ? 0xe7edf3 : 0x111820, 1);
  };
  document.getElementById("fullscreen").onclick = () => document.documentElement.requestFullscreen?.().catch(() => toast("Fullscreen bị trình duyệt chặn", true));
  document.getElementById("screenshot").onclick = () => {
    renderer.render(scene, activeCamera);
    const link = document.createElement("a");
    link.download = "PulmoSlicer-3D.png";
    link.href = canvas.toDataURL("image/png");
    link.click();
  };
  document.querySelectorAll(".clip").forEach(input => input.addEventListener("input", () => {
    const index = Number(input.dataset.clip);
    clippingPlanes[index].constant = Number(input.value);
  }));
  document.getElementById("clip-reset").onclick = () => {
    clippingPlanes.forEach(plane => plane.constant = 10000);
    document.querySelectorAll(".clip").forEach(input => input.value = 10000);
  };
  document.getElementById("help").onclick = () => document.getElementById("help-dialog").showModal();
  document.getElementById("close-help").onclick = () => document.getElementById("help-dialog").close();
}

function updateDiagnostics() {
  const elapsed = ((performance.now() - startedAt) / 1000).toFixed(1);
  document.getElementById("diagnostics").textContent = `${meshes.size}/${manifest.meshes.length} nodes · ${loadedTriangles.toLocaleString()} triangles · ${elapsed}s`;
}

function resize() {
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  if (canvas.width !== width || canvas.height !== height) renderer.setSize(width, height, false);
  activeCamera.aspect = width / Math.max(height, 1);
  activeCamera.updateProjectionMatrix();
}

function animate() {
  resize();
  controls.update();
  renderer.render(scene, activeCamera);
  requestAnimationFrame(animate);
}

async function start() {
  bindUi();
  document.getElementById("case-title").textContent = manifest.caseTitle;
  document.getElementById("disclaimer").textContent = manifest.disclaimer;
  for (const node of manifest.meshes) {
    if (node.visible) await loadNode(node);
    await new Promise(resolve => setTimeout(resolve, 0));
  }
  fitObject(root);
  toast(`Đã tải ${meshes.size} cấu trúc`);
}

window.addEventListener("resize", resize);
window.addEventListener("error", event => toast(event.message || "Lỗi trình xem", true));
canvas.addEventListener("webglcontextlost", event => { event.preventDefault(); toast("Mất WebGL context; đang chờ trình duyệt khôi phục", true); });
start();
animate();

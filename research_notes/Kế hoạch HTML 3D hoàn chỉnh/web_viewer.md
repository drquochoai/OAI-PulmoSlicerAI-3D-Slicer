# Kiến trúc trình xem HTML 3D ngoại tuyến

## “All-in-one” thực sự đòi hỏi gì và nên chọn kiến trúc nào?

### Takeaway
Nên dùng Three.js/WebGL2 làm lõi trình xem bề mặt và glTF/GLB làm hợp đồng dữ liệu nội bộ, nhưng đóng gói các cấu trúc giải phẫu thành nhiều payload nhị phân độc lập được nhúng trong cùng một HTML. Toàn bộ JavaScript, CSS, decoder JS/WASM, metadata, mesh và worker source phải nằm trong file; tuyệt đối không dùng CDN, `fetch()` tới tài nguyên bên ngoài hay service worker.

### Cited Findings
- Three.js `WebGLRenderer` hiện dùng WebGL 2 và không còn hỗ trợ WebGL 1 từ r163; renderer có capability reporting, clipping planes, output color space và lựa chọn `powerPreference`. — [Three.js WebGLRenderer](https://threejs.org/docs/pages/WebGLRenderer)
- WebGL cung cấp đồ họa 3D tương tác tăng tốc phần cứng trong trình duyệt mà không cần plug-in, nhưng khả năng thực tế còn phụ thuộc GPU/driver của thiết bị. — [MDN WebGL API](https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API)
- glTF 2.0 có scene, node hierarchy, mesh, material, camera, binary buffers và định dạng GLB; đây là các primitive phù hợp để biểu diễn cây cấu trúc và bề mặt giải phẫu. — [Khronos glTF 2.0 specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html)
- Three.js `GLTFLoader` nhận trực tiếp `ArrayBuffer` bằng `parse/parseAsync`, hỗ trợ data URI, `KHR_draco_mesh_compression`, `KHR_mesh_quantization` và `EXT_meshopt_compression`. — [Three.js GLTFLoader](https://threejs.org/docs/pages/GLTFLoader.html)
- `EXT_meshopt_compression` là extension glTF đã được Khronos phê chuẩn; nó nén từng `bufferView` độc lập, cho phép giải nén trực tiếp hiệu quả, được thiết kế cho giải mã rất nhanh và có thể kết hợp thêm nén tổng quát. — [Khronos EXT_meshopt_compression](https://raw.githubusercontent.com/KhronosGroup/glTF/main/extensions/2.0/Vendor/EXT_meshopt_compression/README.md)
- `KHR_draco_mesh_compression` cũng đã được Khronos phê chuẩn và cho phép truyền geometry nén thay cho dữ liệu thô, nhưng cần decoder tương ứng. — [Khronos KHR_draco_mesh_compression](https://raw.githubusercontent.com/KhronosGroup/glTF/main/extensions/2.0/Khronos/KHR_draco_mesh_compression/README.md)
- Chrome và Firefox hiện xem các file `file://` như opaque origins; tải tài nguyên local kèm theo bằng `fetch`, XHR, font hoặc texture có thể gặp CORS. — [MDN CORS request not HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS/Errors/CORSRequestNotHttp)
- Worker tạo từ `blob:` URL kế thừa origin của document và được MDN khuyên dùng hơn `data:` URL; CSP phải cho phép `blob:` đối với worker. — [MDN Worker constructor](https://developer.mozilla.org/en-US/docs/Web/API/Worker/Worker)
- Web Workers chạy mã trên background thread để tác vụ nặng không chặn giao diện và giao tiếp với main thread qua message. — [MDN Using Web Workers](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API/Using_web_workers)
- vtk.js là thư viện scientific visualization dùng WebGL, tập trung vào ImageData, PolyData, reader và pipeline; chính tài liệu Kitware lưu ý nó không nhằm cung cấp toàn bộ filter của VTK/C++. — [Kitware vtk.js overview](https://kitware.github.io/vtk-js/docs/)
- vtk.js có volume rendering GPU và các transfer function, vì vậy phù hợp nếu sản phẩm tương lai nhúng CT volume, nhưng đó không phải phạm vi surface-only hiện tại. — [Kitware vtk.js Volume](https://kitware.github.io/vtk-js/api/Rendering_Core_Volume.html)

### Inferences
- Kiến trúc v1 được khuyến nghị: **Three.js + GLTFLoader + MeshoptDecoder**, build/minify thành một script cố định; dữ liệu mỗi anatomy/stable-ID là một GLB hoặc buffer-view bundle độc lập, được base64 hóa hoặc đặt trong thẻ script dữ liệu không thực thi. Khi mở file, JavaScript giải mã chuỗi thành `Uint8Array` rồi gọi `GLTFLoader.parseAsync`, không tạo request mạng.
- Không nên đóng toàn bộ ca thành một GLB duy nhất nếu muốn progressive loading: loader có thể phải parse/decode quá nhiều trước khi người dùng tương tác. Chia payload theo cấu trúc hoặc nhóm nhỏ cho phép ưu tiên phổi/u/aorta trước, sau đó B/A/V và khung xương.
- Mặc định checkbox xuất là **tất cả cấu trúc hợp lệ đang có**; khi mở HTML, trạng thái mong muốn cũng là tất cả hiển thị. Tuy vậy, decoder phải nạp theo hàng đợi ưu tiên và đưa viewer vào trạng thái tương tác ngay sau nhóm lõi đầu tiên, đồng thời tiếp tục nạp các nhóm còn lại với thanh tiến độ.
- Meshopt nên là mặc định vì cơ chế buffer-view độc lập và mục tiêu giải mã nhanh phù hợp lazy decode. Draco chỉ nên là backend benchmark/fallback build-time, không nên đóng gói đồng thời hai decoder nếu không có lợi ích định lượng vì sẽ làm HTML lớn hơn.
- Worker source được đóng thành chuỗi trong HTML, tạo `Blob`, rồi `new Worker(URL.createObjectURL(blob))`; truyền `ArrayBuffer` bằng transferable objects để tránh copy. Cần fallback decode trên main thread theo từng chunk nếu worker bị CSP/browser chặn.
- Không dùng service worker, IndexedDB, local server hoặc dynamic import từ đường dẫn ngoài. Không cần chúng để xem file và chúng làm yêu cầu double-click `file://` kém ổn định hơn.
- HTML nên có CSP meta giới hạn network và tài nguyên, nhưng policy thực tế phải được test trên `file://`; cho phép duy nhất script/style nội tuyến đã đóng gói, `blob:` cho worker và `data:/blob:` cho ảnh tải xuống. Không đưa chuỗi metadata người dùng vào HTML bằng `innerHTML`; dùng `textContent` và serialize an toàn.
- vtk.js không được chọn cho v1 surface viewer vì bundle và abstraction khoa học rộng hơn nhu cầu. Giữ vtk.js làm phương án v2 nếu nhúng CT volume, reslice, labelmap hoặc widget y khoa chuyên sâu.

### Gaps
- Không có kích thước nén hoặc thời gian giải mã chung áp dụng cho mọi ca; phải benchmark trên các mesh thật của PulmoSlicerAI.
- Khả năng WebAssembly và CSP dưới `file://` có khác biệt giữa phiên bản browser/enterprise policy; phải có decoder JavaScript fallback và test trên máy mục tiêu.

## Một trình xem 3D “đầy đủ” cho phạm vi này cần tính năng nào?

### Takeaway
V1 cần là một trình xem mô hình bề mặt hoàn chỉnh, không tự nhận là bản sao 3D Slicer: đầy đủ điều khiển camera, cây giải phẫu, chọn/ẩn/isolate/focus, màu/opacity, clipping bề mặt, đo khoảng cách có cảnh báo, screenshot, fullscreen, trợ giúp và chẩn đoán lỗi. CT voxel, volume rendering, chỉnh sửa segmentation và tính toán phẫu thuật mới không thuộc file HTML mặc định.

### Cited Findings
- `OrbitControls` hỗ trợ rotate, pan, zoom/dolly, touch gestures, damping, zoom-to-cursor, lưu/reset state và auto-rotate. — [Three.js OrbitControls](https://threejs.org/docs/pages/OrbitControls.html)
- `Raycaster` được thiết kế để mouse-pick object 3D và trả về object, điểm giao, face, normal và khoảng cách. — [Three.js Raycaster](https://threejs.org/docs/pages/Raycaster)
- Three.js renderer hỗ trợ global và object-level clipping planes, đủ để làm mặt cắt trực quan của surface mesh. — [Three.js WebGLRenderer](https://threejs.org/docs/pages/WebGLRenderer)
- Fullscreen API cho phép đưa một element và descendants vào chế độ toàn màn hình, nhưng MDN đánh dấu không phải Baseline hoàn toàn nên viewer cần hoạt động tốt cả khi nút fullscreen không khả dụng. — [MDN Fullscreen API](https://developer.mozilla.org/en-US/docs/Web/API/Fullscreen_API)
- `HTMLCanvasElement.toBlob()` tạo Blob ảnh từ canvas, phù hợp để xuất PNG screenshot cục bộ. — [MDN HTMLCanvasElement.toBlob](https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/toBlob)
- `ResizeObserver` theo dõi thay đổi kích thước element; hướng dẫn WebGL best practices khuyến nghị xử lý đúng kích thước canvas và VRAM thận trọng. — [MDN ResizeObserver](https://developer.mozilla.org/en-US/docs/Web/API/ResizeObserver); [MDN WebGL best practices](https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API/WebGL_best_practices)
- Content Security Policy cho phép hạn chế những tài nguyên document được tải và là một lớp giảm nguy cơ XSS. — [MDN Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP)

### Inferences
- Bộ tính năng v1 bắt buộc:
  - Cây anatomy responsive, có search/filter, tri-state checkbox, expand/collapse, `Show all`, `Hide all`, `Invert`, `Isolate`, `Focus`, và badge báo `loading/loaded/empty/error`.
  - Hierarchy giữ stable ID thay vì phụ thuộc tên hiển thị: Lungs → Right/Left → lobes → Lung/B/A/V; Tumor; Aorta → ascending/arch/descending/branches; Chest wall → ribs right/left, sternum, T1–T12. Không đưa clavicle, scapula hoặc costal cartilage.
  - Mouse/touch: rotate 360°, pan, zoom-to-cursor; giới hạn near/far và min/max distance để camera không chui mất vào mesh; nút reset và fit all/fit selection.
  - Camera presets A/P/L/R/S/I kèm orientation cube và ký hiệu L/R/A/P/S/I. Có perspective/orthographic toggle; mọi preset phải kiểm thử đối chiếu Slicer để tránh đảo trái-phải.
  - Picking bằng raycast, hover highlight nhẹ, click chọn, panel thông tin tên chuẩn, bên, lobe, loại B/A/V, màu, opacity và cảnh báo nghiên cứu.
  - Opacity slider cho node và group; show/hide labels; wireframe/edge overlay tùy chọn; nền sáng/tối; ambient + directional lighting; bật/tắt auto-rotate.
  - Color template nhúng dưới dạng versioned JSON map `stableAnatomyId -> sRGB hex + default opacity + material flags`. Templates v1: `PulmoSlicer Surgical Contrast` (mặc định đồng nhất giữa các ca), `Slicer Original`, `Color-blind friendly`, `Monochrome anatomy`. Cho color picker từng node/group, preview template, `Reset selected` và `Reset all to template`; thay đổi chỉ tồn tại trong session.
  - Mặc định exporter chọn tất cả cấu trúc hợp lệ và template Surgical Contrast. Trong HTML tất cả node được bật, nhưng người dùng có thể chọn `Chỉ phổi`, `Chỉ B/A/V`, `U + mạch`, `Aorta`, `Chest wall` qua quick presets.
  - Screenshot PNG với tùy chọn nền trong suốt/đặc, tiêu đề ca ẩn danh và legend; fullscreen nếu browser hỗ trợ; nút Help hiển thị quy ước chuột/touch và phím tắt.
  - Clipping X/Y/Z trực quan với slider, invert và reset. Vì chỉ có surface, phải ghi rõ đây là cắt bề mặt để quan sát, không phải lát CT hay đánh giá mật độ mô.
  - Đo point-to-point v1 có thể làm bằng hai lần ray-pick và hiển thị mm nếu pipeline giữ scale/transform chuẩn; bắt buộc ghi “measurement from exported surface; research/reference only”. Không triển khai geodesic, stenosis, diameter tự động hoặc thể tích lâm sàng trong v1 nếu chưa có validation.
  - Panel diagnostics thu gọn: version exporter/viewer, số node/triangle/draw call đã tải, thời gian first-interactive/load-all, WebGL2/GPU capability không định danh, lỗi decode; có nút sao chép log kỹ thuật nhưng không chứa PHI/path local.
  - Accessibility: keyboard focus, shortcut document, label/ARIA cho controls, contrast tốt, UI co giãn; sidebar có giới hạn chiều rộng và log/status không được làm tràn layout.
- Làm mượt phải tách rõ:
  - **Geometry smoothing** được thực hiện không phá hủy trong Slicer/exporter trước nén, theo profile riêng cho vessel, lobe, tumor, aorta và bone; mesh nguồn không bị sửa. Với mạch, ưu tiên bảo tồn topology/nhánh nhỏ và kiểm tra sai lệch hình học trước khi chấp nhận.
  - **Smooth shading** trong HTML chỉ nội suy normal để nhìn mượt, không làm thay đổi geometry; có toggle Smooth/Flat để người dùng hiểu khác biệt.
  - Nếu người dùng cần chọn mức mượt ngay trong HTML, v1 an toàn nhất là tùy chọn xuất kèm hai phiên bản `Original` và `Presentation-smoothed` cho vessel rồi chuyển đổi tức thời. Đổi lại file lớn hơn; nên để đây là checkbox nâng cao, không nhân đôi tất cả anatomy. Dynamic Laplacian/Taubin smoothing trong browser nên là v2 sau khi có worker, boundary constraints và kiểm thử sai lệch, không phải v1 mặc định.
- “Đầy đủ” không bao gồm: DICOM viewer, MPR, window/level, volume rendering, chỉnh sửa segment, chạy AI/PTL, lưu chỉnh sửa về scene Slicer, hay kết luận lâm sàng. Các tính năng này cần vtk.js/volume payload và một chương trình khác về bản chất.

### Gaps
- Đo khoảng cách chỉ đáng tin nếu exporter chứng minh transform và đơn vị nhất quán từ Slicer RAS/mm qua glTF/web; cần test phantom có kích thước biết trước.
- Fullscreen, download screenshot và clipboard có thể bị enterprise browser policy hạn chế; phải degrade gracefully.

## Progressive loading, LOD, GPU fallback và xử lý lỗi nên hoạt động thế nào?

### Takeaway
Viewer phải đạt “time-to-first-interaction” sớm, không cố decode tất cả trước khi hiện giao diện. Dùng queue ưu tiên, worker, transferable buffers, quality profile và capability-based degradation; không hứa GPU/VRAM cụ thể vì trình duyệt quyết định adapter. Mất WebGL context hoặc thiếu WebGL2 phải tạo thông báo rõ và hướng xử lý, không để màn hình đen.

### Cited Findings
- Three.js `LOD` hỗ trợ nhiều mesh theo khoảng cách camera và tự chuyển giữa mức gần/trung bình/xa. — [Three.js LOD](https://threejs.org/docs/pages/LOD.html)
- WebGL best practices khuyến nghị ước tính VRAM, cung cấp nhiều mức chất lượng, giải phóng object sớm và xử lý `webglcontextlost`; WebGL không cung cấp API portable để hỏi tổng VRAM. — [MDN WebGL best practices](https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API/WebGL_best_practices)
- `isContextLost()` cho biết WebGL context đã mất; context có thể mất do áp lực GPU, chuyển GPU hoặc driver reset. — [MDN isContextLost](https://developer.mozilla.org/en-US/docs/Web/API/WebGLRenderingContext/isContextLost)
- `WebGLRenderer.info` cung cấp số draw call, triangle, point và line để theo dõi tài nguyên/rendering; renderer còn có capability object. — [Three.js WebGLRenderer](https://threejs.org/docs/pages/WebGLRenderer)
- Performance API cung cấp phép đo thời gian trong window và worker. — [MDN Performance API](https://developer.mozilla.org/en-US/docs/Web/API/Performance)

### Inferences
- Boot sequence:
  1. Render ngay HTML shell/sidebar/skeleton và kiểm tra WebGL2.
  2. Parse manifest nhẹ, hiển thị cấu trúc/check state mặc định là tất cả.
  3. Tạo renderer ở `powerPreference: high-performance`, nhưng mô tả đây chỉ là hint; không tuyên bố ép dùng CUDA/shared VRAM.
  4. Decode nhóm ưu tiên: tumor + lobes + aorta (nếu có), sau đó B/A/V, sau đó ribs/sternum/T-spine. Với ca segmentectomy có thể ưu tiên B/A/V trước chest wall.
  5. Cho camera tương tác sau nhóm đầu; status cập nhật một dòng theo tác vụ hiện tại và một progress tổng, không append vô hạn.
  6. Decode phần còn lại trong worker với concurrency thấp có điều chỉnh; upload GPU từng chunk trong frame budget để tránh giật.
- Mặc dù mặc định mọi cấu trúc đều được chọn, nhóm chưa tải vẫn có trạng thái `loading`; nếu người dùng tắt trước khi decode, hạ ưu tiên hoặc bỏ decode. Nếu bật lại, nạp on demand.
- Chỉ tạo LOD cho cấu trúc nặng và bền topology (lobes, chest wall, aorta). Với các nhánh B/A/V nhỏ, distance LOD có thể xóa nhánh quan trọng; tốt hơn dùng một mesh presentation đã decimate bảo tồn topology và optional high-detail khi focus. Không dùng LOD để thay đổi nội dung/nhãn anatomy.
- Quality/export profiles phải được benchmark, không gắn con số tuyệt đối trước dữ liệu. Baseline đề xuất để nghiệm thu trên máy người dùng:
  - `Quick share`: tối ưu first-interactive và file nhỏ; chấp nhận giảm chi tiết chest wall/lobes nhưng không được mất nhánh labeled.
  - `Standard` mặc định: giữ mọi labeled branch và appearance tốt; mục tiêu nội bộ sau benchmark là first-interactive ≤ 5 giây, load-all ≤ 15 giây và median interaction ≥ 30 FPS trên máy mục tiêu.
  - `Surgical detail`: giữ nhiều triangle hơn; cảnh báo dung lượng và VRAM, vẫn phải phản hồi UI trong lúc nạp.
  Những ngưỡng này là **acceptance targets cần hiệu chỉnh bằng benchmark**, không phải khả năng được nguồn bên ngoài đảm bảo.
- Viewer cần adaptive degradation theo thứ tự: tắt MSAA/shadow/post-processing → giảm pixel ratio → dùng low LOD cho cấu trúc lớn → tạm ẩn edge overlay/labels → đề nghị reload ở `Compatibility mode`. Không tự ẩn B/A/V labeled mà không báo.
- Không dùng shadow map mặc định; ánh sáng đơn giản và SSAO/postprocessing chỉ là tùy chọn vì draw cost và memory. `preserveDrawingBuffer` để false trong lúc tương tác; khi screenshot, render frame chuyên biệt hoặc dùng render target để tránh chi phí thường trực.
- Khi context lost: dừng queue/upload, giữ UI và manifest, hiển thị toast không modal, thử reinitialize khi `webglcontextrestored`; nếu thất bại, cung cấp diagnostics và hướng dẫn đóng tab 3D khác/cập nhật driver/chọn Compatibility mode.
- Mọi payload có byte length và SHA-256 trong manifest; trước parse phải kiểm tra range/length, sau decode kiểm tra finite positions, index bounds và triangle count. Một node hỏng chỉ chuyển node đó sang `error`, không làm hỏng toàn viewer.
- Browser matrix 2026 nên được định nghĩa theo release channel, không hard-code version mau lỗi thời:
  - Windows 11: Chrome Stable hiện hành và N-1; Edge Stable hiện hành và N-1 — bắt buộc.
  - Firefox Stable hiện hành và Firefox ESR hiện hành — bắt buộc compatibility test.
  - macOS: Safari hiện hành và N-1 — hỗ trợ thứ cấp nếu file được chia sẻ ra ngoài Windows.
  - Không hỗ trợ Internet Explorer hoặc WebGL1-only.
  - Mỗi ZIP/release ghi chính xác browser build, GPU/driver, file size và dataset fingerprint đã benchmark.
- Test matrix phải có: file:// double-click khi máy offline; đường dẫn có dấu/khoảng trắng; file read-only; network disabled; integrated/shared GPU; discrete GPU; context loss injection; payload corruption/truncation; 100%/125%/150% DPI; màn hình nhỏ; mouse/touchpad/touch; light/dark; all nodes; node rỗng; file lớn; screenshot; fullscreen unavailable.

### Gaps
- Không có một ngưỡng triangle/file-size chung bảo đảm 30 hoặc 60 FPS trên mọi GPU; cần corpus benchmark đại diện và telemetry cục bộ trong test, không gửi đi.
- “Current và N-1” phải được đóng băng thành số build cụ thể trong release checklist tại thời điểm phát hành; không thể xác định vĩnh viễn từ kế hoạch.

## Tiêu chí nghiệm thu và ranh giới an toàn nên là gì?

### Takeaway
Nghiệm thu phải đo được tính độc lập, đúng hình học/hướng, đầy đủ node, khả năng tương tác, nhất quán màu, không lộ PHI và hiệu năng trên máy mục tiêu. File HTML là phương tiện trình bày mô hình bề mặt nghiên cứu, không phải DICOM/diagnostic viewer.

### Cited Findings
- glTF quy định scene/node hierarchy, binary data, mesh, material và hệ tọa độ; do đó exporter phải thực hiện và kiểm thử chuyển đổi hệ tọa độ thay vì chỉ chép vertex Slicer. — [Khronos glTF 2.0 specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html)
- Three.js có output color space mặc định sRGB, vì vậy palette cần được định nghĩa nhất quán theo sRGB và kiểm thử ảnh chụp thay vì dựa vào màu vật liệu tùy ý. — [Three.js WebGLRenderer](https://threejs.org/docs/pages/WebGLRenderer)
- WebGL context có thể mất và WebGL phụ thuộc phần cứng, do đó lỗi GPU phải là một acceptance path có UI rõ ràng. — [MDN WebGL API](https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API); [MDN isContextLost](https://developer.mozilla.org/en-US/docs/Web/API/WebGLRenderingContext/isContextLost)

### Inferences
- Acceptance bắt buộc:
  1. Một file `.html`, không tạo asset cạnh bên, mở bằng double-click khi tắt mạng và không có request ra ngoài.
  2. Manifest ghi viewer/export schema version, stable anatomy IDs, bounds, units, transform, color-template version, payload checksum và flag anonymized.
  3. Default export selection là tất cả node có mesh hợp lệ; summary trước khi xuất liệt kê included/skipped/empty. Không tự tạo cấu trúc người dùng đã đặt `None` trong pipeline segmentation.
  4. Node tree và quan hệ parent/child khớp Subject Hierarchy contract; show/hide group, isolate, focus và restore state hoạt động cho mọi node.
  5. Golden phantom xác nhận L/R/A/P/S/I, kích thước mm, bounds và preset camera; không chấp nhận mirror/invert.
  6. Golden screenshots cho mỗi color template ở background sáng/tối với tolerance; màu được ánh xạ bằng stable ID và reset chính xác.
  7. Vessel smoothing QA: số connected components/branch labels không giảm ngoài policy, không sinh NaN/non-manifold nghiêm trọng, displacement/volume change nằm trong threshold được nhóm dự án phê duyệt; nguồn segmentation không đổi.
  8. Viewer có smooth-vs-flat shading; nếu export kèm original/smoothed vessel variants, toggle không thay đổi ID, màu, transform hoặc visibility tree.
  9. Rotate/pan/zoom/touch, fit/reset, camera presets, pick, opacity, template, clipping, measure, screenshot, fullscreen fallback và help được test end-to-end.
  10. Progressive loader hiển thị tên tác vụ hiện tại; lỗi một payload không khóa UI; corruption, thiếu WebGL2 và context loss có thông báo hành động được.
  11. Standard profile đạt ngưỡng benchmark đã chốt trên máy mục tiêu và ghi kết quả trong release artifact; không dùng tỷ lệ CPU/RAM làm tiêu chí viewer vì bottleneck thường là decode/upload/GPU/draw calls.
  12. HTML không chứa DICOM pixels, patient name, MRN, DOB, UID, local path, log raw hoặc metadata không whitelist; text metadata được escape, không có telemetry/network.
  13. Banner cố định/Help ghi “Research visualization; not automatically validated for diagnosis or surgical decision”; measurement/clipping ghi rõ dựa trên exported surface.
  14. Export hoặc validation thất bại không sửa MRML scene, segmentation nguồn hay màu nguồn; output tạm được dọn và lỗi được log ở Slicer.
- Hai chế độ output có thể tồn tại về sau: all-in-one `.html` mặc định như yêu cầu; `.html + .glb` chỉ là tùy chọn chuyên gia cho ca cực lớn. Không được âm thầm đổi default thành nhiều file.
- Phải tạo một `HTML export contract` riêng: schema manifest, stable IDs, color-template schema, coordinate transform, unit, smoothing provenance, encoder/decoder versions và backward-compatibility policy. Viewer nên từ chối schema major không hỗ trợ nhưng chấp nhận minor mới nếu field lạ có thể bỏ qua.

### Gaps
- Threshold displacement/volume/topology cho vessel smoothing cần clinical/engineering review và phantom/dataset validation; không nên tự đặt chỉ từ web research.
- Giới hạn file-size cảnh báo (ví dụ 100 MB hay 250 MB) phải dựa trên browser/máy đích và ca thật, không nên coi là tiêu chuẩn phổ quát.

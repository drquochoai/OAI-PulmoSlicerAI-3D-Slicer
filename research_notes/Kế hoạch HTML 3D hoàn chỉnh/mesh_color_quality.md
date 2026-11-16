# Chất lượng mesh, làm mượt, màu và QA

## 1. Pipeline VTK/Slicer an toàn từ closed surface đến mesh web

### Takeaway
Phải coi mesh dùng trong HTML là một **dẫn xuất chỉ để hiển thị**, được tạo từ bản sao sâu của closed surface; không được chỉnh sửa segmentation/labelmap hay closed surface nguồn. Pipeline nên có kiểm tra trước/sau từng bước và ưu tiên bảo toàn topology hơn là ép đạt tỷ lệ giảm polygon.

### Cited Findings
- Slicer có thể lưu closed-surface segmentation dưới dạng `.seg.vtm`; định dạng này giữ các trường tùy chỉnh như tên segment, terminology và màu, vì vậy đây là nguồn metadata tốt hơn STL/OBJ rời rạc — [3D Slicer data loading and saving](https://github.com/Slicer/Slicer/blob/main/Docs/user_guide/data_loading_and_saving.md).
- `vtkCleanPolyData` loại điểm không dùng, gộp điểm trùng và có thể chuyển cell suy biến; tài liệu cảnh báo rằng gộp điểm có thể thay đổi topology hoặc tạo non-manifold, nên tolerance phải được chọn rất thận trọng — [VTK vtkCleanPolyData](https://vtk.org/doc/nightly/release/9.4/html/classvtkCleanPolyData.html).
- `vtkDecimatePro` chỉ xử lý triangle, nên polygonal input cần được triangulate trước; bật `PreserveTopology` ngăn mesh splitting và hole elimination nhưng có thể làm cho mục tiêu giảm polygon không đạt được — [VTK vtkDecimatePro](https://vtk.org/doc/nightly/html/classvtkDecimatePro.html).
- `vtkWindowedSincPolyDataFilter` làm đều vị trí đỉnh bằng bộ lọc windowed-sinc, thường cần khoảng 10–20 vòng thay vì 100–200 vòng của bộ lọc smooth cổ điển; passband thấp làm mượt mạnh hơn. Tài liệu cũng cảnh báo làm mượt quá mức làm mất chi tiết hình học — [VTK vtkWindowedSincPolyDataFilter](https://vtk.org/doc/nightly/release/8.2/html/classvtkWindowedSincPolyDataFilter.html).
- `vtkWindowedSincPolyDataFilter` có thể phát sinh error scalar/vector thể hiện độ dịch chuyển của mỗi đỉnh và có tùy chọn normalize tọa độ để cải thiện ổn định số rồi chuyển ngược về hệ tọa độ ban đầu — [VTK vtkWindowedSincPolyDataFilter](https://vtk.org/doc/nightly/release/8.2/html/classvtkWindowedSincPolyDataFilter.html).
- `vtkFeatureEdges` có thể phát hiện boundary edge, non-manifold edge, sharp feature edge và manifold edge, phù hợp để kiểm tra tính kín và lỗi topology trước/sau tối ưu — [VTK vtkFeatureEdges](https://vtk.org/doc/nightly/release/9.3/html/classvtkFeatureEdges.html).
- `vtkDistancePolyDataFilter` tính signed hoặc unsigned distance giữa hai `vtkPolyData`, và có thể tính hai chiều; nó thích hợp để đo sai lệch hình học giữa mesh nguồn và mesh xuất — [VTK vtkDistancePolyDataFilter](https://vtk.org/doc/nightly/release/9.6/html/classvtkDistancePolyDataFilter.html).
- Normals của polygonal mesh được tính bằng cách xác định normal của polygon rồi trung bình tại các điểm chung; normals chỉ áp dụng cho polygon/triangle, không áp dụng cho line/vertex/triangle strip — [VTK vtkmPolyDataNormals](https://vtk.org/doc/nightly/html/classvtkmPolyDataNormals.html).

### Inferences
- Pipeline đề xuất cho mỗi segment:
  1. Lấy closed surface hiện hành và `DeepCopy` sang mesh xuất tạm; ghi checksum/point count/triangle count/bounds/component count của nguồn.
  2. Áp dụng đầy đủ parent transform sang hệ tọa độ bệnh nhân trước khi đổi trục sang web; giữ matrix biến đổi trong manifest để audit.
  3. `vtkTriangleFilter`.
  4. `vtkCleanPolyData` với tolerance tuyệt đối `0` ở lần đầu để loại điểm trùng chính xác và điểm không dùng; không dùng tolerance gần đúng cho mạch nhỏ.
  5. Kiểm tra boundary/non-manifold/component count. Mesh kín phải không có boundary edge ngoài những chỗ đã được đánh dấu chủ ý.
  6. Làm mượt nhẹ bằng `vtkWindowedSincPolyDataFilter`, bật normalize tọa độ; cấu hình theo loại cấu trúc, không dùng một tham số chung.
  7. Kiểm tra độ dịch chuyển và topology; nếu vượt ngưỡng thì tự giảm smoothing hoặc quay về mesh trước smoothing, không hỏi người dùng giữa tác vụ.
  8. Decimate bằng `vtkDecimatePro` với `PreserveTopologyOn`, `SplittingOff`, không xóa boundary vertex. Tỷ lệ giảm chỉ là mục tiêu mềm; chất lượng thắng dung lượng.
  9. Làm sạch tolerance 0 lần cuối, rồi tính lại point normals với consistency/orientation và auto-orient khi mesh kín.
  10. Đo distance hai chiều so với mesh nguồn, component count, boundary/non-manifold edge, bounds và branch-survival; chỉ đóng gói nếu qua gate.
- Không nên mặc định chạy “clean với tolerance > 0”, hole fill hoặc topology-changing decimation vì chúng có thể nối nhầm hai nhánh mạch nằm gần nhau, đóng lỗ thật hoặc làm mất nhánh nhỏ.
- Thứ tự smooth trước rồi decimate là điểm xuất phát hợp lý: giảm nhiễu voxel trước khi chọn bỏ đỉnh. Tuy nhiên phải benchmark thêm một nhánh decimate nhẹ trước smooth cho xương/phổi lớn; pipeline phải chọn theo anatomy class, không coi thứ tự này là chân lý phổ quát.
- Mesh nguồn/high-quality, mesh hiển thị trong Slicer và mesh web phải là ba vai trò tách biệt. Mọi tham số và metric của mesh web được ghi vào manifest để tái lập.

### Gaps
- Không có một bộ tham số WindowedSinc/DecimatePro chính thức nào phù hợp cho mọi CT phổi, độ dày lát cắt và đường kính nhánh; các giá trị cụ thể phải được chốt bằng benchmark trên dữ liệu của dự án.
- Cần xác nhận phiên bản VTK đóng gói cùng Slicer 5.12.4 vì hành vi/cửa sổ mặc định của `vtkWindowedSincPolyDataFilter` đã thay đổi ở các bản VTK mới hơn.

## 2. Làm mượt mạch máu mà không phá nhánh và ý nghĩa đo đạc

### Takeaway
Làm mượt đẹp phải diễn ra trước khi đóng gói và có kiểm soát hình học; trình duyệt chỉ được làm mượt **ánh sáng/normals**, không được tự di chuyển đỉnh. Mạch, phế quản và u cần preset bảo tồn chi tiết riêng, kèm gate phát hiện mất nhánh.

### Cited Findings
- Windowed-sinc giảm thành phần tần số cao của bề mặt; tài liệu VTK nói rõ làm mượt quá mức có thể làm mất chi tiết quan trọng và feature-edge smoothing chỉ giảm chứ không loại bỏ nguy cơ đó — [VTK vtkWindowedSincPolyDataFilter](https://vtk.org/doc/nightly/release/8.2/html/classvtkWindowedSincPolyDataFilter.html).
- Trong Slicer Segment Editor, smoothing factor khoảng `0.1` được mô tả là nhẹ và `0.5` trở lên là mạnh; đây là mô tả giao diện của Slicer chứ không phải passband trực tiếp của WindowedSinc — [3D Slicer Segment Editor](https://slicer.readthedocs.io/en/5.8/user_guide/modules/segmenteditor.html).
- Three.js hỗ trợ smooth shading khi `flatShading=false`; normal map và shading thay đổi cách ánh sáng thể hiện bề mặt nhưng không thay đổi hình dạng thực của mesh — [Three.js MeshStandardMaterial](https://threejs.org/docs/pages/MeshStandardMaterial.html).
- `vtkDecimatePro` có thể bị giới hạn mức giảm khi bật các ràng buộc bảo toàn topology; tài liệu cảnh báo chỉ có thể đảm bảo đạt mức giảm yêu cầu khi cho phép thay đổi topology và những tùy chọn xâm lấn khác — [VTK vtkDecimatePro](https://vtk.org/doc/nightly/html/classvtkDecimatePro.html).

### Inferences
- Tuyệt đối cấm browser-side vertex smoothing/displacement ở chế độ mặc định. HTML chỉ thay đổi normals, material, ánh sáng, opacity và anti-aliasing. Như vậy cùng một file cho kết quả hình học xác định, và đo đạc không đổi theo trình duyệt/GPU.
- Preset khởi đầu để benchmark, **không phải ngưỡng đã được thẩm định lâm sàng**:

| Nhóm | Làm mượt | Giảm polygon ban đầu | Gate bắt buộc |
|---|---|---:|---|
| Động mạch/tĩnh mạch/phế quản phân thùy | Rất nhẹ, passband tương đối cao, 5–15 vòng | 0–25% | Không giảm component/đầu nhánh hợp lệ; không nối hai nhánh; max displacement theo mm và theo bán kính nhánh |
| Động mạch chủ và nhánh quai | Nhẹ–trung bình, 10–20 vòng | 20–45% | Bảo toàn ostium, lòng nhánh, component và topology |
| U phổi | Không hoặc rất nhẹ | 0–15% | Bảo toàn thể tích, bờ và khoảng cách tới cấu trúc; mọi đo đạc từ source, không từ mesh trang trí |
| Thùy/nhu mô/territory | Nhẹ–trung bình | 35–65% | Bảo toàn thể tích, fissure interface và quan hệ chồng lấp |
| Xương sườn/xương ức/T1–T12 | Nhẹ | 45–75% | Không gãy vòng/sai số định vị quá ngưỡng; giữ đúng số và bên |

- Với mạch nhỏ, mức giảm nên bị giới hạn bởi sai số hình học và đường kính tối thiểu chứ không chỉ bởi phần trăm triangle. Nếu nhánh quá nhỏ so với voxel spacing hoặc không qua gate thì giữ nguyên mesh nguồn cho nhánh đó.
- Gate “branch survival” nên so sánh ít nhất: số connected components; số endpoint/nhánh trên centerline nếu centerline khả dụng; tổng chiều dài centerline; bán kính nhỏ nhất; khoảng cách hai chiều source→export và export→source. Một gate chỉ dựa trên Hausdorff tổng thể có thể bỏ sót một nhánh nhỏ mất hoàn toàn.
- HTML có thể cung cấp nút “Hình học gốc / Hình học trình bày” chỉ khi cả hai LOD được nhúng; mặc định nên dùng mesh trình bày đã QA. Nếu chỉ nhúng mesh tối ưu thì mọi phép đo phải ghi “xấp xỉ trên mesh xuất”, không được gắn nhãn đo chẩn đoán.
- Độ mượt thị giác nên đến từ point normals nhất quán, `flatShading=false`, antialiasing và material không kim loại với roughness vừa phải; tránh bóng gương vì che khuất đường kính và chỗ phân nhánh.

### Gaps
- Chưa có tập ca chuẩn và ground truth để xác định ngưỡng mất nhánh, sai số mm, thay đổi thể tích và mức reduction tối đa cho từng anatomy class.
- Cần quyết định có nhúng source LOD riêng phục vụ đo đạc hay giới hạn HTML là viewer trình bày; lựa chọn thứ nhất tăng mạnh dung lượng all-in-one.

## 3. Template màu xác định, tương đồng giữa Slicer và HTML

### Takeaway
Màu cần được quản lý bằng một template phiên bản hóa dựa trên stable anatomical ID, không dựa vào tên node. Nên ưu tiên terminology/recommended color có sẵn; với A1–A10, B1–B10, V1–V10 chưa có màu chuẩn duy nhất thì dùng palette dự án có quy tắc, đồng thời giữ khả năng override và reset.

### Cited Findings
- Slicer Terminologies dùng category/type/type modifier/region để mã hóa cấu trúc; mỗi item của segmentation context có thể chứa recommended display color, và custom terminology context có thể được nạp từ JSON — [3D Slicer Terminologies](https://github.com/slicer/slicer/blob/main/Docs/user_guide/modules/terminologies.md).
- Slicer General Anatomy là một tập con của DICOM master list và tương ứng với `GenericAnatomyColors`; custom name và color vẫn có thể được gán trong khi giữ terminology entry — [3D Slicer Terminologies](https://github.com/slicer/slicer/blob/main/Docs/user_guide/modules/terminologies.md).
- Slicer hỗ trợ color table CSV với `LabelValue`, `Name`, RGBA và các cột terminology chuẩn; tài liệu khuyến nghị dùng coding scheme phục vụ DICOM trong ứng dụng hình ảnh lâm sàng — [3D Slicer Colors developer guide](https://slicer.readthedocs.io/en/latest/developer_guide/modules/colors.html).
- Slicer lưu trạng thái màu tự sinh hay do người dùng chọn qua trường `SegmentN_ColorAutoGenerated`, nên có thể phân biệt màu template với override thủ công — [3D Slicer Segmentations developer guide](https://slicer.readthedocs.io/en/5.8/developer_guide/modules/segmentations.html).
- DICOM SEG có thuộc tính Recommended Display CIELab Value, nhưng giá trị này là màu khuyến nghị để render chứ không định nghĩa một cơ chế render duy nhất — [DICOM Supplement 240](https://dicom.nema.org/Dicom/News/March2024/docs/sups/sup240.pdf).
- Three.js dùng Linear-sRGB làm working space và sRGB cho đầu ra hiển thị; màu hexadecimal/CSS sRGB được chuyển tự động nếu ColorManagement bật. Cấu hình sai color space có thể làm màu tối/sáng sai — [Three.js Color Management](https://threejs.org/manual/pages/color-management.html).
- glTF định nghĩa base color và alpha/material semantics; `alphaMode=BLEND` thực hiện compositing trong khi `OPAQUE` bỏ qua alpha — [glTF 2.0 specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html).

### Inferences
- Định nghĩa `PulmoSlicer Surgical Colors v1` bằng JSON/CSV có schema rõ ràng:
  - `templateId`, `version`, `displayName`, `source`, `colorSpace=sRGB`.
  - Mỗi entry gồm `stableAnatomyId`, terminology codes nếu có, tên Việt/Anh, `rgba`, material parameters, default visibility và priority.
  - Cùng template được áp vào display node trong Slicer và được serialize nguyên vẹn vào manifest HTML; viewer không tự sinh màu ngẫu nhiên.
- Quy tắc màu mặc định đề xuất:
  - Pulmonary arteries và aorta: họ đỏ/coral; từng A1–A10 khác nhẹ về lightness/hue nhưng vẫn nhận biết là động mạch.
  - Pulmonary veins: họ xanh lam/cyan; từng V khác nhẹ nhưng không trùng động mạch.
  - Bronchi: kem/vàng nhạt hoặc trắng ngà, đủ tương phản với phổi và xương.
  - Lobes/territories: pastel bán trong suốt; bên phải/trái và từng thùy có khác biệt nhẹ.
  - Tumor: magenta hoặc vàng nổi bật, luôn có outline/selection highlight không chỉ dựa vào màu.
  - Ribs/sternum/T-spine: ivory/beige trung tính; aorta vẫn nổi bật.
- Không gọi palette trên là “chuẩn màu giải phẫu quốc tế”. Chỉ những entry có terminology/recommended color chính thức mới ghi provenance tương ứng; phần còn lại ghi rõ `project-defined`.
- Thứ tự ưu tiên khi xuất: override người dùng được xác nhận > template được chọn > recommended color từ terminology > fallback theo anatomy class. Nút `Reset to template` khôi phục template; `Reset all` không làm thay đổi segmentation source.
- Mặc định UI xuất HTML chọn **toàn bộ cấu trúc hợp lệ hiện có**; cấu trúc không được tạo hoặc thất bại được hiển thị disabled với lý do, không được thay thế bằng mesh rỗng. Xương đòn, xương vai và sụn sườn không có trong template/phạm vi.
- HTML phải có bộ chọn template ít nhất: `PulmoSlicer Surgical v1` (mặc định), `High contrast`, `Color-vision friendly`, `Current Slicer colors`. Thay template chỉ đổi material, không đổi geometry hoặc stable ID.
- Canonical color nên lưu dưới dạng sRGB hex/RGBA để dễ audit; khi tạo Three.js material phải đi qua ColorManagement, và renderer output là sRGB. QA dùng ảnh chụp tham chiếu để phát hiện double-conversion hoặc thiếu conversion.
- Độ trong suốt cần preset theo nhóm và có nút trả về mặc định. Vì blend của nhiều lớp trong suốt có thể gây sai thứ tự/nhìn xuyên khó hiểu, chọn cấu trúc phải có outline và chế độ isolate; không dựa riêng vào opacity.

### Gaps
- Chưa xác định được một chuẩn công khai duy nhất quy định màu cụ thể cho toàn bộ A1–A10/B1–B10/V1–V10. Vì vậy palette chi tiết phải là quy ước của dự án và cần bác sĩ phẫu thuật duyệt.
- Cần kiểm tra cách Slicer 5.12.4 diễn giải RGB display node so với sRGB trên web bằng test screenshot; không nên giả định các số RGB nhìn giống hệt nếu chưa hiệu chỉnh ánh sáng/tone mapping.

## 4. Riêng tư, toàn vẹn và QA hình học/hiển thị

### Takeaway
Single-file HTML rất dễ được gửi ra ngoài tổ chức, nên phải ẩn danh theo allowlist, không chỉ xóa vài trường quen thuộc. QA phải bao gồm topology, hướng trái/phải, màu, selection mặc định, tính toàn vẹn file và mức sai lệch hình học; cảnh báo “nghiên cứu/không thay thế quyết định lâm sàng” luôn hiển thị trong About/metadata.

### Cited Findings
- DICOM PS3.15 nói rõ áp dụng confidentiality profile không bảo đảm mọi thông tin nhận dạng đã được loại bỏ và không thay thế đánh giá nguy cơ tái nhận dạng theo ngữ cảnh chia sẻ — [DICOM PS3.15 2026b](https://dicom.nema.org/medical/dicom/2026b/output/html/part15.html).
- Basic Application Level Confidentiality Profile loại bỏ thông tin về bệnh nhân, người liên quan, nhân viên, tổ chức, UID/ngày giờ có thể dùng để đối sánh và private attributes; DICOM cũng lưu ý pixel data cần biện pháp riêng nếu được xuất — [DICOM PS3.15 2026b](https://dicom.nema.org/medical/dicom/2026b/output/html/part15.html).
- DICOM nhấn mạnh conformance statement của de-identifier phải mô tả trường nào bị xóa, thay thế, giữ lại và cách duy trì referential integrity — [DICOM PS3.15 2026b](https://dicom.nema.org/medical/dicom/2026b/output/html/part15.html).
- Slicer terminology giúp định danh cấu trúc bằng codes thay vì chỉ dựa vào tên tự do, giảm lỗi nhập và hỗ trợ interoperability — [3D Slicer Terminologies](https://github.com/slicer/slicer/blob/main/Docs/user_guide/modules/terminologies.md).

### Inferences
- Export manifest phải dùng **allowlist**: stable anatomy ID, tên giải phẫu chuẩn, hierarchy, màu, opacity, transform đã chuẩn hóa, geometry metrics, phiên bản exporter/template và disclaimer. Không đưa nguyên MRML node attributes, DICOM tags, đường dẫn file, username, hostname, log, UID, timestamp chụp hay tên scene vào HTML.
- Tên ca mặc định là mã ngẫu nhiên cục bộ như `PulmoSlicer Case`; tên do người dùng nhập được quét cảnh báo nhưng không thể bảo đảm không chứa PHI, nên cần hộp xác nhận trước khi lưu/chia sẻ.
- Không nhúng CT voxel/pixel, screenshot gốc hay report tự do ở v1. Điều này giảm bề mặt rò rỉ nhưng không làm cho mô hình 3D tự động trở thành vô danh; hình học hiếm và tên file vẫn có thể là dữ liệu nhạy cảm.
- Manifest nên chứa `exportProfile`, SHA-256 của từng payload mesh và SHA-256 tổng thể trong footer/sidecar logic nội bộ; viewer kiểm tra hash trước khi parse và báo rõ nếu file bị hỏng.
- Bộ QA tự động trước khi xuất:
  1. stable ID duy nhất; hierarchy không chu kỳ; không có node rỗng.
  2. Tất cả số tọa độ hữu hạn, index hợp lệ, triangle không suy biến vượt ngưỡng.
  3. Bounds và centroid sau đổi tọa độ khớp nguồn; marker R/L/A/P/S/I được đặt từ transform, không suy từ camera.
  4. Boundary/non-manifold/component count trước và sau.
  5. Distance source/export, thay đổi diện tích/thể tích, branch-survival theo nhóm.
  6. Template/color/opacity mapping đủ 100% stable IDs; color-space test.
  7. Mặc định toàn bộ cấu trúc hợp lệ được chọn trong export dialog và xuất hiện trong tree; các cấu trúc loại trừ không xuất hiện.
  8. Snapshot chuẩn từ 6 hướng và so sánh hồi quy; reviewer kiểm tra trái/phải và chồng khít A/B/V/lobe/tumor/aorta/bone.
  9. Mở lại file bằng trình duyệt hỗ trợ với network disabled; toggle/isolate/color/reset hoạt động.
- HTML phải phân biệt “màu hiển thị”, “mesh trình bày” và “dữ liệu nguồn”; không cho phép người dùng hiểu việc làm mượt/đổi màu là chỉnh sửa segmentation gốc.
- Measurement, nếu có, phải ghi đơn vị mm, profile mesh dùng để đo và cảnh báo độ chính xác. Không cho phép số đo trên mesh đã làm mượt được xuất như một kết quả lâm sàng xác nhận nếu chưa có validation.

### Gaps
- Yêu cầu pháp lý cụ thể phụ thuộc nơi triển khai và đối tượng nhận file; DICOM profile không thay thế đánh giá pháp lý/rủi ro của bệnh viện.
- Chưa có threshold nghiệm thu định lượng cho distance, volume change, branch survival và màu ΔE; các ngưỡng này cần được ghi vào test matrix sau benchmark và duyệt lâm sàng.

## 5. Quyết định triển khai và trình tự nghiệm thu

### Takeaway
Triển khai nên chia thành các gate độc lập: nguồn bất biến → mesh preset theo anatomy → màu/manifest xác định → QA tự động → kiểm tra browser. Tính năng “đẹp” không được đi trước khả năng chứng minh mesh không mất nhánh và không sai màu/hướng.

### Cited Findings
- Các format bề mặt đơn như STL/OBJ chỉ tải một segment mỗi file, trong khi `.seg.vtm` có thể giữ metadata segmentation tùy chỉnh; vì vậy nguồn Slicer giàu metadata cần được chuyển sang manifest web trước khi mất thông tin — [3D Slicer data loading and saving](https://github.com/Slicer/Slicer/blob/main/Docs/user_guide/data_loading_and_saving.md).
- Built-in color tables của Slicer là read-only để bảo đảm tính nhất quán; người dùng tạo bản sao nếu muốn chỉnh sửa — [3D Slicer Colors](https://slicer.readthedocs.io/en/latest/user_guide/modules/colors.html).
- `MeshStandardMaterial` là material PBR và tốn chi phí hơn các material đơn giản; opacity, flat shading, roughness và metalness đều là tham số riêng — [Three.js MeshStandardMaterial](https://threejs.org/docs/pages/MeshStandardMaterial.html).

### Inferences
- Trình tự work package đề xuất:
  1. Chốt stable anatomy IDs và schema `PulmoSlicer Surgical Colors v1`.
  2. Viết exporter clone-only và manifest allowlist; chưa smoothing.
  3. Thêm validation topology/distance/orientation và bộ golden cases.
  4. Thêm preset smooth/decimate từng anatomy class với fallback tự động.
  5. Đồng bộ màu Slicer↔HTML, override/reset và regression screenshot.
  6. Thêm material/lighting/opacity/isolate; kiểm tra hiệu năng và transparency sorting.
  7. Privacy review, offline/browser matrix, checksum và release gate.
- Gate phát hành bắt buộc: không mutation source; không mất nhánh vượt chuẩn; không đổi bên/hướng; default chọn toàn bộ cấu trúc hợp lệ; excluded anatomy vắng mặt; màu round-trip đúng; không PHI trong source HTML; file hỏng bị từ chối; viewer vẫn thao tác mượt trên cấu hình máy mục tiêu.
- Nếu preset làm mượt không qua gate, exporter phải tự dùng mesh ít xử lý hơn hoặc mesh nguồn của segment đó, ghi cảnh báo trong log/manifest và vẫn hoàn tất các segment khác. Không được hiện dialog chờ giữa tác vụ.

### Gaps
- Cần hội đồng dự án chốt golden cases, người duyệt lâm sàng, ngưỡng QA và máy chuẩn benchmark trước khi biến các preset đề xuất thành mặc định chính thức.

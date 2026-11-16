# Hướng dẫn cài đặt và chạy PulmoSlicer AI trong 3D Slicer

Tài liệu này áp dụng cho bản phát triển hiện tại trên Windows. PulmoSlicer AI
đang ở giai đoạn nghiên cứu; kết quả phân đoạn và đặt tên giải phẫu phải được
đối chiếu trên CT nguồn và bác sĩ xác nhận.

## 1. Cấu hình đã kiểm chứng

Máy phát triển đã chạy smoke test thành công với:

- 3D Slicer `5.12.4`, build `34645`, source revision `4e21c19`;
- Python của Slicer `3.12.10`;
- Windows 11 x64, AMD Ryzen AI MAX+ 392, 24 logical processors, khoảng 61 GB RAM;
- TotalSegmentator extension revision `d8eda9f`;
- TotalSegmentator Python `2.14.0`;
- PyTorch `2.15.0+cpu`, nnUNetv2 `2.8.1`, pydicom `3.0.2`.

Đường dẫn Slicer trên máy này:

```text
D:\Program Files\3D Slicer 5.12.4
```

Không tự nâng riêng PyTorch, nnUNet hoặc TotalSegmentator bằng `pip` trong
Python Console. Các package này do extension Slicer quản lý và nâng riêng lẻ có
thể phá môi trường đang hoạt động.

## 2. Yêu cầu hệ thống

| Thành phần | Yêu cầu hiện tại |
|---|---|
| Hệ điều hành | Windows 11 x64 đã cập nhật; Windows 10 chưa được release-test |
| 3D Slicer | Đúng `5.12.4` build `34645` cho baseline hiện tại |
| CPU | x86-64; CPU-only phải hoạt động, không yêu cầu CUDA/NVIDIA |
| RAM | 16 GB: Lite/giới hạn; 32 GB: Standard mục tiêu; 64 GB: Performance |
| GPU | Tự động dùng CUDA hoặc ROCm nếu chính PyTorch runtime báo khả dụng; DirectML không được dùng cho TotalSegmentator vì CLI/model hiện không hỗ trợ backend này |
| Lưu trữ | SSD, đủ chỗ cho DICOM nguồn, model, output và thư mục tạm; chưa có ngưỡng dung lượng được chứng nhận |
| Mạng | Cần khi cài extension/model lần đầu; runtime bệnh viện mục tiêu là offline |

Không dùng cấu hình 16 GB để chạy nhiều model nặng song song. Với CT lát mỏng
lớn, phần mềm có quyền chặn tác vụ chi tiết nếu không đủ RAM.

## 3. Extension cần cài

### Bắt buộc

| Thành phần | Nguồn | Vai trò |
|---|---|---|
| DICOM | Có sẵn trong Slicer | Nhập đúng series CT và giữ geometry/source references |
| Segment Editor | Có sẵn trong Slicer | Kiểm tra và chỉnh mask thủ công |
| TotalSegmentator | Extensions Manager | Tạo A/V/B, airway wall và năm thùy phổi |
| PyTorch | Dependency của TotalSegmentator | Runtime AI; Extensions Manager tự cài |
| NNUNet | Dependency của TotalSegmentator | Runtime segmentation; Extensions Manager tự cài |

Khi cài `TotalSegmentator` qua Extensions Manager, bật **Automatically install
dependencies**. Slicer sẽ cài PyTorch và NNUNet phù hợp. Sau đó khởi động lại
Slicer.

### Khuyến nghị

| Extension | Vai trò dự kiến |
|---|---|
| SlicerVMTK | Centerline, graph và kiểm tra nhánh mạch |
| SegmentEditorExtraEffects | Công cụ sửa mask bổ sung |
| MarkupsToModel | Dựng model từ markups trong workflow thủ công |

`LungCTAnalyzer`, `MONAIAuto3DSeg` và `MONAILabel` không phải dependency bắt
buộc của PulmoSlicer AI. Có thể giữ nếu dùng cho nghiên cứu khác.

## 4. Cài PulmoSlicer AI bằng file ZIP

Gói dành riêng cho Slicer `5.12.4` build `34645` nằm tại:

```text
dist\34645-win-amd64-PulmoSlicerAI-gitlocal-2026-11-16.zip
```

Trước khi cài ZIP, phải cài `TotalSegmentator` và khởi động lại Slicer theo mục
3. Gói ZIP không chứa lại model hoặc PyTorch của TotalSegmentator, cũng không
chứa checkpoint PTL của tác giả.

Các bước cài:

1. Mở **View → Extensions Manager**.
2. Chọn **Install from file...**.
3. Chọn nguyên file ZIP trên; không giải nén thủ công.
4. Đợi cài xong rồi nhấn **Restart**.
5. Sau khi Slicer mở lại, vào nhóm **Chest by bsquochoainew → PulmoSlicer AI for segmentectomy**.

Nếu đã cài một ZIP PulmoSlicer AI cũ, vào **Manage Extensions**, uninstall bản
cũ, restart, rồi mới **Install from file...** bản mới. Không chồng hai phiên bản.

Kiểm tra checksum trước khi cài:

```powershell
Get-FileHash .\dist\34645-win-amd64-PulmoSlicerAI-gitlocal-2026-11-16.zip -Algorithm SHA256
```

Giá trị của bản `.10` hiện tại phải là:

```text
acb1b727b33da780ce87d7e9bdb5afda7063405c0af46f4c11edf2ea0b050584
```

Muốn tạo lại ZIP từ source:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Build-SlicerExtensionZip.ps1
```

ZIP có thư mục bao theo format CPack, descriptor `PulmoSlicerAI.s4ext`, module
Python tại `lib/Slicer-5.12/qt-scripted-modules`, và manifest chỉ rõ đây là bản
nghiên cứu. Gói này đã được API giải nén của Extensions Manager đọc thành công
và module/widget đã được nạp lại bằng Slicer thật.

## 5. Kiểm tra tự động trước khi chạy

Mở PowerShell tại thư mục repository và chạy:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Test-SlicerEnvironment.ps1
```

Script thực hiện smoke test headless, không mở DICOM và không đọc dữ liệu bệnh
nhân. Kết quả máy-cục-bộ được ghi tại:

```text
evidence\local\slicer-smoke.json
```

Kết quả đúng phải có `"passed": true`, cùng các module DICOM, SegmentEditor,
TotalSegmentator và PulmoSlicerAI đều là `true`.

Nếu Slicer ở vị trí khác:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Test-SlicerEnvironment.ps1 `
  -SlicerHome "D:\duong-dan\Slicer"
```

## 6. Chạy PulmoSlicer AI từ source khi phát triển

Không cần chép file vào `Program Files`. Chạy trực tiếp bản source:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Run-PulmoSlicerAI.ps1
```

Script sẽ:

1. chạy preflight;
2. mở đúng Slicer `5.12.4`;
3. thêm module path chỉ cho phiên hiện tại;
4. tự chuyển sang module **PulmoSlicer AI**.

Để bỏ qua preflight khi đang phát triển:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Run-PulmoSlicerAI.ps1 -SkipPreflight
```

## 7. Cài bản user-local cho lập trình viên

Script sau chép PulmoSlicer AI vào `%LOCALAPPDATA%`, không ghi đè thư mục Slicer
và không đụng vào DICOM/project:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Install-PulmoSlicerAI.ps1
```

Sau khi cài, script in ra đường dẫn launcher. Mặc định:

```text
%LOCALAPPDATA%\PulmoSlicerAI\5.12.4\Run-PulmoSlicerAI.ps1
```

Installer cố ý không tự thay đổi TotalSegmentator/PyTorch/nnUNet đang chạy tốt.
Nếu thiếu TotalSegmentator, cài bằng Extensions Manager như mục 3; dependency sẽ
được Slicer tự giải quyết. Trong bản phát hành offline sau này, extension và
model bundle phải được đóng gói kèm checksum thay vì tải lúc chạy.

## 8. Cài module thủ công cho lập trình viên

1. Mở Slicer.
2. Chọn **Edit → Application Settings → Modules**.
3. Trong **Additional module paths**, thêm:

   ```text
   D:\VSCODE_WORKING\OAI-PulmoSlicerAI-3D-Slicer\slicer_extension\PulmoSlicerAI
   ```

4. Khởi động lại Slicer.
5. Tìm `PulmoSlicer AI` trong module selector.

Không cần thêm `pulmoslicer_engine` vào Python path của Slicer khi cài bằng ZIP;
engine cần thiết đã nằm trong gói. Runtime/checkpoint PTL được giữ riêng tại
`%LOCALAPPDATA%\PulmoSlicerAI\ptl-v1` và được xác minh trước khi nạp.

## 9. Workflow hiện tại trong PulmoSlicer AI

### Nhập CT

1. Mở module **DICOM**.
2. Import folder DICOM.
3. Chọn đúng một CT series; không trộn phase hoặc reconstruction series.
4. Kiểm tra lát cắt axial/coronal/sagittal trước khi segmentation.

### Tạo artery/vein/airway

1. Mở **PulmoSlicer AI**.
2. Chọn volume CT tại ô **CT ngực**.
3. `lung_vessels` luôn chạy full-resolution/normal trong TotalSegmentator 2.14;
   task này không hỗ trợ Fast. UI không còn hiển thị Fast giả.
4. Giữ **Tự động tốt nhất — CUDA/ROCm rồi CPU**. Dòng **Backend thực tế** phải
   cho biết thiết bị thật; không suy ra khả năng tính toán chỉ từ dung lượng
   shared VRAM.
5. Nhấn **Tạo phế quản, động mạch và tĩnh mạch**.
6. Extension tạo một Segmentation node và gọi task `lung_vessels` của
   TotalSegmentator.
7. Kết quả chỉ được chấp nhận khi có đủ các segment ID ổn định
   `lung_airways`, `lung_arteries`, `lung_veins`.

Không dùng Fast/Faster làm geometry đo đạc hoặc ground truth nhánh ngoại vi vì
chúng giảm độ phân giải để đổi lấy tốc độ.

### Tạo năm thùy

Nhấn **Tạo năm thùy phổi**. Extension gọi task `total` với đúng subset:

- `lung_upper_lobe_left`;
- `lung_lower_lobe_left`;
- `lung_upper_lobe_right`;
- `lung_middle_lobe_right`;
- `lung_lower_lobe_right`.

Nhấn **Kiểm tra và hiển thị mô hình 3D** để tạo closed-surface representation,
sau đó lưu scene. Không chỉnh/smooth mask nguồn chỉ để model 3D đẹp hơn; bề
mặt 3D chỉ là representation hiển thị.

### Cài và chạy PTL A/B/V theo phân thùy

1. Cần Internet ở lần cài PTL đầu tiên. Nhấn **Cài/kiểm tra PTL runtime chính
   thức**. Extension tự cài `torch-geometric==2.6.1` và downloader vào thư mục
   riêng, tải source PTL đúng commit đã khóa, rồi tải ba checkpoint airway,
   artery và vein từ thư mục công khai của tác giả.
2. Mỗi checkpoint được kiểm tra SHA-256. Nếu sai hash hoặc thiếu file, tác vụ
   dừng và không chạy model. Checkpoint không được đóng gói lại vì upstream
   không nêu rõ quyền tái phân phối weights.
3. Chọn **PTL B**, **PTL A**, **PTL V** hoặc **PTL A+B+V** ở ô **Cây phân
   thùy**. Tạo A/V/B nguồn bằng TotalSegmentator trước, sau đó nhấn **PTL: Tách
   và đặt nhãn A/B/V theo phân thùy**. Extension chỉ chạy checkpoint PTL đã chọn
   và tạo ID ổn định, ví dụ `PTL_A_R_01`, `PTL_B_R_01`, `PTL_V_R_01`.
4. Phổi phải có 10 lớp phải; phổi trái dùng 8 lớp theo ontology của PTL, gồm
   `S1+2` và `S7+8` gộp. Mỗi cây còn có lớp 19 central/out-of-lung. Không được
   đổi tên các lớp gộp thành hai nhánh độc lập khi model không cung cấp bằng
   chứng đó.
5. Luôn kiểm tra overlay trên CT. Đây là kết quả nghiên cứu từ một model chưa
   được validation lâm sàng trên dữ liệu của anh.

Nếu máy đã cài PTL thành công thì các lần sau không tải lại; extension chỉ kiểm
tra manifest và hash. Muốn buộc cài lại, đóng Slicer rồi đổi tên thư mục
`%LOCALAPPDATA%\PulmoSlicerAI\ptl-v1` để vẫn có thể phục hồi bản cũ.

### Chạy một click và theo dõi tiến độ

Chọn đúng mức cần thiết tại **Cây phân thùy**:

- **None**: chỉ chạy năm thùy, không tạo A/V/B và không chạy PTL;
- **A/V/B nguồn gộp**: tạo ba mask nguồn của TotalSegmentator, không chạy PTL;
- **PTL B**, **PTL A** hoặc **PTL V**: tạo nguồn rồi chỉ chạy checkpoint PTL của
  hệ đã chọn;
- **PTL A+B+V**: tạo đầy đủ ba cây theo vùng PTL.

Ngay dưới lựa chọn, dòng **Luồng sẽ chạy** liệt kê tuần tự các bước và dependency
được gọi tự động. Khi chọn PTL, selector/nút tạo A/V/B nguồn riêng bị ẩn vì
TotalSegmentator sẽ được gọi nội bộ đúng một lần; người dùng không cần chạy trùng.
Khi chọn `None`, output A/V/B và PTL mới không được tạo. Kết quả cũ trong scene
không bị xóa nhưng bị loại khỏi hiển thị 3D của workflow hiện tại.

Task `lung_vessels` của TotalSegmentator là một model gộp nên khi chọn bất kỳ
PTL A/B/V nào, bước nguồn vẫn tính cả ba mask trong một lượt. Tiết kiệm đạt được
ở bước PTL và dựng mesh: hệ không chọn không được suy luận/hiển thị. Nhấn
**MỘT CLICK: Tạo và hiển thị mô hình 3D phổi** để chạy chuỗi đã chọn. Panel mờ
phía dưới cập nhật stage, tiến độ tác vụ con, thời gian đã chạy, CPU và RAM hệ
thống. Kết quả 3D chỉ tự hiện sau khi output có đủ segment ID bắt buộc. Lần đầu
PTL sẽ tự gọi quy trình cài runtime nếu chưa có.

Các selector output hiển thị **Tự động tạo khi chạy** thay cho `None`. CT đầu vào
tự chọn volume đầu tiên trong scene, nhưng người dùng vẫn phải kiểm tra đúng CT
series. Các nút chạy bước riêng được gom trong **Tác vụ riêng lẻ / công cụ nâng
cao** và mặc định thu gọn; tooltip của từng mục giải thích output và bước nào
không được chạy.

Quality, backend, số CPU thread, bề mặt 3D và Cây phân thùy đều được chốt trước
khi bắt đầu. PulmoSlicer gọi TotalSegmentator ở chế độ không tương tác, vì vậy
không còn hộp thoại Fast/Full-resolution hoặc cảnh báo VRAM chờ người dùng giữa
một run dài. Nếu GPU ưu tiên không khả dụng, backend tự fallback về backend đã
xác minh tốt nhất còn lại, cuối cùng là CPU.

### Động mạch chủ và mốc xương lồng ngực

Mục **Cấu trúc bổ sung** là tùy chọn và mặc định là `None`, vì chạy thêm cấu
trúc không làm TotalSegmentator/PTL nhanh hơn. Có thể chọn:

- chỉ `aorta`;
- `aorta` cùng thân cánh tay đầu, hai động mạch cảnh chung và hai động mạch
  dưới đòn;
- xương sườn phải/trái 1–12, xương ức và T1–T12;
- hoặc cả hai nhóm.

Extension cố ý không yêu cầu xương đòn, xương vai hoặc sụn sườn. Các cấu trúc
này không được đưa vào subset, cây Data hay HTML. Mask `aorta` của
TotalSegmentator là một cấu trúc liên tục; bản hiện tại không đổi tên giả thành
động mạch chủ lên/quai/đoạn xuống khi chưa có bước centerline/landmark và bác sĩ
review. Chọn cấu trúc bổ sung trước khi nhấn **Một click**, hoặc dùng nút riêng
trong phần công cụ nâng cao.

### Xuất một file HTML 3D tương tác

Sau khi có mô hình, mở **3. Xuất HTML 3D tương tác — một file, ngoại tuyến**.

1. Giữ tên mặc định `PulmoSlicer Case` hoặc nhập mã ca đã ẩn danh. Không nhập
   tên bệnh nhân, MRN hoặc ngày sinh.
2. Chọn `Tiêu chuẩn`, `Chia sẻ nhanh` hoặc `Chi tiết`.
3. Chọn template màu. Mặc định là **PulmoSlicer Surgical Contrast**.
4. Mục **Chọn toàn bộ cấu trúc hợp lệ** được bật mặc định. Exporter chỉ lấy
   anatomy PulmoSlicer nằm trong allowlist; node lạ, rỗng hoặc tên tự do không
   được âm thầm đưa vào file.
5. Nhấn **Xuất một file HTML 3D all-in-one** và chọn nơi lưu.

HTML chứa toàn bộ viewer, CSS, mesh nén và metadata ẩn danh trong đúng một file.
Người nhận nhấp đúp để mở bằng Edge/Chrome mà không cần Slicer hoặc Internet.
Viewer hỗ trợ cây giải phẫu, tìm kiếm, show/hide/invert/isolate, xoay 360°, pan,
zoom, fit, sáu hướng nhìn, perspective/orthographic, clipping X/Y/Z, chọn cấu
trúc, opacity, đổi màu, đổi template, wireframe, smooth/flat shading, tự xoay,
đo hai điểm, PNG, fullscreen và diagnostics.

Làm mượt HTML luôn chạy trên `DeepCopy` của closed surface. Mạch B/A/V dùng
preset rất nhẹ, QA component/displacement và tự fallback về mesh ít xử lý hơn
nếu có nguy cơ mất/nhập nhánh. Browser chỉ thay normals/shading, không di chuyển
vertex. Segmentation, labelmap và closed surface nguồn không bị sửa.

Từ bản `.10`, Slicer chỉ sao chép closed surface trên main thread; triangulate,
smoothing, decimation, QA, nén và hash chạy trong worker nền. Progress hiển thị
tên cấu trúc cùng sáu checkpoint con và CPU/RAM vẫn cập nhật. Nút **Hủy xuất
HTML** yêu cầu dừng tại checkpoint an toàn kế tiếp; filter VTK đang chạy được
phép hoàn tất để tránh làm hỏng trạng thái nội bộ. Không cần chờ với cửa sổ
`Not Responding` như bản `.9`.

File không chứa voxel CT, DICOM metadata, raw log hoặc đường dẫn máy tính. Nó có
CSP `connect-src 'none'`, SHA-256 từng mesh và được ghi qua `.partial` rồi atomic
rename. Đây là mô hình trình bày/nghiên cứu; phép đo trong HTML dựa trên exported
surface, không tự động có giá trị chẩn đoán hoặc quyết định phẫu thuật.

### Cài đặt hiệu năng trước khi chạy

- **Lát cắt đầu vào** luôn là `Stride 1 — dùng toàn bộ lát cắt`. TotalSegmentator
  và PTL xử lý một thể tích 3D; bỏ lát 2/4/6 sẽ đổi spacing và có thể làm mất hoặc
  đứt nhánh nhỏ nên không được cung cấp như một chế độ segmentectomy.
- **Tự động an toàn** dùng toàn bộ logical CPU mà TotalSegmentator nhận được,
  một worker resampling và tối đa sáu worker saving.
- **Mục tiêu CPU khoảng 85%** đặt thread target bằng khoảng 85% logical CPU.
  Đây là best effort; Task Manager có thể thấp hơn nếu 12 lõi vật lý đã bão hòa
  hoặc stage bị giới hạn bởi băng thông RAM.
- **Trần RAM 85%** là giới hạn an toàn về ý nghĩa, không phải lệnh cố sử dụng đủ
  85%. Profile giảm worker ghi mask; cố lấp RAM có thể gây paging và chậm hơn.
- **Thủ công** cho phép chọn CPU thread, resampling worker và saving worker để
  benchmark cùng một CT. TotalSegmentator 2.14 mặc định dùng 1 resampling worker
  và 6 saving worker; tăng resampling không chắc nhanh hơn.

Các giá trị được truyền vào child process qua wrapper nằm trong extension; không
sửa hay ghi đè TotalSegmentator/PyTorch đã cài. Mỗi run ghi `slice_stride`,
`requested_threads`, `resample_workers`, `saving_workers` và resource policy vào
JSONL để so sánh. Không thể tự tăng “4 ảnh lên 5 ảnh” trong lúc chạy vì nnU-Net
quản lý các patch 3D bên trong tiến trình con và số thread được chốt khi tiến
trình khởi động.

### Ẩn/hiện theo bên, thùy và làm mượt 3D

Kết quả được tổ chức thật trong Data/Subject Hierarchy dưới **PulmoSlicer AI
Results → Right/Left → Upper/Middle/Lower → B/A/V/Lung**. Từng segment như
`A1 Right` hoặc `lung_upper_lobe_right` là child item của đúng folder. Phổi trái
chỉ có Upper/Lower; extension không tạo Middle giả. Mask nguồn gộp và class
central/out-of-lung nằm trong folder thu gọn **Internal sources**, không bị gán
giả vào Right hoặc Left.

Khung **Ẩn/hiện nhanh theo bên và thùy** trong module phản chiếu cấu trúc này và
cho phép bật/tắt cả nhóm mà không phải mở từng segment trong Data tree.

Chế độ **Nhanh — không smoothing** tạo bề mặt nhanh nhưng có thể trông khối như
Minecraft. Mask voxel không bị mất. Sau khi xử lý xong, đổi **Bề mặt 3D** sang
**Cân bằng** hoặc **Chi tiết**, rồi nhấn **Tạo lại / làm mượt mô hình 3D theo mức
đã chọn**. Extension xóa representation bề mặt cũ và dựng lại từ mask gốc; không
làm mờ/chỉnh mask dùng để đo.

Log hiệu năng không chứa tên volume, tên bệnh nhân hay đường dẫn DICOM và nằm ở:

```text
%LOCALAPPDATA%\PulmoSlicerAI\logs\run-*.jsonl
```

Trong log hiển thị, các cập nhật phần trăm liên tiếp của cùng một tác vụ con chỉ
chiếm một dòng: `50%` được thay bằng `62%`, rồi `75%`... thay vì tích lũy hàng
chục dòng. Tên tác vụ con, ví dụ **TotalSegmentator — A/V/B nguồn** hoặc **PTL —
A**, luôn đứng trước tiến độ. File JSONL vẫn giữ telemetry đầy đủ để phân tích
hiệu năng sau này.

Nút **Mở thư mục log hiệu năng** mở đúng thư mục này. Xem báo cáo phân tích tại
[`PERFORMANCE_AND_ONE_CLICK_AUDIT.md`](PERFORMANCE_AND_ONE_CLICK_AUDIT.md).

Tóm tắt nhiều run để so sánh thread/worker profiles:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\Summarize-PulmoSlicerLogs.ps1
```

## 10. Phần nào đã tự động và phần nào chưa

Đã hoạt động:

- tự nạp PulmoSlicerAI vào Slicer;
- kiểm tra đúng version Slicer/Python;
- kiểm tra các extension/capability bắt buộc và khuyến nghị;
- chọn CT và hai output Segmentation node trong PulmoSlicer AI;
- gọi `lung_vessels` cho airway/artery/vein;
- gọi task `total` chỉ cho năm thùy;
- tự cài và xác minh runtime/checkpoint PTL ở lần dùng đầu;
- tạo graph tâm tuyến nội bộ và chạy ba checkpoint PTL airway/artery/vein;
- cho phép `None` hoặc chỉ chạy checkpoint PTL B/A/V đã chọn;
- nhóm ẩn/hiện Right/Left → lobe → region → A/B/V/Lung;
- tạo folder thật trong Slicer Data tree: Right/Left → lobe → B/A/V/Lung;
- chạy TotalSegmentator không tương tác sau khi người dùng đã chốt lựa chọn;
- thay tại chỗ dòng phần trăm của cùng một tác vụ con trong log hiển thị;
- tạo các segment A/B/V theo 18 vùng giải phẫu, ID ổn định và tự show 3D;
- fail-closed nếu thiếu segment ID bắt buộc;
- tạo closed-surface 3D sau khi người dùng yêu cầu;
- tái tạo closed-surface cân bằng/chi tiết từ mask gốc sau preview không smoothing;
- một nút chạy tuần tự toàn bộ mô hình 3D cơ bản và tự show kết quả;
- tùy chọn tạo aorta/nhánh quai và mốc sườn–ức–T1/T12, không tạo xương đòn,
  xương vai hoặc sụn sườn;
- xuất một HTML 3D all-in-one ngoại tuyến, mặc định chọn toàn bộ cấu trúc hợp lệ;
- làm mượt/decimate mesh dẫn xuất theo loại anatomy với QA và fallback;
- template màu thống nhất giữa Slicer và HTML, cho phép đổi/reset trong viewer;
- progress panel liên tục cùng log JSONL CPU/RAM/stage đã loại PHI;
- nút mở giao diện TotalSegmentator để kiểm tra nâng cao;
- unit/integration tests cho DICOM geometry, class map, mask provenance, storage
  và review state.

Chưa tự động/hoàn chỉnh trong UI:

- tách từng nhánh instance với quan hệ cha–con và màn hình bác sĩ duyệt;
- chia nhu mô thành territory phân thùy;
- lesion/surgical plan;
- tách tự động mask aorta liên tục thành đoạn lên/quai/xuống có landmark review;
- DICOM SEG roundtrip và installer offline hoàn chỉnh.

PTL author reproduction đã chạy trên một fixture công khai; adapter graph nội
bộ vẫn cần thêm ca parity và kiểm tra lâm sàng. Automated smoke test chưa chạy
AI trên CT bệnh nhân; lần chạy `lung_vessels`/lobes/PTL đầu tiên cần người dùng
thực hiện trên CT hợp pháp và kiểm tra kết quả trên lát cắt nguồn.

Lưu ý ký hiệu: động mạch dùng `A1...`, phế quản dùng `B1...`, và tĩnh mạch dùng
`V1...`. `B1/B2/B3` không phải các nhánh động mạch. PTL upstream dùng 19 class
cho mỗi cây (18 segmental class và background), có các dạng gộp/biến thể ở phổi
trái; không được giả tạo đủ A/B/V1–10 bằng cách đổi tên ba mask gộp.

## 11. Xử lý lỗi thường gặp

### Không tìm thấy Slicer

Truyền `-SlicerHome` đúng thư mục chứa `Slicer.exe`.

### PulmoSlicer AI không xuất hiện

Nếu cài ZIP, kiểm tra đã chọn đúng gói build `34645` và đã restart Slicer. Nếu
chạy source, kiểm tra module path trỏ trực tiếp đến folder chứa
`PulmoSlicerAI.py`.

### TotalSegmentator thiếu

Mở **View → Extensions Manager**, cài `TotalSegmentator`, chấp nhận cài
dependencies và restart. Không tự `pip install torch` trong Slicer.

### TotalSegmentator chạy nhưng thiếu model

Cho phép tải model ở lần chạy đầu hoặc chuẩn bị model cache offline đúng version.
Không copy dataset nghiên cứu vào máy bệnh viện.

### Báo thiếu đồng thời lung_airways, lung_arteries và lung_veins sau khi đã chạy xong

Bản `2026.11.16.7` có thể để selector A/V/B, năm thùy và PTL cùng trỏ vào một
Segmentation node; bước năm thùy sau đó thay output A/V/B. Bản `.8` gắn role
`source`/`lobes`/`ptl`, tự tách node dùng chung và chặn ghi đè. Sau khi nâng cấp,
giữ scene hiện tại rồi bấm **Một click**: năm thùy hợp lệ được tái sử dụng, chỉ
stage bị thiếu mới chạy lại. Log lỗi mới cũng ghi trực tiếp chi tiết exception
thay vì chỉ ghi “xem thông báo lỗi”.

### Máy chậm hoặc thiếu RAM

Đóng model/app nặng khác, chạy tuần tự và không chạy lobe cùng lung_vessels.
Chọn **CPU — bắt buộc** chỉ để chẩn đoán hoặc khi GPU runtime lỗi. Không chuyển
sang Fast nếu kết quả sẽ được dùng để phân tích nhánh
nhỏ mà chưa đánh giá quality regression.

### Báo cáo lỗi

Chỉ gửi log đã loại PHI. Không gửi tên bệnh nhân, MRN, UID gốc, screenshot có
thông tin định danh hoặc đường dẫn chứa tên bệnh nhân.


# 14 — Extension packaging Windows và cài offline bệnh viện

## Hai sản phẩm khác nhau
**Slicer extension**: tập module giao diện và Slicer adapters, gói phù hợp Slicer stable cụ thể. **PulmoAI runtime**: Python isolated, wheels, models licensed, driver/provider tests. Distribution wrapper có thể là `.exe` dễ cài, nhưng **chưa có installer ở giai đoạn này**. `.s4ext` là descriptor trong Extensions Index, không phải trình cài extension đầy đủ.

## Compatibility matrix
Pin Slicer stable **theo máy dùng thực tế**, Python/Qt/VTK/ITK shipped version, Windows edition/architecture, TotalSeg version, model SHA, CPU instruction set, optional DirectML driver & AMD SKU; bệnh viện x86-64 chưa chắc giống ASUS. Không nhúng version cũ vô điều kiện nếu Slicer update. Mỗi release target Slicer version phải có smoke test.

## Kịch bản phân phối mong muốn
1. Người phát triển tạo signed build artifacts trên CI có source commit và SBOM.
2. Installer phát hiện Slicer versions; nếu không đúng hiển thị supported builds và cách cài song song.
3. Chép extension vào đúng module path/extension dir, install runtime vào program data app dir, model bundle approved; verify SHA256 và license.
4. Không admin khi có thể; khi cần admin phải nêu lý do, không đòi tắt Windows security.
5. Self test: load Slicer module, spawn CPU worker, read synthetic fixture, detect model registry, offline network disconnected.
6. AMD provider probe optional; lỗi GPU → CPU; không bỏ chức năng nền.
7. Uninstall chỉ xóa app files; **không xóa patient vault, project, exports**; data migration/rollback có snapshot.

## Offline installer manifest
Cần `slicer_compat`, package revision, code SHA, model registry + weights SHA/license, Python env freeze/wheels, runtime environment paths, signing status, min storage/RAM and supported profiles, install/uninstall migration scripts đã kiểm thử, docs/offline troubleshooting.

## Phép thử trên máy sạch
Windows 11 16 GB/32 GB CPU, Windows 11 ASUS 64 GB AMD, không Internet, không NVIDIA, user không admin, Unicode folder, short/long paths, antivirus on, limited disk, restart, uninstall/reinstall, Slicer upgrade, 2 Slicer versions installed, blocked model license, missing Visual C++ runtime, duplicate install. Tất cả cần logs sanitized và PASS/FAIL thật.

## Giới hạn sản phẩm nghiên cứu
Không phát hành tên gọi “clinical approved” chỉ vì extension package cài được; việc phân loại thiết bị y tế, quản lý chất lượng và thẩm định phụ thuộc mục đích sử dụng, quốc gia triển khai và tư vấn pháp lý.

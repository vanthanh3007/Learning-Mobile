# Rendering Performance

## Mục tiêu: 60 FPS (hoặc 120 FPS)

- 1 frame = 16.67ms ở 60 FPS, 8.33ms ở 120 FPS
- Nếu 1 frame mất > 16ms → jank (giật)
- Flutter render qua 2 threads: **UI thread** (Dart) và **Raster thread** (GPU)

---

## Nguyên nhân gây jank phổ biến

### 1. Rebuild widget không cần thiết

```dart
// ❌ SAI — toàn bộ CounterPage rebuild khi counter thay đổi
class CounterPage extends StatefulWidget { ... }
class _State extends State<CounterPage> {
  int count = 0;

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      HeavyWidget(),       // rebuild dù không liên quan count
      AnotherHeavyWidget(),
      Text('$count'),
    ]);
  }
}

// ✅ ĐÚNG — tách phần thay đổi ra riêng
class CounterPage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Column(children: [
      const HeavyWidget(),        // const → không rebuild
      const AnotherHeavyWidget(),
      CounterText(),              // chỉ widget này rebuild
    ]);
  }
}

class CounterText extends StatefulWidget { ... }
```

### 2. Dùng `const` sai cách

```dart
// ❌ Không có const → tạo mới mỗi lần rebuild
Widget build(BuildContext context) {
  return Column(
    children: [
      Padding(padding: EdgeInsets.all(16), child: Text('Title')), // new instance mỗi lần
    ],
  );
}

// ✅ const → tái sử dụng instance
Widget build(BuildContext context) {
  return const Column(
    children: [
      Padding(padding: EdgeInsets.all(16), child: Text('Title')),
    ],
  );
}
```

### 3. Xây dựng widget nặng trong build()

```dart
// ❌ SAI — tính toán nặng trong build()
@override
Widget build(BuildContext context) {
  final processed = expensiveDataProcessing(rawData); // chạy mỗi lần rebuild
  return Text(processed);
}

// ✅ ĐÚNG — cache kết quả
late final processed = expensiveDataProcessing(rawData); // tính 1 lần

@override
Widget build(BuildContext context) {
  return Text(processed);
}
```

---

## RepaintBoundary — tách layer render

```dart
// Isolate phần animation không ảnh hưởng phần còn lại
RepaintBoundary(
  child: AnimatedWidget(), // chỉ layer này repaint khi animate
)

// Dùng cho list item có animation phức tạp
ListView.builder(
  itemBuilder: (context, index) => RepaintBoundary(
    child: ProductCard(products[index]),
  ),
)
```

---

## ListView tối ưu

```dart
// ❌ Tạo hết tất cả item cùng lúc
ListView(children: products.map((p) => ProductCard(p)).toList())

// ✅ Chỉ tạo item visible trên screen
ListView.builder(
  itemCount: products.length,
  itemBuilder: (context, index) => ProductCard(products[index]),
)

// ✅ Với item có chiều cao cố định — nhanh hơn nhiều
ListView.builder(
  itemCount: products.length,
  itemExtent: 80.0, // Flutter không cần tính height mỗi item
  itemBuilder: (context, index) => ProductCard(products[index]),
)
```

---

## Image Performance

```dart
// ✅ Dùng cached_network_image
CachedNetworkImage(
  imageUrl: url,
  placeholder: (_, __) => const ShimmerWidget(),
  errorWidget: (_, __, ___) => const ErrorImage(),
)

// ✅ Preload ảnh trước khi navigate
precacheImage(NetworkImage(product.imageUrl), context);

// ✅ Dùng WebP thay PNG/JPG — nhỏ hơn 25-30%
```

---

## Công cụ profiling

```bash
# Chạy ở profile mode — gần nhất với production
flutter run --profile

# Mở Performance overlay
# Trong DevTools → Performance tab
```

```dart
// Performance overlay trong code
MaterialApp(
  showPerformanceOverlay: true, // hiện FPS bar
)
```

### Đọc Performance Overlay
```
Thanh xanh: UI thread (Dart code)
Thanh đỏ: Raster thread (GPU/Skia)
Nếu vượt đường 16ms → jank
```

---

## Câu hỏi phỏng vấn thường gặp

**Q: `keys` trong Flutter dùng để làm gì?**
> Key giúp Flutter identify widget khi tree thay đổi thứ tự. `ValueKey`, `ObjectKey` cho list item (tránh rebuild sai). `GlobalKey` để access state của widget từ bên ngoài. `UniqueKey` để force rebuild (ít dùng).

**Q: Sự khác biệt giữa `setState` và `markNeedsBuild`?**
> `setState` là API public, đánh dấu State dirty → Flutter schedule rebuild trong frame tiếp theo. `markNeedsBuild` là internal method, không nên dùng trực tiếp. Cả hai đều schedule rebuild không đồng bộ — không rebuild ngay lập tức.

**Q: Tại sao animation mượt dù UI thread đang bận?**
> Flutter dùng separate raster thread cho GPU compositing. Animation đơn giản (opacity, transform) có thể chạy hoàn toàn trên raster thread mà không cần UI thread. `FadeTransition`, `SlideTransition` thường không gây jank vì vậy.

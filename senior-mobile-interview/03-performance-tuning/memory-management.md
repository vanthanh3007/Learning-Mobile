# Memory Management

## Memory Leak là gì?

Object không còn dùng nữa nhưng vẫn bị giữ trong bộ nhớ → app chiếm RAM ngày càng nhiều → chậm, crash.

---

## Các nguyên nhân Memory Leak phổ biến trong Flutter

### 1. Không dispose Controller
```dart
// ❌ SAI
class MyWidget extends StatefulWidget { ... }
class _MyState extends State<MyWidget> {
  final TextEditingController _ctrl = TextEditingController();
  final AnimationController _anim = AnimationController(vsync: this);
  // QUÊN dispose → leak

  @override
  Widget build(BuildContext context) => TextField(controller: _ctrl);
}

// ✅ ĐÚNG
@override
void dispose() {
  _ctrl.dispose();
  _anim.dispose();
  super.dispose();
}
```

### 2. Không cancel StreamSubscription
```dart
// ❌ SAI
StreamSubscription? _sub;

@override
void initState() {
  _sub = dataStream.listen((data) => setState(() => _data = data));
  // stream tiếp tục chạy dù widget bị destroy
}

// ✅ ĐÚNG
@override
void dispose() {
  _sub?.cancel();
  super.dispose();
}
```

### 3. Closure giữ reference đến BuildContext
```dart
// ❌ SAI — closure giữ context alive
Future<void> fetchData() async {
  await Future.delayed(Duration(seconds: 5));
  // Widget có thể đã unmount, nhưng context bị giữ trong closure
  ScaffoldMessenger.of(context).showSnackBar(...);
}

// ✅ ĐÚNG
Future<void> fetchData(BuildContext context) async {
  await Future.delayed(Duration(seconds: 5));
  if (!context.mounted) return; // check trước khi dùng
  ScaffoldMessenger.of(context).showSnackBar(...);
}
```

### 4. Static reference
```dart
// ❌ SAI — static list giữ objects mãi mãi
class ImageCache {
  static final List<Uint8List> _images = []; // không bao giờ clear

  static void add(Uint8List img) => _images.add(img);
}

// ✅ ĐÚNG — dùng LRU cache với giới hạn size
class ImageCache {
  static final _lru = LinkedHashMap<String, Uint8List>();
  static const _maxSize = 100;

  static void add(String key, Uint8List img) {
    if (_lru.length >= _maxSize) {
      _lru.remove(_lru.keys.first); // xóa item cũ nhất
    }
    _lru[key] = img;
  }
}
```

---

## Cách tìm Memory Leak

### 1. Flutter DevTools — Memory tab
- Mở DevTools → Memory tab
- Thực hiện action (navigate, scroll, load data)
- Bấm GC (Garbage Collect)
- Nếu memory vẫn tăng sau GC → có leak

### 2. Dart Observatory
```bash
flutter run --observe
```

### 3. Kiểm tra trong code
```dart
// Thêm log vào dispose để xác nhận widget được dispose
@override
void dispose() {
  debugPrint('MyWidget disposed'); // không log này → leak
  super.dispose();
}
```

---

## Image Memory Optimization

```dart
// ❌ Load ảnh gốc resolution cao
Image.network('https://example.com/image_4k.jpg')

// ✅ Cache + resize
CachedNetworkImage(
  imageUrl: 'https://example.com/image.jpg',
  memCacheWidth: 300,   // resize trước khi lưu memory
  memCacheHeight: 300,
  maxWidthDiskCache: 600,
)

// ✅ Evict khi không cần (navigation nặng)
@override
void dispose() {
  PaintingBinding.instance.imageCache.evict(
    NetworkImage('https://example.com/image.jpg'),
  );
  super.dispose();
}
```

---

## Retain Cycle (iOS) — tương đương trong Dart

Dart dùng garbage collector nên không có retain cycle như Swift/ObjC. Nhưng vẫn có **circular reference** gây chậm GC:

```dart
// Circular reference — GC khó thu hồi
class NodeA {
  NodeB? other;
}

class NodeB {
  NodeA? other;
}

final a = NodeA();
final b = NodeB();
a.other = b;
b.other = a; // vòng tròn → GC cần mark-and-sweep thay vì reference counting
```

---

## Câu hỏi phỏng vấn thường gặp

**Q: Sự khác biệt giữa `dispose()` và `close()` trong BLoC?**
> `dispose()` là lifecycle method của `State<T>` trong Flutter — dọn dẹp controllers, subscriptions. `close()` là method của `BlocBase` — đóng Stream bên trong BLoC/Cubit. `BlocProvider` tự gọi `close()` khi widget bị remove khỏi tree.

**Q: Làm thế nào tránh leak khi dùng Timer?**
> Lưu reference vào field, gọi `timer.cancel()` trong `dispose()`. Hoặc dùng `Timer.periodic` với điều kiện tự cancel: `if (!mounted) { timer.cancel(); return; }`.

**Q: `const` widget giúp gì cho memory?**
> `const` widget được tạo một lần và tái sử dụng — Flutter không tạo instance mới mỗi lần rebuild. Giảm số lần allocation → ít GC pressure hơn. Toàn bộ subtree `const` được skip trong quá trình rebuild.

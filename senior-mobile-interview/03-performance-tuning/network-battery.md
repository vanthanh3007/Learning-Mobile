# Network & Battery Optimization

## Nguyên tắc chung

> Mỗi network request = pin hao + data tốn + latency tăng. Mục tiêu: **làm ít request nhất, mỗi request nhỏ nhất**.

---

## Tối ưu Network

### 1. Request Batching & Deduplication

```dart
// ❌ SAI — nhiều widget cùng request user profile
// Widget A: api.getUserProfile('123')
// Widget B: api.getUserProfile('123')  ← request trùng!
// Widget C: api.getUserProfile('123')  ← request trùng!

// ✅ ĐÚNG — deduplicate bằng in-flight cache
class ApiService {
  final Map<String, Future> _inFlight = {};

  Future<T> deduplicate<T>(String key, Future<T> Function() request) {
    if (_inFlight.containsKey(key)) {
      return _inFlight[key] as Future<T>; // trả về future đang chạy
    }
    final future = request().whenComplete(() => _inFlight.remove(key));
    _inFlight[key] = future;
    return future;
  }
}

// Sử dụng
Future<User> getUser(String id) => apiService.deduplicate(
  'user_$id',
  () => dio.get('/users/$id').then((r) => User.fromJson(r.data)),
);
```

### 2. Connection Pool — Tái dụng HTTP connection

```dart
// Dio tự động dùng keep-alive — tái sử dụng TCP connection
// Không nên tạo nhiều Dio instance
// ✅ Tạo một Dio singleton, tái dùng toàn app
final dio = Dio()
  ..options.connectTimeout = Duration(seconds: 10)
  ..options.receiveTimeout = Duration(seconds: 30)
  ..options.headers['Connection'] = 'keep-alive';
```

### 3. Exponential Backoff khi retry

```dart
Future<T> retryWithBackoff<T>(Future<T> Function() request) async {
  int attempt = 0;
  while (true) {
    try {
      return await request();
    } catch (e) {
      attempt++;
      if (attempt >= 3) rethrow;
      // Backoff: 1s, 2s, 4s
      await Future.delayed(Duration(seconds: pow(2, attempt - 1).toInt()));
    }
  }
}
```

### 4. Compress request body

```dart
// Gzip request với Dio
import 'dart:io';
import 'dart:convert';

final compressed = GZipCodec().encode(utf8.encode(jsonEncode(data)));
await dio.post(
  '/data',
  data: Stream.fromIterable([compressed]),
  options: Options(
    headers: {'Content-Encoding': 'gzip'},
    contentType: 'application/json',
  ),
);
```

---

## Image Optimization

### Chọn format đúng

| Format | Kích thước                     | Dùng cho                               |
| ------ | ------------------------------ | -------------------------------------- |
| WebP   | Nhỏ nhất (25-30% nhỏ hơn JPEG) | Ảnh thường, thumbnail                  |
| JPEG   | Trung bình                     | Ảnh thực, không cần transparent        |
| PNG    | Lớn nhất                       | Cần transparent, icon                  |
| SVG    | Nhỏ                            | Icon, illustration đơn giản            |
| AVIF   | Rất nhỏ                        | Mới, không phải server nào cũng hỗ trợ |

### Responsive images

```dart
// Request đúng size cần thiết, không load 4K cho thumbnail
String getImageUrl(String baseUrl, double width) {
  final pixelRatio = WidgetsBinding.instance.window.devicePixelRatio;
  final targetWidth = (width * pixelRatio).round();
  return '$baseUrl?w=$targetWidth&format=webp&quality=80';
}

// Dùng trong widget
LayoutBuilder(
  builder: (context, constraints) => CachedNetworkImage(
    imageUrl: getImageUrl(product.imageUrl, constraints.maxWidth),
  ),
)
```

---

## Battery Optimization

### 1. Giảm Wakelock

```dart
// ❌ Giữ màn hình sáng khi không cần
WakelockPlus.enable(); // chỉ dùng khi thực sự cần (video, navigation)

// ✅ Enable/disable theo context
@override
void initState() {
  if (widget.isVideoPlaying) WakelockPlus.enable();
}

@override
void dispose() {
  WakelockPlus.disable();
  super.dispose();
}
```

### 2. Location tracking tiết kiệm pin

```dart
// ❌ High accuracy liên tục → hao pin cực nhiều
LocationSettings(accuracy: LocationAccuracy.best)

// ✅ Giảm accuracy khi không cần
LocationSettings(
  accuracy: LocationAccuracy.reduced, // dùng cell tower, không GPS
  distanceFilter: 50, // chỉ update khi di chuyển > 50m
)

// ✅ Dùng significant location change khi chỉ cần city-level
// iOS: startMonitoringSignificantLocationChanges()
// Android: thông qua geofencing
```

### 3. Polling vs Push

```dart
// ❌ Polling mỗi 30 giây — hao pin, hao data
Timer.periodic(Duration(seconds: 30), (_) => fetchNotifications());

// ✅ Push notification — server chủ động push khi có data mới
// Firebase Cloud Messaging: app không làm gì cho đến khi nhận push
FirebaseMessaging.onMessage.listen((message) {
  // Chỉ wake up khi có notification thực sự
  handleNewMessage(message);
});
```

### 4. Sensor usage

```dart
// ❌ Lắng nghe accelerometer liên tục
accelerometerEvents.listen((event) { ... });

// ✅ Unsubscribe khi không cần
StreamSubscription? _sub;

void startListening() {
  _sub = accelerometerEvents.listen((event) {
    if (detected) _sub?.cancel(); // dừng khi đã detect
  });
}
```

---

## Câu hỏi phỏng vấn thường gặp

**Q: App của bạn tốn nhiều pin. Bạn debug như thế nào?**

> Bước 1: Dùng Android Battery Historian hoặc Xcode Energy Report để xem battery breakdown (network, CPU, GPS, wakelock). Bước 2: Identify service nào tốn nhiều nhất. Bước 3: Giảm polling frequency, chuyển sang push, giảm location accuracy, cancel subscription không dùng.

**Q: HTTP/2 giúp gì cho mobile?**

> Multiplexing — nhiều request trên cùng 1 TCP connection (không cần tạo nhiều connection như HTTP/1.1). Header compression — request nhỏ hơn. Server push — server có thể gửi response trước khi client request. Giảm latency, tốt cho battery vì ít TCP handshake hơn.

**Q: Làm thế nào giảm app startup time?**

> Lazy init các service không cần ngay, defer background task sau khi UI render xong, dùng splash screen để ẩn init time, precompile shader (flutter build với --bundle-sksl-path), giảm main() work trước runApp().

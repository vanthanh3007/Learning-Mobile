# Background Processing

## Thách thức trên Mobile

Hệ điều hành mobile **kill background process** để tiết kiệm pin và RAM. Điều này có nghĩa:
- App không thể chạy mãi mãi nền
- iOS giới hạn rất nghiêm ngặt hơn Android
- Cần dùng API chính thức của OS để đảm bảo task được chạy

---

## Các loại Background Task

| Loại | Ví dụ | Flutter solution |
|---|---|---|
| One-off task | Upload file, sync data | `workmanager` |
| Periodic task | Check notification mỗi 15 phút | `workmanager` |
| Long-running | Music playback, location tracking | Foreground Service |
| Scheduled | Reminder, alarm | `flutter_local_notifications` |
| Push-triggered | Process push notification | Firebase FCM |

---

## WorkManager trong Flutter

```dart
// Đăng ký task
void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  Workmanager().initialize(
    callbackDispatcher,
    isInDebugMode: false,
  );

  runApp(MyApp());
}

// Callback chạy khi OS kích hoạt task — phải là top-level function
@pragma('vm:entry-point')
void callbackDispatcher() {
  Workmanager().executeTask((taskName, inputData) async {
    switch (taskName) {
      case 'syncDataTask':
        await syncDataToServer(inputData?['userId']);
        break;
      case 'cleanCacheTask':
        await cleanOldCache();
        break;
    }
    return Future.value(true); // true = success, false = retry
  });
}
```

```dart
// Đăng ký one-off task
Workmanager().registerOneOffTask(
  'syncNow',
  'syncDataTask',
  inputData: {'userId': '123'},
  constraints: Constraints(
    networkType: NetworkType.connected, // chỉ chạy khi có mạng
    requiresBatteryNotLow: true,        // không chạy khi pin yếu
  ),
);

// Đăng ký periodic task (minimum 15 phút trên Android)
Workmanager().registerPeriodicTask(
  'periodicSync',
  'syncDataTask',
  frequency: Duration(hours: 1),
  constraints: Constraints(
    networkType: NetworkType.connected,
  ),
);
```

---

## Foreground Service — cho task dài

Khi cần chạy task lâu và user cần biết (GPS tracking, download lớn):

```dart
// flutter_foreground_task
Future<void> startTrackingService() async {
  await FlutterForegroundTask.startService(
    notificationTitle: 'Đang theo dõi vị trí',
    notificationText: 'Nhấn để dừng',
    callback: startLocationTracking,
  );
}

@pragma('vm:entry-point')
void startLocationTracking() {
  FlutterForegroundTask.setTaskHandler(LocationTaskHandler());
}

class LocationTaskHandler extends TaskHandler {
  @override
  Future<void> onStart(DateTime timestamp, SendPort? sendPort) async {
    // Khởi tạo
  }

  @override
  Future<void> onEvent(DateTime timestamp, SendPort? sendPort) async {
    // Chạy định kỳ — gửi location về UI
    final location = await getLocation();
    sendPort?.send(location);
  }

  @override
  Future<void> onDestroy(DateTime timestamp, FlutterForegroundTask? task) async {
    // Cleanup
  }
}
```

---

## Isolate — chạy code nặng không block UI

```dart
// Tính toán nặng (parse JSON lớn, xử lý ảnh) → chạy trong Isolate
Future<List<Product>> parseProductsInBackground(String jsonString) async {
  return await compute(
    _parseProducts, // function phải là top-level hoặc static
    jsonString,
  );
}

// Top-level function — chạy trong Isolate riêng
List<Product> _parseProducts(String jsonString) {
  final list = jsonDecode(jsonString) as List;
  return list.map((e) => Product.fromJson(e)).toList();
}
```

```dart
// Isolate phức tạp hơn với 2 chiều communication
Future<void> heavyTask() async {
  final receivePort = ReceivePort();

  await Isolate.spawn((SendPort sendPort) {
    // Chạy trong Isolate riêng
    final result = doHeavyCalculation();
    sendPort.send(result);
  }, receivePort.sendPort);

  final result = await receivePort.first;
  print('Result: $result');
}
```

---

## iOS vs Android — điểm khác biệt quan trọng

| | **Android** | **iOS** |
|---|---|---|
| Background task tối thiểu | ~15 phút | ~15 phút (không đảm bảo) |
| Foreground service | Cho phép | Rất hạn chế |
| Battery optimization | Có thể bypass | Không thể bypass |
| Background location | Cần permission | Cần permission, giới hạn hơn |
| App bị kill | Ít hơn | Nhiều hơn (Aggressive) |

---

## Câu hỏi phỏng vấn thường gặp

**Q: Tại sao không dùng Timer cho background task?**
> Timer chỉ chạy khi app đang active. Khi OS suspend app, Timer dừng. WorkManager dùng native API của OS (WorkManager Android, BGTaskScheduler iOS) nên được OS bảo đảm chạy dù app đóng.

**Q: Làm thế nào không hao pin khi track GPS liên tục?**
> Dùng significant location change (mỗi ~500m thay vì real-time), giảm accuracy khi không cần, dùng geofencing thay vì polling, batch location updates thay vì gửi từng điểm. Tránh Isolate chạy liên tục — dùng foreground service với notification.

**Q: compute() khác Isolate.spawn() như thế nào?**
> `compute()` là wrapper đơn giản của Isolate, nhận 1 function + 1 argument, trả về 1 kết quả. Phù hợp cho one-shot computation. `Isolate.spawn()` cho phép 2 chiều communication qua SendPort/ReceivePort, phù hợp cho long-running tasks cần giao tiếp liên tục với main isolate.

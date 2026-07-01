# Caching & Offline Mode

## Tại sao cần Offline Mode?

- Người dùng ở vùng mạng kém (tàu điện, thang máy, nông thôn)
- Trải nghiệm mượt mà hơn — hiển thị data cached trong khi fetch mới
- Giảm tải server và tiết kiệm bandwidth

---

## Các tầng Cache

```
Request → Memory Cache → Disk Cache → Network
                ↑               ↑
           (nhanh nhất)    (persist qua app restart)
```

### 1. Memory Cache (in-memory, mất khi app close)
```dart
class InMemoryCache<T> {
  final Map<String, T> _store = {};
  final Map<String, DateTime> _expiry = {};

  void set(String key, T value, {Duration ttl = const Duration(minutes: 5)}) {
    _store[key] = value;
    _expiry[key] = DateTime.now().add(ttl);
  }

  T? get(String key) {
    if (_expiry[key]?.isAfter(DateTime.now()) == true) {
      return _store[key];
    }
    _store.remove(key);
    return null;
  }
}
```

### 2. Disk Cache (persist qua app restart)
```dart
// Dùng Hive — nhanh, key-value
final box = await Hive.openBox<String>('products_cache');
await box.put('product_list', jsonEncode(products));
final cached = box.get('product_list');
```

---

## Chiến lược Cache phổ biến

### Cache-First (Offline-first)
```dart
Future<List<Product>> getProducts() async {
  // 1. Đọc cache trước
  final cached = await local.getProducts();
  if (cached.isNotEmpty) {
    emit(ProductsLoaded(cached)); // show ngay
  }

  // 2. Fetch network song song
  try {
    final fresh = await remote.fetchProducts();
    await local.saveProducts(fresh); // update cache
    emit(ProductsLoaded(fresh)); // update UI
  } catch (_) {
    // Nếu network lỗi, vẫn có cached data → không crash
    if (cached.isEmpty) emit(ProductsError('No internet'));
  }
}
```

### Network-First (luôn fresh nhất có thể)
```dart
Future<List<Product>> getProducts() async {
  try {
    final fresh = await remote.fetchProducts();
    await local.saveProducts(fresh);
    return fresh;
  } catch (_) {
    return local.getProducts(); // fallback
  }
}
```

### Stale-While-Revalidate
```
1. Trả về cached (dù cũ) → UI hiện ngay
2. Fetch network background
3. Khi network về → update UI silently
```

---

## Đồng bộ dữ liệu khi mất mạng

### Optimistic Update
```dart
// Update UI ngay, không chờ API
Future<void> likePost(String postId) async {
  // 1. Update UI ngay
  final updated = state.posts.map((p) =>
    p.id == postId ? p.copyWith(liked: true, likeCount: p.likeCount + 1) : p
  ).toList();
  emit(PostsLoaded(updated));

  // 2. Gửi API
  try {
    await api.likePost(postId);
  } catch (_) {
    // Rollback nếu thất bại
    emit(PostsLoaded(state.posts)); // state cũ
    showError('Không thể thích bài này');
  }
}
```

### Sync Queue — Queue các action khi offline
```dart
class SyncQueue {
  final LocalStorage storage;

  Future<void> enqueue(SyncAction action) async {
    final queue = await storage.getQueue();
    queue.add(action);
    await storage.saveQueue(queue);
  }

  Future<void> processQueue() async {
    final queue = await storage.getQueue();
    for (final action in queue) {
      try {
        await _execute(action);
        queue.remove(action);
      } catch (_) {
        break; // dừng nếu gặp lỗi, retry sau
      }
    }
    await storage.saveQueue(queue);
  }
}

// Khi có mạng trở lại
connectivity.onConnectivityChanged.listen((status) {
  if (status != ConnectivityResult.none) {
    syncQueue.processQueue();
  }
});
```

---

## Local Storage Options trong Flutter

| | **Hive** | **Isar** | **SQLite (sqflite)** | **SharedPreferences** |
|---|---|---|---|---|
| Loại | Key-value (NoSQL) | NoSQL | Relational SQL | Key-value |
| Performance | Rất nhanh | Rất nhanh | Trung bình | Chậm |
| Query phức tạp | Không | Có | Có | Không |
| Type safe | Có (code gen) | Có (code gen) | Không | Không |
| Dùng cho | Cache, settings | App data phức tạp | Data quan hệ | Settings đơn giản |

---

## Câu hỏi phỏng vấn thường gặp

**Q: Cache invalidation strategy của bạn là gì?**
> TTL (time-to-live) cho data thay đổi thường xuyên. Version-based invalidation khi có breaking change. Event-based invalidation khi có action thay đổi data (tạo order → invalidate cart cache).

**Q: Làm thế nào handle conflict khi offline user thay đổi data mà server cũng thay đổi?**
> Last-write-wins (đơn giản nhưng có thể mất data), server-wins (bỏ local change), merge strategy (CRDT cho collaborative apps). Hầu hết mobile app dùng last-write-wins với timestamp, kèm notify user nếu conflict.

**Q: Khi nào không nên cache?**
> Data nhạy cảm (OTP, payment info), data real-time (stock prices, live scores), data cá nhân hóa cao thay đổi liên tục. Cache sai loại data có thể gây security issue hoặc UX tệ hơn.

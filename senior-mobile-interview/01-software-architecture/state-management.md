# State Management — Senior Level

## Tư duy Senior về State Management

Senior không hỏi "dùng cái gì" — họ hỏi:
- **Bạn chọn X vì lý do gì?**
- **Trade-off là gì?**
- **App scale lên 50 màn hình thì architecture có còn hold không?**

---

## So sánh toàn diện

| Tiêu chí | GetX | Provider | BLoC/Cubit | Riverpod |
|---|---|---|---|---|
| Boilerplate | Rất ít | Ít | Nhiều | Ít-vừa |
| Testability | Kém | Tốt | Rất tốt | Rất tốt |
| Scalability | Kém | Trung bình | Tốt | Tốt |
| Type safety | Thấp | Trung bình | Cao | Rất cao |
| Learning curve | Dễ | Dễ | Khó | Trung bình |
| Community | Lớn | Lớn | Lớn | Đang tăng |
| Được Flutter team recommend | Không | Có | Có | Không chính thức |

---

## Memory Leak trong State Management

### Nguyên nhân phổ biến

**1. Không dispose StreamSubscription**
```dart
// ❌ SAI — leak stream
class MyWidget extends StatefulWidget { ... }
class _MyState extends State<MyWidget> {
  StreamSubscription? _sub;

  @override
  void initState() {
    _sub = someStream.listen((_) { ... }); // không bao giờ cancel
  }
  // QUÊN dispose → leak
}

// ✅ ĐÚNG
@override
void dispose() {
  _sub?.cancel();
  super.dispose();
}
```

**2. BLoC/Cubit không được close**
```dart
// ❌ SAI — dùng BlocProvider.value mà cubit do bên ngoài quản lý
// nhưng bên ngoài không close nó

// ✅ ĐÚNG — BlocProvider tự close khi widget bị remove
BlocProvider(
  create: (_) => MyCubit(), // BlocProvider chịu trách nhiệm dispose
  child: MyWidget(),
)
```

**3. BuildContext sau async gap**
```dart
// ❌ SAI — context có thể đã unmount sau await
Future<void> doSomething(BuildContext context) async {
  await Future.delayed(Duration(seconds: 2));
  Navigator.of(context).pop(); // context có thể không còn valid
}

// ✅ ĐÚNG — check mounted trước khi dùng context
Future<void> doSomething(BuildContext context) async {
  await Future.delayed(Duration(seconds: 2));
  if (!context.mounted) return;
  Navigator.of(context).pop();
}
```

---

## Global vs Local State — Decision Tree

```
State này có cần chia sẻ giữa nhiều màn hình?
├── Có → Global State (BLocProvider ở root, Get.put permanent)
└── Không → State này có thay đổi UI không?
            ├── Có → Local State (setState, Cubit scoped)
            └── Không → const / final (không cần state)
```

### Ví dụ phân loại

| State | Loại | Lý do |
|---|---|---|
| User đã đăng nhập chưa | Global | Mọi màn hình cần biết |
| Giỏ hàng | Global | Persist khi navigate |
| Loading button | Local | Chỉ button đó cần biết |
| Nội dung form | Local | Chỉ form đó dùng |
| Dark/Light theme | Global | Áp dụng toàn app |
| Tab đang active | Local | Chỉ widget tab bar đó |

---

## Đồng bộ state và tránh race condition

### Vấn đề: Nhiều request cùng lúc

```dart
// ❌ Có thể race condition
Future<void> search(String query) async {
  emit(Loading());
  final result = await api.search(query); // request 1
  emit(Loaded(result)); // result của request nào về trước?
}
```

### Giải pháp: Cancel request cũ

```dart
// ✅ Dùng debounce + cancel token (với Dio)
CancelToken? _cancelToken;

Future<void> search(String query) async {
  _cancelToken?.cancel(); // hủy request trước
  _cancelToken = CancelToken();

  emit(Loading());
  try {
    final result = await api.search(query, cancelToken: _cancelToken);
    emit(Loaded(result));
  } on DioException catch (e) {
    if (!e.type == DioExceptionType.cancel) {
      emit(Error(e.message));
    }
  }
}
```

---

## Câu hỏi phỏng vấn thường gặp

**Q: Tại sao không dùng GetX cho project lớn?**
> GetX gộp state management + navigation + DI vào một package — quá nhiều responsibility. Khó test vì tight coupling. Khi team lớn, convention không rõ ràng dẫn đến code không nhất quán.

**Q: Riverpod khác Provider ở điểm gì?**
> Riverpod không phụ thuộc BuildContext, type-safe hơn, hỗ trợ async tốt hơn, có thể override provider trong test dễ dàng. Provider dễ bị ProviderNotFoundException runtime; Riverpod bắt lỗi compile time.

**Q: Khi nào dùng BlocListener thay vì BlocBuilder?**
> BlocListener cho side effects (navigate, show dialog, snackbar) mà không rebuild UI. BlocBuilder cho rebuild UI. BlocConsumer khi cần cả hai. Dùng sai → rebuild UI không cần thiết hoặc side effect chạy nhiều lần.

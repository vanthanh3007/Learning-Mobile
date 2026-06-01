# Flutter Interview Questions — Middle Level

---

## PHẦN 1: DART FUNDAMENTALS

### 1.1. Null Safety

**Q: Dart null safety là gì? Giải thích `?`, `!`, `late`, `required`.**

```dart
// Nullable — có thể null
String? name; // mặc định = null

// Non-nullable — KHÔNG thể null
String title = 'Hello';

// Late — khai báo sau, nhưng đảm bảo sẽ có giá trị trước khi dùng
late String description;

// Force unwrap — "tôi chắc chắn nó không null"
String value = name!; // nếu null → runtime crash

// Required — bắt buộc truyền vào
void greet({required String name}) {}
```

**Câu bẫy:** `late` không phải nullable. Nếu truy cập `late` variable trước khi gán → `LateInitializationError`.

---

### 1.2. `final` vs `const`

**Q: Khác biệt giữa `final` và `const`?**

| | `final` | `const` |
|---|---|---|
| Gán giá trị | 1 lần, tại **runtime** | 1 lần, tại **compile-time** |
| Ví dụ | `final now = DateTime.now();` | `const pi = 3.14;` |
| Trong class | Có thể dùng instance variable | Phải là `static const` |
| Collection | Bản thân biến immutable, items vẫn mutable | Cả collection đều immutable |

```dart
final list1 = [1, 2, 3];
list1.add(4); // OK — list vẫn mutable

const list2 = [1, 2, 3];
list2.add(4); // ERROR — không thể modify
```

---

### 1.3. Async/Await, Future, Stream

**Q: Giải thích sự khác nhau giữa Future và Stream?**

```dart
// Future — trả về 1 giá trị duy nhất trong tương lai
Future<String> fetchUser() async {
  final response = await http.get('/user');
  return response.body;
}

// Stream — trả về nhiều giá trị theo thời gian
Stream<int> countDown(int from) async* {
  for (int i = from; i >= 0; i--) {
    await Future.delayed(Duration(seconds: 1));
    yield i;  // phát ra từng giá trị
  }
}
```

| | Future | Stream |
|---|---|---|
| Giá trị | 1 lần | Nhiều lần |
| Lắng nghe | `await` / `.then()` | `.listen()` / `StreamBuilder` |
| Ví dụ | API call | WebSocket, Firebase realtime |

**Q: `async*` và `yield` là gì?**
- `async*` đánh dấu function trả về Stream
- `yield` phát ra 1 giá trị vào Stream
- `yield*` forward toàn bộ Stream khác

---

### 1.4. Isolates

**Q: Isolate là gì? Khi nào dùng?**

- Dart là **single-threaded**, chạy trên 1 event loop
- **Isolate** = thread riêng biệt, có **memory riêng** (không share memory)
- Giao tiếp giữa các isolate qua **message passing** (SendPort/ReceivePort)

```dart
// Cách đơn giản nhất — compute()
final result = await compute(expensiveFunction, data);

// Khi nào dùng Isolate?
// - Parse JSON lớn (>1MB)
// - Xử lý ảnh
// - Tính toán phức tạp
// - Mã hóa/giải mã

// KHÔNG cần Isolate cho:
// - API call (đã async, không block UI)
// - Đọc file nhỏ
```

**Câu bẫy:** Isolate KHÔNG share memory → không thể truyền object có reference phức tạp. Chỉ truyền được primitive types và một số types đơn giản.

---

### 1.5. Extension, Mixin, Abstract class

**Q: So sánh Mixin vs Abstract class vs Extension?**

```dart
// Abstract class — định nghĩa contract, có thể có implementation
abstract class Animal {
  void breathe() => print('breathing...'); // có implementation
  void makeSound(); // bắt buộc override
}

// Mixin — chia sẻ behavior, KHÔNG CÓ constructor
mixin Swimmable {
  void swim() => print('swimming...');
}

// Kết hợp
class Duck extends Animal with Swimmable {
  @override
  void makeSound() => print('quack!');
}

// Extension — thêm method vào class có sẵn mà KHÔNG sửa source
extension StringX on String {
  bool get isEmail => contains('@');
}

'test@mail.com'.isEmail; // true
```

| | Abstract class | Mixin | Extension |
|---|---|---|---|
| Constructor | Có | **Không** | Không |
| Kế thừa | `extends` (1 class) | `with` (nhiều mixin) | Không kế thừa |
| Mục đích | Định nghĩa contract | Chia sẻ behavior | Mở rộng class có sẵn |

---

### 1.6. Generics

**Q: Generics dùng để làm gì? Cho ví dụ thực tế.**

```dart
// API Response wrapper
class ApiResponse<T> {
  final T? data;
  final String? error;
  final bool success;

  ApiResponse.success(this.data) : error = null, success = true;
  ApiResponse.failure(this.error) : data = null, success = false;
}

// Sử dụng
ApiResponse<User> userResponse = await fetchUser();
ApiResponse<List<Product>> productsResponse = await fetchProducts();

// Generic với constraint
class Repository<T extends BaseModel> {
  Future<T> getById(String id) { ... }
  Future<List<T>> getAll() { ... }
}
```

---

## PHẦN 2: FLUTTER CORE

### 2.1. Widget Tree — Element Tree — Render Tree

**Q: Giải thích 3 trees trong Flutter.**

```
Widget Tree          Element Tree         RenderObject Tree
(Blueprint)          (Instance)           (Layout & Paint)
────────────         ────────────         ──────────────────
MaterialApp    →     ComponentElement  →   (không render)
  Scaffold     →     ComponentElement  →   RenderFlex
    Column     →     RenderElement     →   RenderFlex
      Text     →     RenderElement     →   RenderParagraph
      Icon     →     RenderElement     →   RenderCustomPaint
```

- **Widget**: immutable, chỉ là mô tả (blueprint). Được tạo lại liên tục
- **Element**: instance thực tế, quản lý lifecycle, được tái sử dụng
- **RenderObject**: thực hiện layout, painting, hit testing

**Câu bẫy:** Khi `setState()`, widget rebuild KHÔNG có nghĩa tạo lại element. Flutter so sánh widget cũ vs mới (bằng `runtimeType` + `key`) → nếu giống thì **update element**, không tạo mới.

---

### 2.2. StatelessWidget vs StatefulWidget

**Q: Khi nào dùng StatelessWidget, khi nào StatefulWidget?**

```dart
// Stateless — không có state nội bộ, chỉ phụ thuộc vào input
class UserAvatar extends StatelessWidget {
  final String imageUrl;
  const UserAvatar({required this.imageUrl});

  @override
  Widget build(BuildContext context) {
    return CircleAvatar(backgroundImage: NetworkImage(imageUrl));
  }
}

// Stateful — có state nội bộ, thay đổi theo thời gian
class LikeButton extends StatefulWidget {
  @override
  State<LikeButton> createState() => _LikeButtonState();
}

class _LikeButtonState extends State<LikeButton> {
  bool isLiked = false;

  @override
  Widget build(BuildContext context) {
    return IconButton(
      icon: Icon(isLiked ? Icons.favorite : Icons.favorite_border),
      onPressed: () => setState(() => isLiked = !isLiked),
    );
  }
}
```

**Level Middle cần biết thêm:**
- `setState()` trigger rebuild toàn bộ widget subtree → cần tối ưu
- Khi dùng state management (Bloc, Riverpod...) thì hầu hết widget là Stateless

---

### 2.3. Key trong Flutter

**Q: Key dùng để làm gì? Khi nào cần dùng?**

```dart
// KHÔNG có key — Flutter match widget theo index
// → Khi reorder list, state bị lẫn lộn!
ListView(
  children: items.map((item) => ListTile(title: Text(item))).toList(),
);

// CÓ key — Flutter match đúng widget
ListView(
  children: items.map((item) => ListTile(
    key: ValueKey(item.id),  // ← quan trọng!
    title: Text(item.name),
  )).toList(),
);
```

**Các loại Key:**
| Key | Khi nào dùng |
|---|---|
| `ValueKey` | Khi có giá trị unique (id, email) |
| `ObjectKey` | Khi object là unique identifier |
| `UniqueKey` | Force tạo mới widget mỗi lần build |
| `GlobalKey` | Truy cập state/context từ bên ngoài (dùng hạn chế) |

**Khi nào BẮT BUỘC dùng Key:**
- List có thể **reorder, thêm, xóa** items
- Widget cùng type nằm cạnh nhau và có state riêng
- `AnimatedSwitcher` cần biết widget đã thay đổi

---

### 2.4. BuildContext

**Q: BuildContext là gì?**

- BuildContext = **vị trí của widget trong Element Tree**
- Mỗi widget có 1 context riêng
- Dùng để **truy cập lên trên tree** (Theme, MediaQuery, Navigator, Provider...)

```dart
// Lấy theme
Theme.of(context).primaryColor;

// Lấy screen size
MediaQuery.of(context).size;

// Navigate
Navigator.of(context).push(...);

// Provider
Provider.of<UserModel>(context);
// hoặc
context.read<UserModel>();
context.watch<UserModel>();
```

**Câu bẫy phổ biến:**
```dart
// SAI — dùng context trước khi widget được mount
@override
void initState() {
  super.initState();
  // context chưa sẵn sàng cho InheritedWidget
  final user = Provider.of<User>(context); // có thể lỗi!
}

// ĐÚNG — dùng didChangeDependencies hoặc addPostFrameCallback
@override
void didChangeDependencies() {
  super.didChangeDependencies();
  final user = Provider.of<User>(context);
}
```

---

### 2.5. Widget Lifecycle (StatefulWidget)

**Q: Trình tự lifecycle của StatefulWidget?**

```
createState()
    ↓
initState()          ← Chạy 1 lần, khởi tạo state, subscribe stream
    ↓
didChangeDependencies()  ← Khi InheritedWidget thay đổi
    ↓
build()              ← Tạo widget tree, có thể chạy nhiều lần
    ↓
didUpdateWidget()    ← Khi parent rebuild, widget config thay đổi
    ↓
setState()           ← Trigger rebuild
    ↓
deactivate()         ← Widget bị remove khỏi tree (tạm thời)
    ↓
dispose()            ← Cleanup: cancel stream, dispose controller
```

**Quy tắc quan trọng:**
```dart
@override
void initState() {
  super.initState(); // PHẢI gọi đầu tiên
  _controller = TextEditingController();
  _subscription = stream.listen(...);
}

@override
void dispose() {
  _controller.dispose();    // PHẢI cleanup
  _subscription.cancel();   // tránh memory leak
  super.dispose(); // PHẢI gọi cuối cùng
}
```

---

### 2.6. InheritedWidget

**Q: InheritedWidget hoạt động như thế nào?**

- Cơ chế để **truyền data xuống widget tree** mà không cần truyền qua constructor
- Là nền tảng của `Theme.of()`, `MediaQuery.of()`, `Provider`

```dart
class AppConfig extends InheritedWidget {
  final String apiUrl;

  const AppConfig({
    required this.apiUrl,
    required Widget child,
  }) : super(child: child);

  static AppConfig of(BuildContext context) {
    return context.dependOnInheritedWidgetOfExactType<AppConfig>()!;
  }

  @override
  bool updateShouldNotify(AppConfig oldWidget) {
    return apiUrl != oldWidget.apiUrl;
  }
}

// Sử dụng
final apiUrl = AppConfig.of(context).apiUrl;
```

`updateShouldNotify` quyết định có rebuild dependents hay không.

---

## PHẦN 3: STATE MANAGEMENT

### 3.1. Tổng quan các giải pháp

**Q: So sánh các state management phổ biến trong Flutter?**

| | Bloc/Cubit | Riverpod | GetX | Provider |
|---|---|---|---|---|
| Complexity | Cao | Trung bình | Thấp | Thấp |
| Boilerplate | Nhiều | Ít | Rất ít | Ít |
| Testability | Rất tốt | Rất tốt | Khó | Tốt |
| Scalability | Rất tốt | Rất tốt | Trung bình | Trung bình |
| Learning curve | Cao | Trung bình | Thấp | Thấp |
| Phổ biến tuyển dụng | Rất cao | Cao | Giảm dần | Trung bình |

---

### 3.2. BLoC Pattern (chi tiết)

**Q: Giải thích BLoC pattern. Sự khác biệt giữa Bloc và Cubit?**

```dart
// ========== CUBIT (đơn giản hơn) ==========
class CounterCubit extends Cubit<int> {
  CounterCubit() : super(0); // state khởi tạo = 0

  void increment() => emit(state + 1);
  void decrement() => emit(state - 1);
}

// ========== BLOC (event-driven) ==========

// Events
abstract class CounterEvent {}
class IncrementPressed extends CounterEvent {}
class DecrementPressed extends CounterEvent {}

// State
class CounterState {
  final int count;
  const CounterState(this.count);
}

// Bloc
class CounterBloc extends Bloc<CounterEvent, CounterState> {
  CounterBloc() : super(const CounterState(0)) {
    on<IncrementPressed>((event, emit) {
      emit(CounterState(state.count + 1));
    });
    on<DecrementPressed>((event, emit) {
      emit(CounterState(state.count - 1));
    });
  }
}
```

**Cubit vs Bloc:**
| | Cubit | Bloc |
|---|---|---|
| Input | Gọi method trực tiếp | Dispatch Event |
| Traceability | Thấp hơn | Cao — mọi thay đổi qua Event |
| Boilerplate | Ít | Nhiều hơn |
| Khi nào dùng | Logic đơn giản | Logic phức tạp, cần log event |

```dart
// Sử dụng trong UI
BlocBuilder<CounterBloc, CounterState>(
  builder: (context, state) {
    return Text('${state.count}');
  },
);

// Lắng nghe side effect (show snackbar, navigate...)
BlocListener<AuthBloc, AuthState>(
  listener: (context, state) {
    if (state is AuthError) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(state.message)),
      );
    }
  },
  child: ...,
);

// Kết hợp cả hai
BlocConsumer<AuthBloc, AuthState>(
  listener: (context, state) { /* side effects */ },
  builder: (context, state) { /* UI */ },
);
```

---

### 3.3. Bloc — buildWhen, listenWhen

**Q: `buildWhen` và `listenWhen` dùng để làm gì?**

```dart
BlocBuilder<UserBloc, UserState>(
  // Chỉ rebuild khi tên thay đổi, bỏ qua các state change khác
  buildWhen: (previous, current) {
    return previous.name != current.name;
  },
  builder: (context, state) {
    return Text(state.name);
  },
);

BlocListener<OrderBloc, OrderState>(
  // Chỉ listen khi status thay đổi
  listenWhen: (previous, current) {
    return previous.status != current.status;
  },
  listener: (context, state) {
    if (state.status == OrderStatus.completed) {
      Navigator.of(context).pushNamed('/success');
    }
  },
);
```

→ Giúp **tối ưu performance**, tránh rebuild/listen không cần thiết.

---

### 3.4. Riverpod (nếu dùng)

```dart
// Provider đơn giản
final greetingProvider = Provider<String>((ref) => 'Hello World');

// StateNotifier
class TodoNotifier extends StateNotifier<List<Todo>> {
  TodoNotifier() : super([]);

  void add(Todo todo) {
    state = [...state, todo];
  }

  void remove(String id) {
    state = state.where((t) => t.id != id).toList();
  }
}

final todoProvider = StateNotifierProvider<TodoNotifier, List<Todo>>(
  (ref) => TodoNotifier(),
);

// Sử dụng trong widget
class TodoList extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final todos = ref.watch(todoProvider);
    return ListView(
      children: todos.map((t) => TodoItem(t)).toList(),
    );
  }
}
```

**ref.watch vs ref.read:**
- `ref.watch` — reactive, rebuild khi provider thay đổi (dùng trong `build`)
- `ref.read` — đọc 1 lần, không reactive (dùng trong callbacks, `onPressed`)

---

## PHẦN 4: NAVIGATION

### 4.1. Navigator 1.0 vs 2.0

**Q: Giải thích Navigator trong Flutter.**

```dart
// ===== Navigator 1.0 (imperative) =====
// Push
Navigator.of(context).push(
  MaterialPageRoute(builder: (_) => DetailScreen()),
);

// Push named
Navigator.of(context).pushNamed('/detail', arguments: {'id': 123});

// Pop
Navigator.of(context).pop();

// Push và xóa tất cả route trước đó
Navigator.of(context).pushAndRemoveUntil(
  MaterialPageRoute(builder: (_) => HomeScreen()),
  (route) => false,
);

// Push replacement
Navigator.of(context).pushReplacementNamed('/home');
```

```dart
// ===== Route với go_router (phổ biến hiện tại) =====
final router = GoRouter(
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => HomeScreen(),
      routes: [
        GoRoute(
          path: 'detail/:id',
          builder: (context, state) {
            final id = state.pathParameters['id']!;
            return DetailScreen(id: id);
          },
        ),
      ],
    ),
  ],
);

// Sử dụng
context.go('/detail/123');
context.push('/detail/123');

// go vs push:
// go — thay thế stack (như web URL navigation)
// push — thêm vào stack (có nút back)
```

---

### 4.2. Deep Linking

**Q: Cách handle deep link trong Flutter?**

```dart
// go_router tự hỗ trợ deep link
GoRouter(
  routes: [
    GoRoute(
      path: '/product/:id',
      builder: (context, state) {
        final productId = state.pathParameters['id']!;
        return ProductDetailScreen(id: productId);
      },
    ),
  ],
);

// Android: AndroidManifest.xml
// <intent-filter>
//   <action android:name="android.intent.action.VIEW" />
//   <data android:scheme="myapp" android:host="product" />
// </intent-filter>

// iOS: Info.plist — URL Schemes hoặc Universal Links
```

---

## PHẦN 5: PERFORMANCE OPTIMIZATION

### 5.1. Các nguyên tắc tối ưu

**Q: Làm sao tối ưu performance Flutter app?**

```dart
// 1. CONST CONSTRUCTOR — tránh rebuild không cần thiết
// SAI
Container(
  child: Text('Hello'),
)

// ĐÚNG
const SizedBox(height: 16), // const widget không bao giờ rebuild

// 2. TÁCH WIDGET NHỎ — thay vì 1 widget lớn với setState
// SAI — rebuild toàn bộ screen khi chỉ counter thay đổi
class MyScreen extends StatefulWidget { ... }

// ĐÚNG — tách phần thay đổi ra widget riêng
class CounterDisplay extends StatefulWidget { ... }

// 3. LISTVIEW.BUILDER — thay vì ListView thường cho list dài
// SAI — render ALL items
ListView(
  children: items.map((i) => ItemWidget(i)).toList(),
);

// ĐÚNG — chỉ render items visible trên màn hình
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) => ItemWidget(items[index]),
);

// 4. CACHE IMAGE
CachedNetworkImage(
  imageUrl: url,
  placeholder: (context, url) => CircularProgressIndicator(),
  errorWidget: (context, url, error) => Icon(Icons.error),
);

// 5. REPAINT BOUNDARY — isolate repaint area
RepaintBoundary(
  child: ComplexAnimationWidget(),
);
```

---

### 5.2. Jank & Performance Profiling

**Q: Jank là gì? Cách detect và fix?**

- Flutter target **60fps** (hoặc 120fps trên high-refresh devices)
- Mỗi frame = **16ms** để build + render
- Nếu vượt 16ms → **jank** (frame drop, UI giật)

**Nguyên nhân phổ biến:**
1. Build method quá nặng
2. Tính toán phức tạp trên main isolate
3. Quá nhiều widget rebuild không cần thiết
4. Image không optimize (size quá lớn)
5. Shader compilation jank (lần đầu chạy animation)

**Cách fix:**
```dart
// Dùng DevTools Performance tab
// Dùng Profile mode (không phải Debug mode) để đo
// flutter run --profile

// SkSL warmup để fix shader jank
// flutter run --profile --cache-sksl
// flutter build apk --bundle-sksl-path=flutter_01.sksl.json
```

---

## PHẦN 6: NETWORKING & DATA

### 6.1. HTTP & API

**Q: Cách tổ chức networking layer?**

```dart
// Base API client
class ApiClient {
  final Dio _dio;

  ApiClient() : _dio = Dio(BaseOptions(
    baseUrl: 'https://api.example.com',
    connectTimeout: Duration(seconds: 10),
    receiveTimeout: Duration(seconds: 10),
  )) {
    _dio.interceptors.addAll([
      AuthInterceptor(),
      LogInterceptor(),
      RetryInterceptor(),
    ]);
  }

  Future<Response> get(String path, {Map<String, dynamic>? params}) {
    return _dio.get(path, queryParameters: params);
  }
}

// Interceptor ví dụ
class AuthInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final token = getToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    if (err.response?.statusCode == 401) {
      // Refresh token logic
    }
    handler.next(err);
  }
}
```

---

### 6.2. JSON Serialization

```dart
// Dùng json_serializable + build_runner
@JsonSerializable()
class User {
  final int id;
  final String name;

  @JsonKey(name: 'created_at')
  final DateTime createdAt;

  User({required this.id, required this.name, required this.createdAt});

  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
  Map<String, dynamic> toJson() => _$UserToJson(this);
}

// Hoặc dùng freezed (khuyên dùng)
@freezed
class User with _$User {
  const factory User({
    required int id,
    required String name,
    @JsonKey(name: 'created_at') required DateTime createdAt,
  }) = _User;

  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);
}
// freezed tự generate: ==, hashCode, copyWith, toString
```

---

### 6.3. Local Storage

**Q: Các cách lưu trữ dữ liệu local trong Flutter?**

| Cách | Khi nào dùng |
|---|---|
| `SharedPreferences` | Key-value đơn giản (settings, token) |
| `Hive` | NoSQL, nhanh, structured data |
| `sqflite` / `drift` | SQL, relational data, query phức tạp |
| `secure_storage` | Dữ liệu nhạy cảm (token, password) |
| File | Ảnh, document, large binary |

```dart
// SharedPreferences
final prefs = await SharedPreferences.getInstance();
await prefs.setString('token', 'abc123');
final token = prefs.getString('token');

// Secure Storage
final storage = FlutterSecureStorage();
await storage.write(key: 'token', value: 'abc123');
final token = await storage.read(key: 'token');
```

---

## PHẦN 7: PLATFORM-SPECIFIC

### 7.1. Platform Channel

**Q: Cách giao tiếp giữa Flutter và Native code?**

```dart
// Flutter side
class BatteryService {
  static const platform = MethodChannel('com.app/battery');

  Future<int> getBatteryLevel() async {
    try {
      final int level = await platform.invokeMethod('getBatteryLevel');
      return level;
    } on PlatformException catch (e) {
      throw Exception('Failed: ${e.message}');
    }
  }
}

// Android side (Kotlin)
// class MainActivity : FlutterActivity() {
//   override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
//     MethodChannel(flutterEngine.dartExecutor, "com.app/battery")
//       .setMethodCallHandler { call, result ->
//         if (call.method == "getBatteryLevel") {
//           result.success(getBatteryLevel())
//         } else {
//           result.notImplemented()
//         }
//       }
//   }
// }
```

**Các loại Channel:**
- `MethodChannel` — gọi method, nhận kết quả (phổ biến nhất)
- `EventChannel` — stream data từ native → Flutter
- `BasicMessageChannel` — message đơn giản

---

### 7.2. Platform-specific UI

```dart
// Check platform
import 'dart:io';

if (Platform.isIOS) {
  // Cupertino style
} else if (Platform.isAndroid) {
  // Material style
}

// Hoặc dùng adaptive widgets
Switch.adaptive(value: val, onChanged: onChanged);
// → Material Switch trên Android, CupertinoSwitch trên iOS
```

---

## PHẦN 8: TESTING

### 8.1. Các loại test

**Q: Giải thích các loại test trong Flutter.**

```dart
// 1. UNIT TEST
test('Counter increments', () {
  final counter = Counter();
  counter.increment();
  expect(counter.value, 1);
});

// 2. WIDGET TEST
testWidgets('MyWidget shows title', (tester) async {
  await tester.pumpWidget(MaterialApp(
    home: MyWidget(title: 'Hello'),
  ));

  expect(find.text('Hello'), findsOneWidget);

  await tester.tap(find.byType(ElevatedButton));
  await tester.pump(); // rebuild

  expect(find.text('Clicked!'), findsOneWidget);
});

// 3. BLOC TEST (dùng bloc_test package)
blocTest<CounterBloc, int>(
  'emits [1] when increment is added',
  build: () => CounterBloc(),
  act: (bloc) => bloc.add(IncrementPressed()),
  expect: () => [1],
);

// 4. INTEGRATION TEST
// test/integration_test/app_test.dart
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('full app flow', (tester) async {
    await tester.pumpWidget(MyApp());
    await tester.pumpAndSettle();

    await tester.tap(find.text('Login'));
    await tester.pumpAndSettle();

    expect(find.text('Home'), findsOneWidget);
  });
}
```

---

### 8.2. Mocking

```dart
// Dùng Mockito
@GenerateMocks([UserRepository])
void main() {
  late MockUserRepository mockRepo;

  setUp(() {
    mockRepo = MockUserRepository();
  });

  test('fetch user returns user', () async {
    when(mockRepo.getUser(1)).thenAnswer(
      (_) async => User(id: 1, name: 'John'),
    );

    final user = await mockRepo.getUser(1);
    expect(user.name, 'John');
    verify(mockRepo.getUser(1)).called(1);
  });
}
```

---

## PHẦN 9: ARCHITECTURE

### 9.1. Clean Architecture

**Q: Giải thích cấu trúc project Flutter theo Clean Architecture.**

```
lib/
├── core/
│   ├── error/           # Exceptions, Failures
│   ├── network/         # API client, interceptors
│   ├── utils/           # Constants, helpers
│   └── di/              # Dependency injection (get_it)
│
├── features/
│   └── auth/
│       ├── data/
│       │   ├── models/        # JSON ↔ Object (extends Entity)
│       │   ├── datasources/   # API calls, local DB
│       │   └── repositories/  # Implementation
│       │
│       ├── domain/
│       │   ├── entities/      # Business objects (pure Dart)
│       │   ├── repositories/  # Abstract contract
│       │   └── usecases/      # Business logic
│       │
│       └── presentation/
│           ├── bloc/          # State management
│           ├── pages/         # Screens
│           └── widgets/       # Reusable UI components
```

**Data flow:**
```
UI → Bloc → UseCase → Repository(abstract) → DataSource
                            ↑
                    Repository(impl)
```

---

### 9.2. Dependency Injection

```dart
// Dùng get_it
final sl = GetIt.instance;

void init() {
  // Bloc
  sl.registerFactory(() => AuthBloc(loginUseCase: sl()));

  // Use cases
  sl.registerLazySingleton(() => LoginUseCase(sl()));

  // Repository
  sl.registerLazySingleton<AuthRepository>(
    () => AuthRepositoryImpl(remoteDataSource: sl(), localDataSource: sl()),
  );

  // Data sources
  sl.registerLazySingleton<AuthRemoteDataSource>(
    () => AuthRemoteDataSourceImpl(client: sl()),
  );

  // External
  sl.registerLazySingleton(() => Dio());
}
```

---

## PHẦN 10: CÂU HỎI TÌNH HUỐNG THỰC TẾ

### Q1: App bị jank khi scroll list với nhiều ảnh. Bạn sẽ xử lý thế nào?

**Trả lời mẫu:**
1. Dùng `ListView.builder` (lazy loading) thay vì `ListView`
2. Dùng `CachedNetworkImage` để cache ảnh
3. Resize ảnh từ server (thumbnail cho list, full cho detail)
4. Thêm `RepaintBoundary` cho mỗi item
5. Dùng `const` constructor cho phần static
6. Kiểm tra bằng DevTools Performance tab (Profile mode)

### Q2: Cách handle authentication flow (token, refresh token)?

**Trả lời mẫu:**
1. Lưu token vào `flutter_secure_storage`
2. Tạo Dio Interceptor:
   - Request: attach token vào header
   - Error 401: tự động refresh token
   - Nếu refresh fail → logout, chuyển về login screen
3. Dùng Bloc để quản lý auth state:
   - `AuthAuthenticated` → show home
   - `AuthUnauthenticated` → show login
4. Wrap MaterialApp với `BlocListener<AuthBloc>` để handle routing

### Q3: Bạn nhận task build app offline-first. Approach thế nào?

**Trả lời mẫu:**
1. Local DB (Hive/Drift) là source of truth
2. Khi có mạng → sync với server
3. Dùng `connectivity_plus` để check network
4. Queue các thao tác offline, sync khi online
5. Handle conflict resolution (last-write-wins hoặc merge)
6. Show UI indicator: online/offline/syncing

### Q4: Khi nào bạn chọn Bloc vs Riverpod vs GetX?

**Trả lời mẫu:**
- **Bloc**: Dự án lớn, team đông, cần strict pattern, dễ test
- **Riverpod**: Dự án vừa-lớn, muốn linh hoạt, compile-time safe
- **GetX**: Prototype nhanh, MVP, nhưng khó maintain khi scale
- Quan trọng nhất: **team quen cái nào, dùng cái đó** — consistency > perfection

### Q5: Build responsive UI cho cả phone và tablet?

**Trả lời mẫu:**
```dart
class ResponsiveLayout extends StatelessWidget {
  final Widget mobile;
  final Widget tablet;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= 768) {
          return tablet;
        }
        return mobile;
      },
    );
  }
}

// Dùng MediaQuery cho adaptive sizing
final screenWidth = MediaQuery.of(context).size.width;
final isTablet = screenWidth >= 768;

// Dùng Flex/Expanded thay vì fixed width
// Dùng FractionallySizedBox cho % width
```

---

## PHẦN 11: CÂU HỎI "BẪY" THƯỜNG GẶP

### Bẫy 1: "Flutter là single-threaded, vậy sao nó mượt?"
→ Dart single-threaded nhưng dùng **event loop** (giống JS). I/O operations (network, file) chạy bên ngoài Dart VM. UI rendering engine (Skia/Impeller) chạy trên thread riêng. Chỉ business logic chạy trên main isolate.

### Bẫy 2: "setState có gì sai?"
→ `setState` không sai, nhưng:
- Rebuild toàn bộ subtree → nếu widget lớn sẽ chậm
- Không chia sẻ state giữa các widget xa nhau
- Khó test business logic

### Bẫy 3: "Hot reload và Hot restart khác gì?"
- **Hot reload**: giữ state, chỉ update code đã thay đổi. Nhanh (~1s)
- **Hot restart**: reset state, compile lại toàn bộ. Chậm hơn (~3-5s)
- Hot reload KHÔNG hoạt động khi: thay đổi main(), thay đổi enum, thay đổi generic types

### Bẫy 4: "Tại sao widget là immutable?"
→ Widget chỉ là **mô tả** (blueprint), không phải UI thực tế. Khi state thay đổi, Flutter tạo widget tree mới → so sánh với cũ (reconciliation) → chỉ update phần khác. Nếu widget mutable → không thể so sánh an toàn.

### Bẫy 5: "Impeller vs Skia?"
- **Skia**: rendering engine cũ, compile shader tại runtime → jank lần đầu
- **Impeller**: engine mới, pre-compile shader → không còn shader jank
- iOS: Impeller là default từ Flutter 3.16
- Android: Impeller đang dần stable

---

## TÓM TẮT: CHECKLIST TRƯỚC PHỎNG VẤN

- [ ] Dart: null safety, async/await, isolate, generics, mixin
- [ ] Widget: StatelessWidget vs StatefulWidget, lifecycle, key, BuildContext
- [ ] 3 Trees: Widget Tree, Element Tree, RenderObject Tree
- [ ] State Management: Bloc/Cubit chi tiết (hoặc Riverpod/GetX tùy JD)
- [ ] Navigation: Navigator 1.0 + go_router
- [ ] Performance: const, ListView.builder, RepaintBoundary, profiling
- [ ] Networking: Dio, interceptors, error handling
- [ ] Architecture: Clean Architecture, DI (get_it)
- [ ] Testing: unit, widget, bloc, integration
- [ ] Platform Channel: MethodChannel, EventChannel
- [ ] CI/CD: build flavors, fastlane, codemagic (biết sơ)

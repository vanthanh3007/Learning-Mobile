# Flutter GetX — Kiến thức chi tiết

## 1. Tổng quan

GetX là một package all-in-one cho Flutter, cung cấp:

| Module | Chức năng |
|--------|----------|
| **State Management** | Reactive & simple state |
| **Route Management** | Navigation không cần context |
| **Dependency Injection** | Binding, Get.put, Get.find |
| **Utilities** | Snackbar, Dialog, BottomSheet, i18n, Theme |

```yaml
dependencies:
  get: ^4.6.6
```

---

## 2. State Management

### 2.1 Rx (Reactive) — `.obs`

```dart
class CounterController extends GetxController {
  // Biến reactive
  var count = 0.obs;           // RxInt
  var name = ''.obs;           // RxString
  var isLoading = false.obs;   // RxBool
  var user = Rxn<User>();      // RxNullable
  var items = <String>[].obs;  // RxList

  void increment() => count++;
  void setName(String v) => name.value = v;
  void addItem(String item) => items.add(item);
}
```

#### Obx — rebuild tự động khi `.obs` thay đổi

```dart
Obx(() => Text('Count: ${controller.count}'));

// Chỉ rebuild khi count thay đổi (không cần chỉ định field)
Obx(() => Column(
  children: [
    Text('${controller.count}'),
    Text('${controller.name}'),
  ],
));
```

#### GetX widget — tích hợp controller

```dart
GetX<CounterController>(
  init: CounterController(),
  builder: (controller) => Text('${controller.count}'),
);
```

---

### 2.2 Simple State — `update()`

```dart
class CounterController extends GetxController {
  int count = 0;  // Biến thường, KHÔNG có .obs

  void increment() {
    count++;
    update();          // Thông báo rebuild
    // update(['id1']); // Chỉ rebuild widget có id cụ thể
  }
}
```

```dart
// GetBuilder — chỉ rebuild khi gọi update()
GetBuilder<CounterController>(
  init: CounterController(),
  // id: 'id1',  // Optional: chỉ rebuild khi update(['id1'])
  builder: (controller) => Text('${controller.count}'),
);
```

---

### 2.3 So sánh Obx vs GetBuilder

| | **Obx** | **GetBuilder** |
|--|---------|---------------|
| **Kiểu biến** | `.obs` (Reactive) | Biến thường |
| **Trigger rebuild** | Tự động | Phải gọi `update()` |
| **Hiệu năng** | Tốt (granular) | Tốt (manual control) |
| **Boilerplate** | Ít | Ít |
| **Use case** | Real-time, stream | Form, batch update |

---

## 3. GetxController Lifecycle

```dart
class MyController extends GetxController {
  @override
  void onInit() {
    super.onInit();
    // Khởi tạo, gọi API lần đầu
    fetchData();
  }

  @override
  void onReady() {
    super.onReady();
    // Widget đã render xong — phù hợp cho dialog, navigation
  }

  @override
  void onClose() {
    // Dọn dẹp: cancel stream, dispose controller...
    super.onClose();
  }

  Future<void> fetchData() async { /* ... */ }
}
```

### Workers — lắng nghe thay đổi của Rx

```dart
class MyController extends GetxController {
  var count = 0.obs;
  var query = ''.obs;

  @override
  void onInit() {
    super.onInit();

    // ever: gọi mỗi lần giá trị thay đổi
    ever(count, (value) => print('count changed: $value'));

    // once: chỉ gọi lần đầu tiên
    once(count, (value) => print('first change: $value'));

    // debounce: gọi sau khi ngừng thay đổi N ms
    debounce(query, (value) => search(value),
        time: const Duration(milliseconds: 300));

    // interval: gọi mỗi N ms khi đang thay đổi
    interval(count, (value) => print(value),
        time: const Duration(seconds: 1));
  }
}
```

---

## 4. Dependency Injection

### 4.1 Get.put — tạo và đăng ký ngay

```dart
// Tạo và inject vào memory
final controller = Get.put(CounterController());

// Với tag — dùng khi cần nhiều instance cùng loại
Get.put(CounterController(), tag: 'home');
Get.put(CounterController(), tag: 'profile');

// permanent: không bị xóa khi không dùng
Get.put(AuthController(), permanent: true);
```

### 4.2 Get.lazyPut — tạo khi cần

```dart
// Chỉ tạo instance khi lần đầu gọi Get.find
Get.lazyPut(() => CounterController());

// fenix: tự tạo lại sau khi bị xóa
Get.lazyPut(() => CounterController(), fenix: true);
```

### 4.3 Get.find — lấy instance đã đăng ký

```dart
final controller = Get.find<CounterController>();
final homeController = Get.find<CounterController>(tag: 'home');
```

### 4.4 Get.create — luôn tạo instance mới

```dart
Get.create(() => CounterController());
// Mỗi lần Get.find() → trả về instance mới
```

### 4.5 Bindings — tổ chức DI theo route

```dart
class HomeBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut(() => HomeController());
    Get.lazyPut(() => UserRepository());
  }
}

// Gắn vào route
GetPage(
  name: '/home',
  page: () => HomePage(),
  binding: HomeBinding(),
)
// Controller tự động inject khi vào trang, xóa khi rời trang
```

### 4.6 BindingsBuilder — inline binding

```dart
GetPage(
  name: '/home',
  page: () => HomePage(),
  binding: BindingsBuilder(() {
    Get.lazyPut(() => HomeController());
  }),
)
```

---

## 5. Route Management

### 5.1 Cấu hình

```dart
void main() => runApp(
  GetMaterialApp(
    initialRoute: '/home',
    getPages: [
      GetPage(name: '/home', page: () => HomePage(), binding: HomeBinding()),
      GetPage(name: '/profile', page: () => ProfilePage()),
      GetPage(name: '/login', page: () => LoginPage()),
      GetPage(
        name: '/detail/:id',         // Route param
        page: () => DetailPage(),
        transition: Transition.rightToLeft,
      ),
    ],
    unknownRoute: GetPage(name: '/404', page: () => NotFoundPage()),
  ),
);
```

### 5.2 Navigation API

```dart
// Push
Get.to(() => ProfilePage());
Get.toNamed('/profile');

// Push với arguments
Get.toNamed('/detail/123');
Get.toNamed('/profile', arguments: {'userId': '123'});

// Replace (không thể back)
Get.off(() => HomePage());
Get.offNamed('/home');

// Clear stack + push (dùng sau login/logout)
Get.offAll(() => HomePage());
Get.offAllNamed('/home');

// Back
Get.back();
Get.back(result: 'data');   // Trả data về trang trước

// Close snackbar/dialog/bottomsheet
Get.close(1);
```

### 5.3 Nhận arguments & params

```dart
class DetailPage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    // Route params: /detail/:id
    final id = Get.parameters['id'];

    // Arguments
    final args = Get.arguments as Map;
    final userId = args['userId'];

    return Text('ID: $id');
  }
}
```

### 5.4 Navigation trong Controller

```dart
class AuthController extends GetxController {
  Future<void> login(String email, String password) async {
    final success = await _authRepo.login(email, password);
    if (success) {
      Get.offAllNamed('/home');
    } else {
      Get.snackbar('Lỗi', 'Sai email hoặc mật khẩu');
    }
  }
}
```

---

## 6. Utilities

### 6.1 Snackbar

```dart
Get.snackbar(
  'Tiêu đề',
  'Nội dung thông báo',
  snackPosition: SnackPosition.BOTTOM,
  backgroundColor: Colors.green,
  colorText: Colors.white,
  duration: const Duration(seconds: 3),
  icon: const Icon(Icons.check, color: Colors.white),
  mainButton: TextButton(
    onPressed: () {},
    child: const Text('Hoàn tác', style: TextStyle(color: Colors.white)),
  ),
);

// Shorthand
Get.showSnackbar(GetSnackBar(title: 'Hello', message: 'World'));
```

### 6.2 Dialog

```dart
// Default dialog
Get.defaultDialog(
  title: 'Xác nhận',
  content: const Text('Bạn chắc chắn muốn xóa?'),
  textConfirm: 'Xóa',
  textCancel: 'Hủy',
  onConfirm: () {
    // xử lý
    Get.back();
  },
);

// Custom dialog
Get.dialog(
  AlertDialog(
    title: const Text('Custom Dialog'),
    content: const Text('Nội dung'),
  ),
  barrierDismissible: false,
);
```

### 6.3 BottomSheet

```dart
Get.bottomSheet(
  Container(
    height: 300,
    color: Colors.white,
    child: Column(
      children: [
        ListTile(
          leading: const Icon(Icons.share),
          title: const Text('Chia sẻ'),
          onTap: () => Get.back(),
        ),
        ListTile(
          leading: const Icon(Icons.delete),
          title: const Text('Xóa'),
          onTap: () => Get.back(),
        ),
      ],
    ),
  ),
  isScrollControlled: true,
);
```

---

## 7. GetConnect — HTTP Client

```dart
class ApiProvider extends GetConnect {
  @override
  void onInit() {
    httpClient.baseUrl = 'https://api.example.com';
    httpClient.defaultContentType = 'application/json';

    // Interceptor — thêm token vào header
    httpClient.addRequestModifier<void>((request) {
      request.headers['Authorization'] = 'Bearer ${GetStorage().read('token')}';
      return request;
    });

    // Interceptor — xử lý response
    httpClient.addResponseModifier((request, response) {
      if (response.statusCode == 401) {
        Get.offAllNamed('/login');
      }
      return response;
    });
  }

  Future<Response<List<User>>> getUsers() => get('/users');
  Future<Response<User>> createUser(User user) => post('/users', user.toJson());
  Future<Response<User>> updateUser(User user) => put('/users/${user.id}', user.toJson());
  Future<Response> deleteUser(String id) => delete('/users/$id');
}
```

---

## 8. Internationalisation (i18n)

```dart
class AppTranslations extends Translations {
  @override
  Map<String, Map<String, String>> get keys => {
    'en_US': {
      'hello': 'Hello',
      'greeting': 'Hello @name!',
    },
    'vi_VN': {
      'hello': 'Xin chào',
      'greeting': 'Xin chào @name!',
    },
  };
}

// Cấu hình
GetMaterialApp(
  translations: AppTranslations(),
  locale: const Locale('vi', 'VN'),
  fallbackLocale: const Locale('en', 'US'),
)

// Dùng
Text('hello'.tr);
Text('greeting'.trParams({'name': 'Minh'}));

// Đổi ngôn ngữ
Get.updateLocale(const Locale('en', 'US'));
```

---

## 9. GetStorage — Local Storage

```dart
import 'package:get_storage/get_storage.dart';

// Khởi tạo trong main()
await GetStorage.init();

final box = GetStorage();

// Ghi
box.write('token', 'abc123');
box.write('user', {'id': 1, 'name': 'Minh'});

// Đọc
final token = box.read<String>('token');
final user = box.read('user');

// Xóa
box.remove('token');
box.erase(); // Xóa tất cả

// Lắng nghe thay đổi
box.listenKey('token', (value) => print('Token changed: $value'));
```

---

## 10. GetX Service — Singleton dài hạn

```dart
class AuthService extends GetxService {
  var isLoggedIn = false.obs;
  var currentUser = Rxn<User>();

  Future<AuthService> init() async {
    // Restore session từ storage
    final token = GetStorage().read<String>('token');
    if (token != null) {
      isLoggedIn.value = true;
    }
    return this;
  }
}

// Đăng ký trong main() — tồn tại suốt vòng đời app
void main() async {
  await Get.putAsync(() => AuthService().init());
  runApp(MyApp());
}

// Lấy ra dùng
final auth = Get.find<AuthService>();
```

---

## 11. Reactive Extensions nâng cao

```dart
var count = 0.obs;
var name = ''.obs;
var items = <String>[].obs;

// Kết hợp nhiều Rx
// Dùng Obx(() => ...) — tự động track tất cả .obs bên trong

// Map
var doubled = count.value * 2; // trong Obx sẽ auto update

// List operations
items.add('item');
items.addAll(['a', 'b']);
items.remove('item');
items.clear();
items.refresh(); // Trigger rebuild dù nội dung không đổi

// Custom Rx class
class User {
  String name;
  int age;
  User(this.name, this.age);
}

var user = User('Minh', 25).obs;
user.update((val) {
  val?.name = 'Nam';  // Mutate in place + notify
});
user.value = User('Nam', 30); // Replace entirely
```

---

## 12. Testing với GetX

```dart
void main() {
  group('CounterController', () {
    late CounterController controller;

    setUp(() {
      Get.testMode = true;  // Bật test mode
      controller = Get.put(CounterController());
    });

    tearDown(() => Get.reset()); // Xóa tất cả instances

    test('initial count is 0', () {
      expect(controller.count.value, 0);
    });

    test('increment increases count', () {
      controller.increment();
      expect(controller.count.value, 1);
    });
  });
}
```

---

## 13. Kiến trúc thực tế với GetX

```
lib/
├── app/
│   ├── bindings/
│   │   └── initial_binding.dart   ← Services, Global DI
│   ├── routes/
│   │   ├── app_pages.dart         ← Danh sách GetPage
│   │   └── app_routes.dart        ← Tên routes (constants)
│   └── modules/
│       ├── home/
│       │   ├── bindings/
│       │   │   └── home_binding.dart
│       │   ├── controllers/
│       │   │   └── home_controller.dart
│       │   └── views/
│       │       └── home_view.dart
│       └── auth/
│           ├── bindings/
│           ├── controllers/
│           └── views/
├── data/
│   ├── models/
│   ├── providers/          ← GetConnect
│   └── repositories/
└── core/
    ├── services/            ← GetxService
    ├── theme/
    └── utils/
```

---

## 14. So sánh GetX vs BLoC vs Riverpod

| Tiêu chí | GetX | BLoC | Riverpod |
|---------|------|------|---------|
| **Learning curve** | Thấp | Cao | Trung bình |
| **Boilerplate** | Rất ít | Nhiều | Trung bình |
| **Tính năng** | All-in-one | State only | State + DI |
| **Testability** | Trung bình | Rất tốt | Rất tốt |
| **Scalability** | Tốt | Rất tốt | Rất tốt |
| **Community** | Lớn | Rất lớn | Lớn |
| **Type safety** | Trung bình | Cao | Rất cao |
| **Separation of concerns** | Ít nghiêm ngặt | Nghiêm ngặt | Nghiêm ngặt |

---

## 15. Các lỗi thường gặp

| Lỗi | Nguyên nhân | Cách sửa |
|-----|------------|---------|
| `"CounterController" not found` | Chưa `Get.put` hoặc Binding | Kiểm tra Binding hoặc gọi `Get.put` |
| UI không update | Dùng `update()` nhưng không có `GetBuilder` | Kiểm tra loại widget hoặc đổi sang `.obs` |
| Memory leak | Controller không được xóa | Dùng Binding để auto-dispose |
| `Cannot navigate without context` | Dùng Navigator thay vì Get | Dùng `Get.to()`, `Get.toNamed()` |
| Circular dependency | A phụ thuộc B, B phụ thuộc A | Refactor dùng Service hoặc event |

---

## 16. Best Practices

- **Dùng Bindings** — để auto inject và dispose controller theo route
- **Ưu tiên `GetxService`** cho global state tồn tại lâu dài
- **Tách rõ logic** — Controller chỉ chứa business logic, View chỉ chứa UI
- **Không dùng context** trong Controller — dùng `Get.snackbar`, `Get.dialog`
- **`Get.lazyPut` với `fenix: true`** khi cần tạo lại controller sau dispose
- **Test mode** — luôn gọi `Get.testMode = true` và `Get.reset()` trong tests
- **Tránh lạm dụng `.obs`** cho những giá trị không cần reactive

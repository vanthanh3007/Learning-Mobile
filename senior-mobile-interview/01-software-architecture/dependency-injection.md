# Dependency Injection (DI)

## DI là gì?

Thay vì class tự tạo dependency của nó, dependency được **truyền vào từ bên ngoài**.

```dart
// ❌ Không dùng DI — tight coupling
class ProductCubit extends Cubit<ProductState> {
  final repo = ProductRepositoryImpl(); // tự tạo → không thể mock trong test
}

// ✅ Dùng DI — loose coupling
class ProductCubit extends Cubit<ProductState> {
  final ProductRepository repo; // nhận từ bên ngoài → dễ mock, dễ swap
  ProductCubit(this.repo) : super(ProductInitial());
}
```

---

## Các cách DI trong Flutter

### 1. GetIt (Service Locator) — phổ biến nhất

```dart
// setup — thường ở main.dart hoặc injection.dart
final getIt = GetIt.instance;

void setupDI() {
  // Singleton — 1 instance duy nhất suốt app
  getIt.registerSingleton<ApiService>(ApiService());

  // LazySingleton — tạo khi lần đầu Get.find
  getIt.registerLazySingleton<AuthRepository>(
    () => AuthRepositoryImpl(getIt<ApiService>()),
  );

  // Factory — tạo mới mỗi lần Get.find
  getIt.registerFactory<LoginCubit>(
    () => LoginCubit(getIt<AuthRepository>()),
  );
}
```

```dart
// Sử dụng
final cubit = getIt<LoginCubit>();
```

### 2. Injectable (code generation trên GetIt)

```dart
// Tự động generate boilerplate bằng annotation
@injectable
class AuthRepositoryImpl implements AuthRepository {
  final ApiService api;
  AuthRepositoryImpl(this.api); // auto inject
}

@injectable
class LoginCubit extends Cubit<LoginState> {
  final AuthRepository repo;
  LoginCubit(this.repo) : super(LoginInitial());
}
```

### 3. GetX Bindings

```dart
class HomeBinding extends Bindings {
  @override
  void dependencies() {
    Get.lazyPut(() => HomeCubit(Get.find<ProductRepository>()));
  }
}
```

### 4. BlocProvider (cho BLoC ecosystem)

```dart
BlocProvider(
  create: (context) => ProductCubit(
    getIt<GetProductsUseCase>(), // lấy từ GetIt
  ),
  child: ProductScreen(),
)
```

---

## Singleton vs Factory vs LazySingleton

| Loại | Tạo khi nào | Số lượng instance | Dùng cho |
|---|---|---|---|
| `Singleton` | Khi đăng ký | 1 | ApiService, Database |
| `LazySingleton` | Lần đầu `find()` | 1 | Repository, UseCase |
| `Factory` | Mỗi lần `find()` | Nhiều | Cubit, ViewModel |

```dart
// Singleton — tạo ngay, phù hợp cho service cần init sớm
getIt.registerSingleton<Dio>(Dio()..options.baseUrl = 'https://api.example.com');

// LazySingleton — tạo khi cần, tiết kiệm memory khi startup
getIt.registerLazySingleton<UserRepository>(
  () => UserRepositoryImpl(getIt<Dio>()),
);

// Factory — mỗi màn hình cần Cubit mới, tránh state cũ
getIt.registerFactory<CartCubit>(
  () => CartCubit(getIt<CartRepository>()),
);
```

---

## DI trong Testing

```dart
// Swap implementation trong test — không thể làm nếu không có DI
void main() {
  setUp(() {
    getIt.registerFactory<ProductRepository>(
      () => MockProductRepository(), // dùng mock thay vì real
    );
  });

  test('load products', () async {
    final cubit = ProductCubit(getIt<ProductRepository>());
    // test...
  });
}
```

---

## Câu hỏi phỏng vấn thường gặp

**Q: Sự khác biệt giữa Service Locator và Dependency Injection thuần?**
> Service Locator (GetIt) — class chủ động gọi `getIt.find()` để lấy dependency. DI thuần — dependency được inject qua constructor, class không biết container tồn tại. DI thuần testable hơn, nhưng cần framework hỗ trợ (Dagger/Hilt trên Android). Flutter thường dùng GetIt vì đơn giản và không cần code generation bắt buộc.

**Q: Vì sao không nên dùng global variable thay cho DI?**
> Global variable không thể swap trong test, không quản lý vòng đời, gây coupling ngầm giữa các class. DI explicit và có thể override.

**Q: `registerSingleton` vs `registerLazySingleton` — khi nào quan trọng?**
> Khi app có nhiều service nặng, `registerSingleton` khởi tạo tất cả lúc startup → chậm. `registerLazySingleton` trì hoãn đến khi cần → startup nhanh hơn. Với service cần warm-up sớm (Firebase, analytics) thì dùng `registerSingleton`.

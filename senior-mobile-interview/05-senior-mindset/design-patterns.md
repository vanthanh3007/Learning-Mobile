# Design Patterns & SOLID

## SOLID Principles

### S — Single Responsibility
> Mỗi class chỉ có một lý do để thay đổi.

```dart
// ❌ SAI — 1 class làm quá nhiều thứ
class UserManager {
  void login(String email, String password) { ... }
  void logout() { ... }
  void sendEmail(String to, String body) { ... }  // sai chỗ
  void saveToDatabase(User user) { ... }           // sai chỗ
  void generateReport() { ... }                    // sai chỗ
}

// ✅ ĐÚNG — mỗi class 1 responsibility
class AuthService { void login(...); void logout(); }
class EmailService { void send(String to, String body); }
class UserRepository { void save(User user); }
class ReportGenerator { void generate(); }
```

### O — Open/Closed
> Open for extension, Closed for modification.

```dart
// ❌ SAI — mỗi lần thêm payment method phải sửa class cũ
class PaymentService {
  void pay(String method, double amount) {
    if (method == 'credit_card') { /* ... */ }
    else if (method == 'paypal') { /* ... */ }
    // thêm method mới → sửa code cũ → risk regression
  }
}

// ✅ ĐÚNG — extend không modify
abstract class PaymentMethod {
  void pay(double amount);
}

class CreditCard implements PaymentMethod {
  @override void pay(double amount) { /* ... */ }
}

class PayPal implements PaymentMethod {
  @override void pay(double amount) { /* ... */ }
}

// Thêm ZaloPay chỉ cần thêm class mới — không sửa code cũ
class ZaloPay implements PaymentMethod {
  @override void pay(double amount) { /* ... */ }
}
```

### L — Liskov Substitution
> Subclass phải hoạt động đúng khi thay thế parent class.

```dart
// ❌ SAI — Square extend Rectangle nhưng vi phạm behavior
class Rectangle {
  double width, height;
  double get area => width * height;
}

class Square extends Rectangle {
  @override
  set width(double v) { super.width = v; super.height = v; } // phá vỡ contract
}

// ✅ ĐÚNG — dùng interface chung
abstract class Shape {
  double get area;
}

class Rectangle implements Shape {
  final double width, height;
  @override double get area => width * height;
}

class Square implements Shape {
  final double side;
  @override double get area => side * side;
}
```

### I — Interface Segregation
> Đừng bắt client implement method họ không dùng.

```dart
// ❌ SAI — interface quá béo
abstract class Animal {
  void eat();
  void fly();   // không phải con vật nào cũng bay được
  void swim();  // không phải con vật nào cũng bơi được
}

// ✅ ĐÚNG — tách nhỏ interface
abstract class CanEat { void eat(); }
abstract class CanFly { void fly(); }
abstract class CanSwim { void swim(); }

class Duck implements CanEat, CanFly, CanSwim { ... }
class Dog implements CanEat, CanSwim { ... }
class Eagle implements CanEat, CanFly { ... }
```

### D — Dependency Inversion
> Depend on abstractions, not concretions.

```dart
// ❌ SAI — depend on concrete class
class OrderService {
  final MySQLDatabase db = MySQLDatabase(); // tight coupling
}

// ✅ ĐÚNG — depend on abstraction
abstract class Database {
  Future<void> save(Map data);
}

class OrderService {
  final Database db; // inject từ ngoài, có thể là MySQL, MongoDB, mock...
  OrderService(this.db);
}
```

---

## Design Patterns phổ biến nhất

### Singleton
```dart
class AppDatabase {
  static AppDatabase? _instance;
  AppDatabase._();

  static AppDatabase get instance {
    _instance ??= AppDatabase._();
    return _instance!;
  }
}
```

### Factory
```dart
abstract class Logger {
  void log(String message);
  factory Logger(String type) {
    switch (type) {
      case 'console': return ConsoleLogger();
      case 'file': return FileLogger();
      default: throw ArgumentError('Unknown logger: $type');
    }
  }
}
```

### Observer (= Stream/BLoC trong Flutter)
```dart
// BLoC là Observer pattern — UI observe State changes
BlocBuilder<CartCubit, CartState>(
  builder: (context, state) => CartBadge(count: state.itemCount),
)
```

### Repository Pattern
```dart
// Abstract interface
abstract class ProductRepository {
  Future<List<Product>> getAll();
  Future<Product> getById(String id);
  Future<void> save(Product product);
}

// Concrete implementations
class RemoteProductRepository implements ProductRepository { ... }
class LocalProductRepository implements ProductRepository { ... }
class CachedProductRepository implements ProductRepository {
  final RemoteProductRepository remote;
  final LocalProductRepository local;
  // Composite — kết hợp 2 source
}
```

### Decorator (dùng trong Interceptor)
```dart
// Interceptor là Decorator pattern
// Bọc thêm behavior (auth, logging, retry) mà không sửa Dio core
dio.interceptors.add(AuthInterceptor());
dio.interceptors.add(LoggingInterceptor());
dio.interceptors.add(RetryInterceptor());
```

---

## Câu hỏi phỏng vấn thường gặp

**Q: Kể ví dụ thực tế bạn áp dụng SOLID trong project?**
> "Tôi tách PaymentService thành interface + implementations riêng (VNPay, ZaloPay, Card). Khi business yêu cầu thêm payment method mới, tôi chỉ thêm class mới mà không sửa code cũ — tránh regression. Đây là Open/Closed Principle."

**Q: Singleton có vấn đề gì không?**
> Khó test vì global state, khó inject mock. Nên dùng DI (GetIt) thay vì Singleton thuần — GetIt cho phép override instance trong test.

**Q: Factory vs Abstract Factory khác nhau thế nào?**
> Factory tạo 1 loại object. Abstract Factory tạo family of related objects. Ví dụ: Factory Method tạo Button; Abstract Factory tạo cả Button + TextField + Dialog theo theme (Material hay Cupertino).

# Clean Architecture & MVVM/MVI

## Tổng quan

Clean Architecture chia app thành 3 lớp độc lập, phụ thuộc một chiều từ ngoài vào trong:

```
┌──────────────────────────────────┐
│  Presentation Layer (UI)         │  ← Widget, Screen, ViewModel
├──────────────────────────────────┤
│  Domain Layer (Business Logic)   │  ← UseCase, Entity, Repository interface
├──────────────────────────────────┤
│  Data Layer (Data Source)        │  ← Repository impl, API, Local DB
└──────────────────────────────────┘

Quy tắc: Lớp trong KHÔNG biết lớp ngoài tồn tại
```

---

## Từng lớp làm gì?

### Presentation Layer
- Chứa UI (Widget, Screen)
- Chứa ViewModel/Cubit/BLoC
- Chỉ gọi UseCase, không gọi trực tiếp Repository hay API
- Không chứa business logic

```dart
// ✅ Đúng — Cubit gọi UseCase
class ProductCubit extends Cubit<ProductState> {
  final GetProductsUseCase getProducts;
  ProductCubit(this.getProducts) : super(ProductInitial());

  Future<void> load() async {
    emit(ProductLoading());
    final result = await getProducts();
    emit(ProductLoaded(result));
  }
}
```

### Domain Layer
- **Entity**: model thuần túy, không phụ thuộc framework
- **UseCase**: 1 class = 1 hành động business
- **Repository interface**: định nghĩa contract, không implement

```dart
// Entity — thuần Dart, không import Flutter/Dio
class Product {
  final String id;
  final String name;
  final double price;
  Product({required this.id, required this.name, required this.price});
}

// Repository interface
abstract class ProductRepository {
  Future<List<Product>> getProducts();
}

// UseCase
class GetProductsUseCase {
  final ProductRepository repo;
  GetProductsUseCase(this.repo);

  Future<List<Product>> call() => repo.getProducts();
}
```

### Data Layer
- **Repository implementation**: implement interface từ Domain
- **Remote data source**: gọi API (Dio, http)
- **Local data source**: đọc/ghi DB (Hive, SQLite)
- **Model**: có thêm `fromJson`/`toJson`, map sang Entity

```dart
// Model (Data layer) — có fromJson
class ProductModel extends Product {
  ProductModel({required super.id, required super.name, required super.price});

  factory ProductModel.fromJson(Map<String, dynamic> json) => ProductModel(
    id: json['id'],
    name: json['name'],
    price: json['price'].toDouble(),
  );
}

// Repository implementation
class ProductRepositoryImpl implements ProductRepository {
  final ProductRemoteDataSource remote;
  final ProductLocalDataSource local;
  ProductRepositoryImpl(this.remote, this.local);

  @override
  Future<List<Product>> getProducts() async {
    try {
      final data = await remote.fetchProducts();
      await local.saveProducts(data);
      return data;
    } catch (_) {
      return local.getProducts(); // fallback offline
    }
  }
}
```

---

## MVVM vs MVI

| | **MVVM** | **MVI** |
|---|---|---|
| Viết tắt | Model-View-ViewModel | Model-View-Intent |
| Data flow | 2 chiều (binding) | 1 chiều (unidirectional) |
| State | Nhiều observable riêng lẻ | 1 object State duy nhất |
| Trong Flutter | GetX Controller | BLoC/Cubit |
| Debug | Khó trace khi phức tạp | Dễ trace — mỗi Intent rõ ràng |

```
MVVM:  View ↔ ViewModel ↔ Model
MVI:   View → Intent → Model → State → View (vòng tròn 1 chiều)
```

---

## Câu hỏi phỏng vấn thường gặp

**Q: Tại sao Domain layer không được import Flutter?**
> Để có thể test pure Dart, không cần Flutter test environment. Và để tách biệt hoàn toàn với framework — mai này đổi sang nền tảng khác, Domain không cần thay đổi.

**Q: Sự khác biệt giữa Entity và Model?**
> Entity là business object thuần túy. Model là Entity + logic serialization (fromJson/toJson) phục vụ data layer. Entity không biết JSON tồn tại.

**Q: UseCase có nhất thiết phải có không?**
> Không bắt buộc cho app nhỏ. Nhưng khi logic phức tạp (combine nhiều repo, có business rule), UseCase giúp tái sử dụng và test độc lập.

**Q: Trade-off của Clean Architecture?**
> Boilerplate nhiều hơn, folder nhiều hơn. App nhỏ sẽ over-engineer. Nhưng với team lớn và app phức tạp, lợi ích về maintainability và testability bù đắp hoàn toàn.

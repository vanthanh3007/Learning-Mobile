# API Optimization

## RESTful vs GraphQL vs gRPC

| | **REST** | **GraphQL** | **gRPC** |
|---|---|---|---|
| Protocol | HTTP/1.1 | HTTP/1.1 | HTTP/2 |
| Data format | JSON | JSON | Protobuf (binary) |
| Over-fetching | Có (nhận cả field không cần) | Không (chọn field) | Không |
| Under-fetching | Có (cần nhiều request) | Không (1 query lấy đủ) | Không |
| Type safety | Không | Có (schema) | Rất cao (proto) |
| Mobile phù hợp | Tốt | Tốt | Tốt (performance cao) |
| Learning curve | Thấp | Trung bình | Cao |
| Dùng khi | API đơn giản, CRUD | Data phức tạp, nhiều client | Microservices, realtime |

---

## Pagination — 3 chiến lược

### 1. Offset Pagination (phổ biến nhất)
```
GET /products?page=2&limit=20
```
```dart
// Cubit
Future<void> loadPage(int page) async {
  final items = await api.getProducts(page: page, limit: 20);
  emit(ProductsLoaded(items));
}
```
**Vấn đề:** Nếu có item mới được thêm vào giữa 2 request → duplicate hoặc skip item.

### 2. Cursor-based Pagination (chuẩn cho infinite scroll)
```
GET /products?cursor=eyJpZCI6MTAwfQ&limit=20
```
```dart
String? _nextCursor;

Future<void> loadMore() async {
  final response = await api.getProducts(cursor: _nextCursor);
  _nextCursor = response.nextCursor;
  emit(ProductsLoaded([...currentItems, ...response.items]));
}
```
**Ưu điểm:** Không bị duplicate/skip khi data thay đổi liên tục (feed, timeline).

### 3. Keyset Pagination
```
GET /products?after_id=100&limit=20
```
Dùng ID hoặc timestamp của item cuối cùng làm anchor. Nhanh hơn offset với database lớn.

---

## Tối ưu Payload

### Compression
```dart
// Dio tự động xử lý gzip nếu server support
final dio = Dio();
dio.options.headers['Accept-Encoding'] = 'gzip, deflate';
```

### Chỉ lấy field cần thiết
```dart
// REST: dùng sparse fieldsets nếu API hỗ trợ
GET /users?fields=id,name,avatar

// GraphQL: mặc định chỉ lấy field request
query {
  user {
    id
    name
    avatar  // không nhận email, phone, address, ...
  }
}
```

### Request batching
```dart
// Thay vì 10 request riêng lẻ
final results = await Future.wait([
  api.getUser(id),
  api.getCart(id),
  api.getNotifications(id),
]); // chạy song song, tổng thời gian = request chậm nhất
```

---

## Interceptor với Dio — pattern chuẩn

```dart
class ApiInterceptor extends Interceptor {
  final TokenStorage tokenStorage;
  final Dio dio;

  ApiInterceptor(this.tokenStorage, this.dio);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final token = tokenStorage.getAccessToken();
    options.headers['Authorization'] = 'Bearer $token';
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401) {
      // Token hết hạn → refresh
      try {
        final newToken = await _refreshToken();
        tokenStorage.saveAccessToken(newToken);

        // Retry request gốc với token mới
        final retryResponse = await dio.fetch(err.requestOptions
          ..headers['Authorization'] = 'Bearer $newToken');
        handler.resolve(retryResponse);
      } catch (_) {
        // Refresh thất bại → logout
        handler.reject(err);
      }
    } else {
      handler.next(err);
    }
  }

  Future<String> _refreshToken() async {
    final refreshToken = tokenStorage.getRefreshToken();
    final response = await dio.post('/auth/refresh',
      data: {'refresh_token': refreshToken},
    );
    return response.data['access_token'];
  }
}
```

---

## Câu hỏi phỏng vấn thường gặp

**Q: Khi nào chọn GraphQL thay vì REST?**
> Khi có nhiều client khác nhau (mobile, web, TV) với nhu cầu data khác nhau. REST dễ over-fetch. GraphQL cho phép mỗi client tự define data cần lấy. Trade-off: phức tạp hơn, cần setup thêm, caching khó hơn.

**Q: Offset pagination có vấn đề gì ở production?**
> Nếu data thay đổi liên tục (user đăng bài mới, item bị xóa), page N không còn consistent giữa 2 lần request. Cursor-based giải quyết được vấn đề này vì dùng ID/timestamp làm anchor thay vì vị trí số học.

**Q: Làm thế nào xử lý concurrent refresh token requests?**
> Dùng mutex/lock: request đầu tiên gặp 401 thực hiện refresh, các request còn lại chờ. Khi refresh xong, tất cả retry cùng lúc với token mới. Nếu không lock, nhiều request sẽ đồng thời refresh → race condition.

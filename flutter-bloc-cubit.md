# Flutter BLoC / Cubit — Kiến thức chi tiết

## 1. Tổng quan

| Khái niệm | Mô tả |
|-----------|------|
| **BLoC** | Business Logic Component — pattern quản lý state dùng Stream |
| **Cubit** | Phiên bản đơn giản hơn của BLoC, không dùng Event |
| **Package** | `flutter_bloc` (bao gồm cả Cubit và BLoC) |
| **Tác giả** | Felix Angelos (felangel) |

---

## 2. Cubit

### 2.1 Cấu trúc cơ bản

```dart
// State
class CounterState {
  final int count;
  const CounterState(this.count);
}

// Cubit
class CounterCubit extends Cubit<CounterState> {
  CounterCubit() : super(const CounterState(0));

  void increment() => emit(CounterState(state.count + 1));
  void decrement() => emit(CounterState(state.count - 1));
  void reset()     => emit(const CounterState(0));
}
```

### 2.2 Khi nào dùng Cubit?
- Logic đơn giản, ít trạng thái
- Không cần trace lịch sử event
- Team nhỏ, tốc độ phát triển nhanh

---

## 3. BLoC

### 3.1 Cấu trúc cơ bản

```dart
// Events
abstract class CounterEvent {}
class IncrementEvent extends CounterEvent {}
class DecrementEvent extends CounterEvent {}
class ResetEvent extends CounterEvent {}

// State
class CounterState {
  final int count;
  const CounterState(this.count);
}

// BLoC
class CounterBloc extends Bloc<CounterEvent, CounterState> {
  CounterBloc() : super(const CounterState(0)) {
    on<IncrementEvent>((event, emit) => emit(CounterState(state.count + 1)));
    on<DecrementEvent>((event, emit) => emit(CounterState(state.count - 1)));
    on<ResetEvent>((event, emit) => emit(const CounterState(0)));
  }
}
```

### 3.2 Khi nào dùng BLoC?
- App lớn, nhiều developer
- Cần audit trail / replay events
- Logic phức tạp, nhiều nguồn event
- Cần test kỹ lưỡng từng event

---

## 4. So sánh Cubit vs BLoC

| Tiêu chí | Cubit | BLoC |
|---------|-------|------|
| **Độ phức tạp** | Đơn giản hơn | Phức tạp hơn |
| **Boilerplate** | Ít | Nhiều |
| **Tracing** | Không có event | Có event đầy đủ |
| **Testability** | Tốt | Rất tốt |
| **Reactivity** | Emit trực tiếp | Thêm event → xử lý |
| **Phù hợp** | App nhỏ/vừa | App lớn, enterprise |

---

## 5. Cung cấp State — Providers

### 5.1 BlocProvider

```dart
// Cung cấp một bloc/cubit mới
BlocProvider(
  create: (context) => CounterCubit(),
  child: MyWidget(),
);

// Cung cấp bloc đã có (không tạo mới)
BlocProvider.value(
  value: existingCubit,
  child: MyWidget(),
);
```

### 5.2 MultiBlocProvider

```dart
MultiBlocProvider(
  providers: [
    BlocProvider(create: (_) => CounterCubit()),
    BlocProvider(create: (_) => AuthBloc()),
    BlocProvider(create: (_) => ThemeBloc()),
  ],
  child: MyApp(),
);
```

### 5.3 RepositoryProvider

```dart
RepositoryProvider(
  create: (context) => UserRepository(),
  child: BlocProvider(
    create: (context) => UserBloc(
      userRepo: context.read<UserRepository>(),
    ),
    child: MyWidget(),
  ),
);
```

---

## 6. Tiêu thụ State — Widgets

### 6.1 BlocBuilder — rebuild UI khi state thay đổi

```dart
BlocBuilder<CounterCubit, CounterState>(
  // buildWhen: chỉ rebuild khi cần thiết
  buildWhen: (previous, current) => previous.count != current.count,
  builder: (context, state) {
    return Text('Count: ${state.count}');
  },
);
```

### 6.2 BlocListener — side-effects (navigation, snackbar...)

```dart
BlocListener<AuthBloc, AuthState>(
  listenWhen: (previous, current) => current is AuthFailure,
  listener: (context, state) {
    if (state is AuthFailure) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(state.message)),
      );
    }
  },
  child: LoginForm(),
);
```

### 6.3 BlocConsumer — kết hợp Builder + Listener

```dart
BlocConsumer<LoginBloc, LoginState>(
  listenWhen: (prev, curr) => curr is LoginSuccess || curr is LoginFailure,
  listener: (context, state) {
    if (state is LoginSuccess) {
      Navigator.pushReplacementNamed(context, '/home');
    } else if (state is LoginFailure) {
      showErrorDialog(context, state.error);
    }
  },
  buildWhen: (prev, curr) => curr is LoginLoading || curr is LoginInitial,
  builder: (context, state) {
    return state is LoginLoading
        ? const CircularProgressIndicator()
        : LoginForm();
  },
);
```

### 6.4 Truy cập bloc không rebuild

```dart
// Đọc bloc mà không lắng nghe thay đổi
final cubit = context.read<CounterCubit>();
cubit.increment();

// Lắng nghe state (gây rebuild)
final state = context.watch<CounterCubit>().state;

// Chọn một phần state
final count = context.select<CounterCubit, int>((c) => c.state.count);
```

---

## 7. State Design Patterns

### 7.1 Sealed class (Dart 3+) — Khuyến nghị

```dart
sealed class AuthState {}

class AuthInitial extends AuthState {}
class AuthLoading extends AuthState {}
class AuthSuccess extends AuthState {
  final User user;
  AuthSuccess(this.user);
}
class AuthFailure extends AuthState {
  final String message;
  AuthFailure(this.message);
}

// Dùng pattern matching
switch (state) {
  case AuthInitial():  // ...
  case AuthLoading():  // ...
  case AuthSuccess(:final user): Text(user.name);
  case AuthFailure(:final message): Text(message);
}
```

### 7.2 Equatable — tránh rebuild thừa

```dart
class CounterState extends Equatable {
  final int count;
  const CounterState(this.count);

  @override
  List<Object?> get props => [count]; // BLoC so sánh props để quyết định emit
}
```

### 7.3 copyWith pattern

```dart
class ProfileState extends Equatable {
  final String name;
  final String email;
  final bool isLoading;

  const ProfileState({
    required this.name,
    required this.email,
    this.isLoading = false,
  });

  ProfileState copyWith({String? name, String? email, bool? isLoading}) {
    return ProfileState(
      name: name ?? this.name,
      email: email ?? this.email,
      isLoading: isLoading ?? this.isLoading,
    );
  }

  @override
  List<Object?> get props => [name, email, isLoading];
}
```

---

## 8. Async trong BLoC/Cubit

```dart
class UserCubit extends Cubit<UserState> {
  final UserRepository _repo;
  UserCubit(this._repo) : super(UserInitial());

  Future<void> fetchUser(String id) async {
    emit(UserLoading());
    try {
      final user = await _repo.getUserById(id);
      emit(UserLoaded(user));
    } catch (e) {
      emit(UserError(e.toString()));
    }
  }
}

// Trong BLoC với transformer
class SearchBloc extends Bloc<SearchEvent, SearchState> {
  SearchBloc() : super(SearchInitial()) {
    on<SearchQueryChanged>(
      _onQueryChanged,
      transformer: debounce(const Duration(milliseconds: 300)),
    );
  }

  Future<void> _onQueryChanged(
    SearchQueryChanged event,
    Emitter<SearchState> emit,
  ) async {
    if (event.query.isEmpty) return emit(SearchInitial());
    emit(SearchLoading());
    try {
      final results = await _searchRepo.search(event.query);
      emit(SearchSuccess(results));
    } catch (e) {
      emit(SearchFailure(e.toString()));
    }
  }
}
```

---

## 9. Event Transformers (BLoC)

```dart
import 'package:bloc_concurrency/bloc_concurrency.dart';

// Sequential: xử lý tuần tự, chờ event trước xong mới xử lý tiếp
on<MyEvent>(_handler, transformer: sequential());

// Droppable: bỏ qua event mới nếu đang xử lý
on<MyEvent>(_handler, transformer: droppable());

// Restartable: hủy event đang xử lý, xử lý event mới
on<MyEvent>(_handler, transformer: restartable());

// Concurrent: xử lý song song (mặc định)
on<MyEvent>(_handler, transformer: concurrent());

// Debounce custom
EventTransformer<T> debounce<T>(Duration duration) {
  return (events, mapper) => events.debounceTime(duration).switchMap(mapper);
}
```

---

## 10. BlocObserver — Global Logging

```dart
class AppBlocObserver extends BlocObserver {
  @override
  void onCreate(BlocBase bloc) {
    super.onCreate(bloc);
    print('onCreate -- ${bloc.runtimeType}');
  }

  @override
  void onEvent(Bloc bloc, Object? event) {
    super.onEvent(bloc, event);
    print('onEvent -- ${bloc.runtimeType}, $event');
  }

  @override
  void onTransition(Bloc bloc, Transition transition) {
    super.onTransition(bloc, transition);
    print('onTransition -- ${bloc.runtimeType}, $transition');
  }

  @override
  void onError(BlocBase bloc, Object error, StackTrace stackTrace) {
    print('onError -- ${bloc.runtimeType}, $error');
    super.onError(bloc, error, stackTrace);
  }

  @override
  void onClose(BlocBase bloc) {
    super.onClose(bloc);
    print('onClose -- ${bloc.runtimeType}');
  }
}

// Đăng ký trong main()
void main() {
  Bloc.observer = AppBlocObserver();
  runApp(MyApp());
}
```

---

## 11. Testing

### 11.1 Test Cubit

```dart
import 'package:bloc_test/bloc_test.dart';

void main() {
  group('CounterCubit', () {
    late CounterCubit cubit;

    setUp(() => cubit = CounterCubit());
    tearDown(() => cubit.close());

    test('initial state is 0', () {
      expect(cubit.state.count, 0);
    });

    blocTest<CounterCubit, CounterState>(
      'increment emits [1]',
      build: () => CounterCubit(),
      act: (cubit) => cubit.increment(),
      expect: () => [const CounterState(1)],
    );

    blocTest<CounterCubit, CounterState>(
      'increment twice emits [1, 2]',
      build: () => CounterCubit(),
      act: (cubit) => cubit
        ..increment()
        ..increment(),
      expect: () => [const CounterState(1), const CounterState(2)],
    );
  });
}
```

### 11.2 Test BLoC với mock

```dart
class MockUserRepository extends Mock implements UserRepository {}

blocTest<UserBloc, UserState>(
  'emits [Loading, Loaded] when FetchUser succeeds',
  setUp: () {
    when(() => mockRepo.getUserById('1'))
        .thenAnswer((_) async => fakeUser);
  },
  build: () => UserBloc(repo: mockRepo),
  act: (bloc) => bloc.add(FetchUserEvent('1')),
  expect: () => [
    UserLoading(),
    UserLoaded(fakeUser),
  ],
  verify: (_) {
    verify(() => mockRepo.getUserById('1')).called(1);
  },
);
```

---

## 12. Kiến trúc theo layer với BLoC

```
lib/
├── core/
│   ├── theme/
│   └── utils/
├── data/
│   ├── models/
│   ├── repositories/        ← implements interfaces
│   └── datasources/
├── domain/
│   ├── entities/
│   ├── repositories/        ← abstract interfaces
│   └── usecases/
└── presentation/
    ├── pages/
    ├── widgets/
    └── blocs/
        ├── auth/
        │   ├── auth_bloc.dart
        │   ├── auth_event.dart
        │   └── auth_state.dart
        └── counter/
            ├── counter_cubit.dart
            └── counter_state.dart
```

---

## 13. Các lỗi thường gặp

| Lỗi | Nguyên nhân | Cách sửa |
|-----|------------|---------|
| `emit() called after close()` | Gọi emit sau khi bloc đã close | Kiểm tra `if (!isClosed) emit(...)` |
| State không update UI | Equatable props sai | Kiểm tra lại `props` list |
| BlocProvider not found | Widget không nằm trong scope | Đặt BlocProvider cao hơn trong tree |
| Rebuild quá nhiều | Không dùng `buildWhen` | Thêm `buildWhen` để filter |
| Stream memory leak | Không close bloc | Dùng `BlocProvider` thay vì tạo manual |

---

## 14. Best Practices

- **State phải Immutable** — không thay đổi trực tiếp, luôn tạo object mới
- **Dùng Equatable** — tránh rebuild khi state không thay đổi
- **Một Bloc/Cubit = một feature** — không gộp nhiều domain vào 1 bloc
- **Repository pattern** — bloc chỉ gọi repository, không gọi HTTP trực tiếp
- **BlocObserver** — log toàn bộ transitions trong dev mode
- **Không đặt BuildContext vào bloc** — vi phạm separation of concerns
- **Dùng `buildWhen`/`listenWhen`** — tối ưu performance

---

## 15. Packages liên quan

```yaml
dependencies:
  flutter_bloc: ^8.1.6
  bloc: ^8.1.4
  equatable: ^2.0.5

dev_dependencies:
  bloc_test: ^9.1.7
  mocktail: ^1.0.4

# Optional
dependencies:
  bloc_concurrency: ^0.2.5    # event transformers
  hydrated_bloc: ^9.1.5       # persist state to disk
  replay_bloc: ^0.2.4         # undo/redo support
```

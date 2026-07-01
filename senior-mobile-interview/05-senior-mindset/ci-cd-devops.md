# CI/CD & DevOps cho Mobile

## CI/CD là gì trong Mobile?

```
Developer push code
        ↓
CI (Continuous Integration)
  ├── Static analysis (dart analyze)
  ├── Unit tests / Widget tests
  ├── Integration tests
  └── Build check (không bị build lỗi)
        ↓
CD (Continuous Delivery/Deployment)
  ├── Build APK/IPA
  ├── Sign app
  ├── Upload lên TestFlight / Firebase App Distribution
  └── (Optional) Submit lên Store
```

---

## GitHub Actions — Flutter

```yaml
# .github/workflows/flutter_ci.yml
name: Flutter CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.16.0'
          channel: 'stable'

      - name: Install dependencies
        run: flutter pub get

      - name: Analyze
        run: flutter analyze

      - name: Run tests
        run: flutter test --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build-android:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: subosito/flutter-action@v2

      - name: Build APK
        run: flutter build apk --release

      - name: Upload APK
        uses: actions/upload-artifact@v3
        with:
          name: release-apk
          path: build/app/outputs/flutter-apk/app-release.apk
```

---

## Fastlane — Tự động hóa deploy

```ruby
# Fastfile
default_platform(:android)

platform :android do
  desc "Run tests"
  lane :test do
    gradle(task: "test")
  end

  desc "Build và upload lên Firebase App Distribution"
  lane :beta do
    gradle(task: "bundle", build_type: "Release")
    firebase_app_distribution(
      app: ENV["FIREBASE_APP_ID"],
      groups: "internal-testers",
      release_notes: "Build từ branch #{git_branch}"
    )
  end

  desc "Submit lên Play Store"
  lane :deploy do
    gradle(task: "bundle", build_type: "Release")
    upload_to_play_store(track: "internal")
  end
end
```

---

## Flavors — Multi-environment

```dart
// Cấu hình khác nhau cho dev/staging/production
enum Flavor { development, staging, production }

class AppConfig {
  final Flavor flavor;
  final String apiBaseUrl;
  final String appName;

  AppConfig._({required this.flavor, required this.apiBaseUrl, required this.appName});

  static late AppConfig _instance;
  static AppConfig get instance => _instance;

  static void setFlavor(Flavor flavor) {
    switch (flavor) {
      case Flavor.development:
        _instance = AppConfig._(
          flavor: flavor,
          apiBaseUrl: 'https://dev-api.example.com',
          appName: 'MyApp Dev',
        );
      case Flavor.staging:
        _instance = AppConfig._(
          flavor: flavor,
          apiBaseUrl: 'https://staging-api.example.com',
          appName: 'MyApp Staging',
        );
      case Flavor.production:
        _instance = AppConfig._(
          flavor: flavor,
          apiBaseUrl: 'https://api.example.com',
          appName: 'MyApp',
        );
    }
  }
}
```

```dart
// main_development.dart
void main() {
  AppConfig.setFlavor(Flavor.development);
  runApp(const MyApp());
}

// main_production.dart
void main() {
  AppConfig.setFlavor(Flavor.production);
  runApp(const MyApp());
}
```

```bash
# Chạy từng flavor
flutter run --flavor development -t lib/main_development.dart
flutter run --flavor production -t lib/main_production.dart
```

---

## App Signing

```bash
# Tạo keystore (Android)
keytool -genkey -v -keystore release.keystore \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias my-key-alias

# key.properties (KHÔNG commit vào git)
storePassword=your_store_password
keyPassword=your_key_password
keyAlias=my-key-alias
storeFile=../release.keystore
```

```groovy
// android/app/build.gradle
def keystoreProperties = new Properties()
keystoreProperties.load(new FileInputStream(rootProject.file('key.properties')))

signingConfigs {
  release {
    keyAlias keystoreProperties['keyAlias']
    keyPassword keystoreProperties['keyPassword']
    storeFile file(keystoreProperties['storeFile'])
    storePassword keystoreProperties['storePassword']
  }
}
```

---

## Câu hỏi phỏng vấn thường gặp

**Q: Làm thế nào bảo vệ API key trong CI/CD?**
> Lưu vào secrets của CI (GitHub Secrets, Bitrise Secrets) — không hardcode trong code. Inject vào build qua environment variables hoặc dart-define. Không bao giờ commit key.properties hay .env vào git.

**Q: Sự khác biệt giữa Firebase App Distribution và TestFlight?**
> Firebase App Distribution: đa nền tảng, free, dễ setup, không cần Apple Developer account cho tester. TestFlight: chỉ iOS/macOS, cần Apple account, tích hợp sâu với App Store Connect, tester nhận notification từ Apple.

**Q: Làm thế nào handle version tự động trong CI?**
> Dùng git tag làm version name, build number từ CI run number hoặc git commit count. `flutter build apk --build-name=1.2.3 --build-number=$GITHUB_RUN_NUMBER`.

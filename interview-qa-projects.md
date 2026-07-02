# Câu hỏi & Trả lời mẫu — Phỏng vấn theo Project

> Mục tiêu: Trả lời câu hỏi kỹ thuật bằng kinh nghiệm thực tế từ project của mình.
> Format trả lời: **STAR** (Situation → Task → Action → Result)

---

## Project: MASU (Ship / Driver / Merchant)

> Hệ sinh thái giao hàng gồm 3 Flutter app. ~641 Dart files. Clean Architecture + BLoC/Cubit + GetX DI.

---

### Kiến trúc

**Q: Bạn tổ chức kiến trúc project Masu như thế nào?**

> "Masu dùng Clean Architecture chia 3 lớp rõ ràng:
> - **UI layer**: Cubit + View, mỗi screen 1 Cubit riêng (scoped)
> - **Repository layer**: abstract interface + implementation tách biệt — dễ swap data source và mock trong test
> - **Service layer**: Retrofit `@RestApi()` code generation, Dio làm HTTP client
>
> DI dùng GetX service locator với `Get.lazyPut(fenix: true)` — Cubit tự tạo lại khi bị dispose, tránh leak state cũ. Routing cũng dùng GetX named routes với enum `ZPRoute` để type-safe."

---

**Q: Tại sao chọn BLoC/Cubit thay vì GetX controller cho state management?**

> "Về mặt kỹ thuật, GetX controller và Cubit đều được dùng trong project — nhưng Cubit là lựa chọn chính vì:
> - Tách biệt rõ state/logic khỏi UI → dễ test độc lập
> - Mỗi Cubit chỉ emit state, không có side effect lẫn lộn
> - Khi team scale lên, convention của BLoC rõ ràng hơn
>
> GetX được giữ cho DI và routing — không dùng GetX controller cho business logic để tránh God object."

---

### Real-time

**Q: Real-time tracking trong Masu implement thế nào?**

> "Dùng **Firebase Realtime Database** thay vì WebSocket tự build. Driver app cập nhật location lên Firebase, Ship app lắng nghe stream thay đổi.
>
> Lý do chọn Firebase Realtime DB:
> - Tự handle reconnect khi mạng không ổn định
> - Offline persistence built-in — ship user vẫn thấy vị trí cuối cùng khi mất mạng
> - Không cần maintain WebSocket server riêng
>
> Trade-off: tốn chi phí Firebase khi scale lớn, nhưng phù hợp với giai đoạn đầu của sản phẩm."

---

**Q: Firebase Realtime Database khác Firestore ở điểm gì? Bạn chọn cái nào và tại sao?**

> "Realtime Database: JSON tree, sync cực nhanh, phù hợp data thay đổi liên tục như location.
> Firestore: document/collection, query mạnh hơn, scale tốt hơn cho data phức tạp.
>
> Masu chọn Realtime Database cho location tracking vì latency thấp hơn và phù hợp với data structure đơn giản (lat/lng update liên tục). Các data khác như order history thì dùng REST API."

---

### Push Notification & Deep Link

**Q: FCM trong Masu xử lý thế nào? Có gặp vấn đề gì không?**

> "Mình build `fcm_configuration.dart` (~200 dòng) handle đủ 3 trường hợp:
> - **Foreground**: `FirebaseMessaging.onMessage` → show local notification
> - **Background**: `onBackgroundMessage` handler (top-level function, không dùng được context)
> - **App bị kill**: notification tap → `getInitialMessage()` → navigate
>
> Vấn đề gặp phải: iOS cần sync APNS token với FCM token — nếu không làm bước này, notification không nhận được trên iOS. Giải quyết bằng cách listen `onTokenRefresh` và sync lên server ngay khi token thay đổi."

---

**Q: Deep link hoạt động như thế nào trong Masu?**

> "Dùng package `app_links` để handle Universal Link (iOS) và App Link (Android).
>
> Flow:
> 1. Notification tap hoặc user click link ngoài → OS mở app với URL
> 2. `RouteUtils` parse URL: `/merchant?MId=X&PId=Y&id=Z`
> 3. Navigate đến đúng màn hình với arguments
>
> Handle 2 case: app đang chạy (`onAppLink` stream) và app vừa mở từ killed state (`getInitialAppLink`). Nếu không handle cả 2 case thì deep link sẽ miss khi app bị kill."

---

### API & Networking

**Q: API layer trong Masu setup như thế nào?**

> "Dùng **Retrofit** code generation (`@RestApi()` annotation) trên Dio. NetworkManager tạo Dio instance với:
> - Timeout 60 giây
> - `PrettyDioLogger` cho debug
> - Custom interceptor tự inject: Bearer token, AppName, AppVersion, OSName, DeviceNumber, UI_TimezoneOffset vào mỗi request
>
> Error handling centralize trong `BaseErrorHandling` — convert DioError thành `BaseError` rồi show dialog. Response chuẩn hóa qua `BaseResponse<T>` với StatusCode, Msg, Data."

---

**Q: Refresh token implement thế nào?**

> "Trong error interceptor, nếu response 401 → gọi refresh token API → update token trong SharedPreferences → retry request gốc với token mới.
>
> Cần handle race condition: nếu nhiều request cùng nhận 401 một lúc → chỉ 1 request được refresh, các request còn lại chờ. Implement bằng flag `_isRefreshing` và queue các request đang pending."

---

### Offline & Connectivity

**Q: Offline mode trong Masu xử lý thế nào?**

> "Dùng `ConnectivityService` (GetxService) listen `connectivity_plus` stream. Khi mất mạng → show dialog cảnh báo để user biết.
>
> Critical data (token, user profile, search history, địa chỉ) được cache trong SharedPreferences → user vẫn thấy thông tin cũ khi offline.
>
> Token được monitor qua Stream — nếu token expired hoặc bị revoke → auto navigate về login, không để user stuck ở màn hình trắng."

---

### Performance & Scale

**Q: Project 641 file, làm sao tránh rebuild widget không cần thiết?**

> "Cubit scoped per screen là key — chỉ widget đang `BlocBuilder<SpecificCubit>` mới rebuild, không ảnh hưởng widget khác.
>
> Các pattern dùng thêm:
> - `const` constructor cho static widget
> - `BlocSelector` khi chỉ cần một field của state thay vì rebuild theo toàn bộ state
> - `RepaintBoundary` cho list item có animation
> - `CachedNetworkImage` với `memCacheWidth/Height` để control memory footprint của ảnh"

---

### Server-driven UI — Carousel & Banner Popup

**Q: Trang chủ Ship app có carousel ảnh — bạn implement như thế nào?**

> "Dùng package `carousel_slider ^4.2.1` kết hợp với dữ liệu lấy từ API `/api/v1/User/HomePage_App`.
>
> Server trả về `configSlide` gồm:
> - Danh sách `Slide` với `SlideImages` (imageUrl, title, moreInfo)
> - `configSlide.slideShow`: số slide hiển thị cùng lúc
> - `configSlide.gapSlide`: khoảng cách giữa các slide
>
> Widget `MasuCarouselSlider` nhận list này và render — hoàn toàn data-driven, không cần update app khi thêm/bớt slide. Thứ tự, nội dung, link click đều do backend kiểm soát."

---

**Q: MasuShip có popup banner quảng cáo — nó hoạt động thế nào?**

> "Dùng class `ZPMarketingManager` (Singleton) quản lý 2 loại banner:
>
> - **BANNER_POPUP**: nổi ở góc màn hình, người dùng có thể kéo di chuyển, khi thả tự snap về góc gần nhất bằng animation
> - **BANNER_CENTER_POPUP**: dạng modal chính giữa màn hình
>
> Toàn bộ config lấy từ `moreInfo.appSetting.configLayoutBanner` trên API — ảnh, vị trí ban đầu, thời gian delay hiện, action khi click (gọi API hoặc navigate), action khi đóng.
>
> Điểm hay: banner không cần hardcode trong app, marketing team có thể đẩy campaign mới mà không cần release. Khi user click/đóng, app có thể gọi API tracking để đo hiệu quả banner."

---

---

## Project: MASU DRIVER

> Flutter app cho tài xế/chủ xe. 578 Dart files, 27 Cubits, 43 screens. Hỗ trợ: taxi, giao hàng, thuê xe, mua hộ.

---

### GPS & Background Location

**Q: Driver app gửi vị trí real-time lên server như thế nào?**

> "Implement trong `track_location.dart` (~414 dòng). Dùng `Geolocator.getPositionStream()` để nhận GPS stream liên tục.
>
> Quan trọng là có **smart filtering** để tránh gửi quá nhiều request:
> - **Time gate**: bỏ qua update nếu chưa đủ N giây kể từ lần trước
> - **Distance gate**: bỏ qua nếu di chuyển chưa đến N mét
>
> Hai tham số này được server trả về qua `ResponseSetting` khi login — backend có thể điều chỉnh tần suất tracking mà không cần update app."

---

**Q: Nếu mạng mất khi driver đang chạy, location data có bị mất không?**

> "Không — có queue system dùng SharedPreferences làm buffer. Tối đa 100 location được lưu local khi API call thất bại. Khi có mạng trở lại, batch upload toàn bộ queue lên server.
>
> Điều này quan trọng cho việc giải quyết tranh chấp: nếu customer claim driver không đến, có log GPS đầy đủ để đối chiếu."

---

**Q: Background location tracking trên Android và iOS khác nhau thế nào?**

> "Android:
> - Cần xin `ignoreBatteryOptimizations` permission để tránh OS kill process
> - Dùng foreground service với notification thường trú — user thấy icon trên status bar khi driver đang online
> - `wakelock` package để giữ CPU không sleep
>
> iOS:
> - Khai báo `location` background mode trong Info.plist
> - Set `activityType: automotive` để iOS biết đây là navigation — ít bị throttle hơn
> - Không có foreground service concept như Android, thay vào đó iOS tự quản lý lifecycle
>
> Setting cho từng platform được server trả về qua `ResponseSetting` — không hardcode trong app."

---

### Order Flow

**Q: Flow nhận và xử lý đơn hàng của driver như thế nào?**

> "Driver nhận notification qua FCM khi có đơn mới. Tap vào → app load chi tiết đơn từ API.
>
> Điểm đặc biệt: các action available (confirm/cancel/begin/end) **không phải client quyết định** mà do backend trả về qua `DataButton` flags:
> ```
> OwnerCanConfirm, OwnerCanCancel, OwnerCanBegin, OwnerCanEnd, OwnerCanReview
> ```
> UI chỉ hiện button tương ứng với flag `true`. Lợi ích: business logic nằm ở server, không cần sync logic giữa 3 app (Ship/Driver/Merchant), tránh inconsistency."

---

**Q: Online/Offline toggle của driver implement thế nào?**

> "Gọi API `UpdateOwnerIsBusy` với payload `{IsBusy: true/false, Latitude, Longitude}`.
>
> Khi IsBusy = false → driver visible cho customer, hệ thống có thể dispatch đơn.
> Khi IsBusy = true → driver ẩn khỏi matching system.
>
> Background location tracking vẫn chạy dù driver offline — để chủ xe có thể track xe của họ. Đây là tính năng của app kiêm cả driver lẫn owner."

---

### Earnings & Wallet

**Q: Dashboard thu nhập implement thế nào?**

> "Screen `my_income_screen.dart` có 3 tab: Overview, Income, và breakdown theo loại dịch vụ.
>
> API `getReportIncomeData(fromDate, toDate, serviceCategoryId)` — filter theo thời gian và loại dịch vụ (taxi, giao hàng, thuê xe...).
>
> Driver có thể xem: thu nhập theo ngày/tuần/tháng, breakdown từng service, lịch sử transaction 2 tuần/1 tháng/2 tháng, và rút tiền về tài khoản ngân hàng."

---

### Maps & Navigation

**Q: Google Maps trong Driver app dùng gì đặc biệt hơn customer app?**

> "Driver app có Firebase Realtime Database listener trực tiếp trên map:
> ```dart
> FirebaseDatabase.instance
>   .ref('/Orders/{orderGUID}/Maps/{mapOptions}')
>   .listen(...)
> ```
> Map tự cập nhật markers (pickup, dropoff, driver position) và polyline route theo real-time. Không cần user pull-to-refresh.
>
> Ngoài ra dùng `map_launcher` để mở app navigation (Google Maps/Waze) khi driver cần turn-by-turn — không tự build navigation vì đã có app chuyên dụng làm tốt hơn."

---

### Architecture Differences

**Q: Driver app khác Ship app (customer) về mặt kỹ thuật như thế nào?**

> | Điểm | Driver App | Ship App (Customer) |
> |---|---|---|
> | GPS | Continuous stream + batch queue | Chỉ khi tìm kiếm/đặt xe |
> | Background | Foreground service, wakelock | Minimal |
> | Firebase | Realtime DB write + FCM | Realtime DB read + FCM |
> | Order flow | Receive→Confirm→Begin→End | Place→Pay→Track |
> | Payment | Withdrawal (nhận tiền) | Top-up/spending |
> | Settings | Server-driven tracking config | Static config |
>
> Driver app phức tạp hơn nhiều về background execution và battery management."

---

### Dynamic Popup Form

**Q: Driver app có popup form xuất hiện khi thực hiện action trên đơn hàng — bạn implement thế nào?**

> "Khi driver tap action button trên đơn, server có thể kèm theo `IsShowPopupForm: true` trong response. App kiểm tra flag này — nếu `true` thì mở `ZPBottomForm` (bottom sheet) thay vì execute action luôn.
>
> Form được render hoàn toàn từ `FormConfig` — một list field definitions do server trả về trong `Buttons.more['FormConfig']`. Mỗi field có:
> - `fieldName`, `type` (text/dropdown/image/...), `label`
> - `required`: bắt buộc hay không
> - `conditionShow`: điều kiện để field này xuất hiện (dựa theo giá trị field khác)
>
> Sau khi user điền form, app submit lên dynamic endpoint `/api/v1/{apiName}` cũng lấy từ config.
>
> Lợi ích: team backend có thể thêm/bớt field cho từng loại action (taxi/giao hàng/mua hộ) mà không cần update app — deploy logic form mới hoàn toàn từ server."

---

**Q: Conditional field trong form động implement thế nào?**

> "Mỗi field có property `conditionShow` — là một điều kiện JSON kiểu `{fieldName: 'reasonType', value: 'OTHER'}`.
>
> Trong `MyFormCubit`, khi user thay đổi giá trị một field → cubit emit state mới → `MyForm` widget rebuild → với mỗi field, evaluate `conditionShow` dựa trên current form values → field xuất hiện hoặc ẩn đi.
>
> Ví dụ: dropdown 'Lý do hủy' mặc định ẩn ô 'Ghi chú', chỉ hiện khi user chọn 'Lý do khác'. Toàn bộ logic này nằm trên server config, không hardcode trong app."

---

---

## Project: MASU MERCHANT

> Flutter app cho chủ cửa hàng. 648 Dart files, 29 Cubits. Quản lý menu, đơn hàng, doanh thu, lịch hoạt động.

---

### Product/Menu Management

**Q: Hệ thống quản lý menu trong Merchant app phức tạp như thế nào?**

> "Đây là phần phức tạp nhất trong toàn bộ hệ sinh thái Masu. Menu có **3 tầng**:
> - **Group** (danh mục): Món chính, Đồ uống, Topping...
> - **Product** (sản phẩm): từng item trong group
> - **Attribute** (biến thể): size S/M/L, ice level, topping chọn thêm...
>
> Ngoài ra còn có **Display Group** tách biệt với logical group — cho phép frontend customer app hiển thị theo layout riêng mà không phụ thuộc cấu trúc data backend.
>
> Tổng cộng có **12+ API endpoint** chỉ cho việc CRUD menu, bao gồm reorder (drag-and-drop), batch update attribute, toggle visibility."

---

**Q: Drag-and-drop reorder sản phẩm implement thế nào?**

> "Dùng `ReorderableListView` của Flutter. Sau khi user thả item vào vị trí mới, gọi API `ChangeOrderNo` với index mới. Server lưu `OrderNo` field cho từng product/group, trả về list đã sorted.
>
> Không update local trước (optimistic) mà đợi server confirm rồi mới refresh list — vì nếu fail thì rollback order sẽ phức tạp."

---

### Order Management

**Q: Khi merchant nhận đơn mới, flow xử lý như thế nào?**

> "1. FCM push về device → background handler check `obj_type == 'OrderMerchant'` → set flag `hasReloadOrderMerchant = true` trong SharedPreferences
> 2. Khi app được resume (foreground) → detect flag → gọi API reload order list
> 3. UI hiện countdown timer để merchant confirm trong thời gian quy định
>
> Lý do dùng flag thay vì reload ngay trong background handler: background handler chạy trong isolate riêng, không có BuildContext → không thể update UI trực tiếp. Flag là bridge giữa background và foreground."

---

**Q: Action buttons của merchant (confirm/cancel/ready) được quyết định thế nào?**

> "Giống Driver app — **backend-driven** qua `GetActionButton` response. Merchant app không có logic nào tự tính toán state, chỉ render button theo flag từ server.
>
> Lợi ích lớn nhất: khi business flow thay đổi (thêm trạng thái, bỏ bước), chỉ cần update server — 3 app (Ship/Driver/Merchant) đều phản ánh ngay mà không cần release app mới."

---

### Store Availability

**Q: Merchant bật/tắt nhận đơn implement thế nào?**

> "API `PUT /api/v1/Merchant/UpdateMerchantIsBusy` với busy reason code (đông khách, hết nguyên liệu, đóng cửa sớm...).
>
> Khác với Driver app toggle (binary on/off), Merchant có lý do kèm theo — hiển thị cho customer biết tại sao store không nhận đơn.
>
> Schedule cố định theo tuần dùng `MerchantWeekdaySchedule` — merchant set giờ mở/đóng cho từng ngày, backend tự tính toán có nhận đơn hay không mà không cần app gọi toggle mỗi ngày."

---

### Revenue & Analytics

**Q: Dashboard doanh thu build như thế nào?**

> "Dùng SliverAppBar với collapsible header — khi scroll xuống danh sách đơn hàng, header thu gọn lại để maximize không gian.
>
> Filter theo 3 time range preset (2 tuần, 1 tháng, 2 tháng) hoặc custom date range qua custom calendar widget. API `GetReportIncomeData` nhận `fromDate, toDate, serviceCategoryId` trả về breakdown theo loại dịch vụ.
>
> `operational_performance_screen.dart` show KPIs: tỷ lệ accept đơn, thời gian prepare trung bình, rating — những metric này merchant dùng để cải thiện performance."

---

### So sánh 3 app Masu

**Q: 3 app Masu (Ship/Driver/Merchant) share gì và tách gì?**

> "**Share:**
> - Cùng package name `masuship` (base infrastructure)
> - Cùng networking layer (NetworkManager, Retrofit pattern)
> - Cùng FCM setup, AppManager singleton
> - Cùng routing enum pattern (ZPRoute)
> - Cùng BLoC/Cubit + GetX DI architecture
>
> **Tách biệt:**
> - Toàn bộ UI modules riêng (Ship: browse/cart, Driver: map/GPS, Merchant: menu/order)
> - Business logic trong từng Cubit hoàn toàn khác nhau
> - API endpoints khác nhau (namespace theo role: `/Owner/`, `/OrderMerchant/`, `/api/v1/`)
> - Background behavior: Driver có GPS stream, Merchant không cần
>
> 3 app riêng biệt chứ không phải 1 app nhiều flavor — vì permission, UI và flow khác nhau quá nhiều."

---

## Project: SIGO (Cho thuê xe tự lái)

> Flutter (Mobile) + React JS (Web). 911 Dart files, 96 Cubits. Renter + Owner dual mode, KYC với MLKit, VietQR payment.

---

### KYC & Xác thực

**Q: KYC trong Sigo implement thế nào? Tại sao dùng MLKit thay vì upload lên server?**

> "KYC 3 bước:
> 1. Chụp mặt trước CMND/CCCD → Google MLKit Text Recognition đọc số CMND, tên, ngày sinh ngay trên thiết bị
> 2. Chụp mặt sau → OCR tiếp tục trích xuất
> 3. Selfie với liveness check → đảm bảo người dùng đang cầm điện thoại thật, không phải ảnh in
>
> Lý do dùng MLKit on-device thay vì upload raw image:
> - **Privacy**: ảnh CMND không rời thiết bị, chỉ gửi text data đã extract lên server
> - **Speed**: không cần round-trip network cho bước OCR
> - **Cost**: MLKit miễn phí, Vision API trả tiền theo lượt
>
> Ngoài ra có flow xác thực bằng lái xe riêng — chủ xe có thể yêu cầu renter cung cấp trước khi cho thuê."

---

**Q: Liveness check implement thế nào?**

> "Dùng `google_mlkit_object_detection` kết hợp camera stream. App detect khuôn mặt real-time và yêu cầu user thực hiện action (nhìn trái, nhìn phải, chớp mắt) để confirm đang dùng camera live, không phải ảnh tĩnh.
>
> Kết quả: confidence score từ ML model → nếu đủ ngưỡng mới cho phép submit. Server không xử lý logic này — toàn bộ trên thiết bị."

---

### Dual User Mode

**Q: Renter và Owner có 2 app riêng hay 1 app toggle?**

> "1 app, nhưng có **2 màn hình chính hoàn toàn tách biệt**: `MainScreen` cho Renter và `MainOwnerScreen` cho Owner. Toggle qua `AppManager.isModeRoleOwner`.
>
> Cấu trúc tab khác nhau hoàn toàn:
> - Renter: Tìm kiếm → Đặt xe → Chuyến đi → Tài khoản
> - Owner: Dashboard → Đội xe → Lịch bận → Doanh thu
>
> Lý do không làm 2 app riêng: nhiều user vừa là renter vừa là owner — dùng 1 app tiện hơn, không cần đăng nhập 2 lần."

---

### Booking & Pricing

**Q: Tính giá thuê xe dynamic như thế nào?**

> "Khi user thay đổi bất kỳ thông tin booking (ngày, giờ, địa chỉ giao xe, voucher), app gọi API `UpdateBookingInfo` → server trả về `RentalPriceDetail` với breakdown:
> ```
> Giá theo ngày × số ngày
> + Phí giao xe (nếu chọn owner delivery)
> + Bảo hiểm
> + VAT
> − Voucher discount
> = Tổng thanh toán
> ```
> Không tính giá phía client — server là source of truth để tránh sai lệch khi giá thay đổi."

---

**Q: Booking có 3 mode delivery thế nào?**

> "1. **Self-pickup**: User tự đến lấy xe tại địa điểm chủ xe — không tính phí giao
> 2. **Owner delivery**: Chủ xe tự giao đến địa chỉ user — tính phí giao theo km
> 3. **Third-party delivery**: Redirect sang app giao hàng bên thứ 3
>
> Mỗi mode có pricing khác nhau và flow khác nhau. Mode được set trong `ParamUpdateBookingCar` và ảnh hưởng trực tiếp đến `RentalPriceDetail` từ server."

---

### Calendar & Availability

**Q: Quản lý lịch xe available như thế nào?**

> "Owner set lịch bận (ngày xe không cho thuê) trong `BusyRentalSchedule`. Data được sync qua Firebase Realtime Database — khi owner update lịch trên 1 thiết bị, customer app thấy ngay không cần refresh.
>
> Khi customer search xe → filter theo ngày thuê → chỉ xe có `availableDate` trùng với request mới hiện. Blocking logic ở server, client chỉ display."

---

### Thanh toán

**Q: VietQR tích hợp thế nào?**

> "VietQR có Dio client riêng biệt (khác Dio của API chính) với base URL `https://api.vietqr.io/v2` và custom headers `x-client-id`, `x-api-key`.
>
> Flow:
> 1. User chọn thanh toán → app generate QR từ VietQR API
> 2. User scan QR bằng app ngân hàng → chuyển khoản
> 3. VietQR webhook notify server → server update order status → FCM push về app
>
> Wallet system: user có thể nạp tiền vào ví Sigo trước, sau đó dùng ví thanh toán trực tiếp không cần scan QR mỗi lần."

---

### Performance & Security

**Q: Device fingerprinting trong Sigo làm gì?**

> "Mỗi API request gửi kèm `DeviceNumber` (hash từ device properties qua `device_info_plus`) + `AppName` + `AppVersion` + `OS`.
>
> Server dùng để:
> - Detect bất thường: 1 account login từ quá nhiều thiết bị
> - Fraud prevention: tài khoản bị flag nếu pattern request bất thường
> - Debug: biết request đến từ iOS hay Android version nào khi có bug report
>
> Không phải chống được tất cả gian lận, nhưng thêm 1 layer khiến attacker khó hơn."

---

**Q: Custom image caching trong Sigo có gì đặc biệt?**

> "Sigo build `smart_cache_network_image` wrapper riêng thay vì dùng `cached_network_image` thuần. Wrapper này có `ImageCacheTracker` theo dõi:
> - Memory size của từng ảnh (width × height × bytes)
> - Error timestamp nếu load thất bại
> - `trackedImageMemorySizes` map để detect memory leak
>
> Lý do: app có nhiều ảnh xe chất lượng cao, không có tracking dễ OOM crash trên device ít RAM."

---

## Project: VFC Suite (1, 2, 3)

---

## Project: VFC 1 & 2

> React Native + Expo. Vai trò: **UI customization & maintenance**.
> VFC 1: field service (đơn hàng, hóa đơn, báo cáo). VFC 2: CRM (task, khách hàng).
> Cùng stack: Expo + @macashipo/mlib + Context API.

---

### Lưu ý khi trả lời phỏng vấn

> **Trả lời thật về scope:** "Tôi tham gia giai đoạn sau — chủ yếu custom UI components, thêm tính năng mới theo yêu cầu, và maintain codebase hiện có. Không phải người setup kiến trúc ban đầu."
>
> Điều này thể hiện **tính trung thực** — Senior interviewer đánh giá cao hơn là phóng đại.

---

### Tech Stack (React Native vs Flutter)

**Q: Bạn thấy React Native và Flutter khác nhau thế nào khi làm việc thực tế?**

> "Khác biệt rõ nhất tôi thấy khi maintain VFC:
>
> | Aspect | React Native (VFC) | Flutter (Masu/Sigo) |
> |---|---|---|
> | State | Context + useReducer | BLoC/Cubit |
> | Styling | StyleSheet.create() | ThemeData, widget tree |
> | Build | Expo EAS — đơn giản hơn | Flutter build tools |
> | Performance | JS bridge có overhead | Compiled to native |
> | Ecosystem | npm — nhiều package hơn | pub.dev — ít hơn nhưng chất lượng hơn |
>
> React Native với Expo thì setup và CI/CD nhanh hơn, nhưng khi cần custom native code thì Flutter dễ hơn (không cần biết JS bridge). Với app phức tạp như Masu Driver cần background GPS, Flutter tự nhiên hơn."

---

### Server-driven UI

**Q: Dynamic UI trong VFC hoạt động như thế nào?**

> "Backend trả về `configPage.UIType` string — app navigate đến `GenericScreen` với UIType đó. Component `MyPage` render layout tương ứng dựa trên UIType.
>
> Ví dụ: thêm màn hình báo cáo mới chỉ cần server trả về UIType mới, app không cần release version mới.
>
> Đây là pattern tương tự Server-Driven UI (SDUI) mà các công ty lớn như Airbnb, Grab dùng — linh hoạt nhưng cần discipline ở cả client lẫn server khi thay đổi schema."

---

### Custom Components

**Q: Bạn custom những gì cụ thể trong VFC?**

> "Tôi tập trung vào 3 phần:
>
> 1. **Form controls**: Thêm field type mới (currency input với format tự động, dropdown có pagination cho danh sách lớn). Hệ thống dùng `MyFormControl` wrapper với helper `HFormControl` cho get/set value.
>
> 2. **Card components**: Custom `card_invoice.js` hiển thị chi tiết hóa đơn với nhiều section — giá, thuế, trạng thái, QR code.
>
> 3. **State components**: `AStateLoading`, `AStateEmpty`, `AStateError` — chuẩn hóa UX cho các trạng thái loading/empty/error thay vì mỗi màn hình tự handle khác nhau.
>
> Không động vào networking layer hay business logic — scope chỉ là UI layer."

---

### Maintenance

**Q: Khi maintain codebase người khác build, bạn tiếp cận thế nào?**

> "Với VFC tôi làm theo trình tự:
> 1. Đọc hiểu luồng data: AppContext → useApp hook → reducer actions
> 2. Trace 1 feature end-to-end (ví dụ: login flow) để hiểu convention
> 3. Không refactor vội — chỉ sửa đúng chỗ cần sửa, tránh break cái đang chạy
> 4. Khi thêm component mới: follow pattern của component cũ trong cùng folder
>
> Nguyên tắc: khi maintain, **consistency > personal preference** — viết theo style của codebase dù không phải style mình chọn."

---

---

## Project: VFC 3 — PestMan

> React Native 0.79.5 + Expo 53. 319 files. **Built from scratch**. Offline-first, SQLite + gzip, config-driven forms, QR device tracking.

---

### Offline-first Architecture

**Q: Offline mode trong VFC 3 implement thế nào?**

> "App dùng `expo-sqlite` làm local database. Khi mất mạng, toàn bộ dữ liệu form nhân viên nhập (task data, device scan, ảnh chụp) được lưu vào SQLite với UUID làm key.
>
> Điểm đặc biệt: dataset lớn hơn 10MB được **nén bằng gzip** (thư viện pako) trước khi ghi vào SQLite dạng BLOB — giảm dung lượng đáng kể. Khi có mạng, background sync tự upload queue theo thứ tự.
>
> Database có migration handler — khi update app version mới, schema được upgrade tự động không mất data user."

---

**Q: Tại sao chọn SQLite thay vì chỉ dùng SharedPreferences/SecureStore?**

> "SharedPreferences phù hợp cho key-value đơn giản (token, settings). Nhưng VFC 3 cần:
> - Lưu nhiều form records cùng lúc (nhân viên có thể có 20+ task offline)
> - Query theo điều kiện (filter theo DeviceQRCode, DateScan)
> - Schema versioning khi app update
>
> SQLite cho phép làm tất cả những điều trên. Nếu dùng SharedPreferences, toàn bộ data là 1 JSON blob — parse chậm và không thể query."

---

### Config-driven Forms

**Q: MyFormControlV2 hoạt động như thế nào?**

> "Backend trả về mảng field configs. Mỗi config có `FieldName`, `Type`, `Label`, validation rules. Component `MyFormControlV2` map từng type sang control tương ứng:
>
> ```
> 'text'       → TextInput
> 'currency'   → Formatted number input
> 'date'       → Date picker
> 'select'     → Dropdown (có pagination)
> 'image'      → Camera capture
> 'signature'  → Canvas WebView
> 'checkbox'   → Toggle
> ...20+ types
> ```
>
> Khi PM yêu cầu thêm field mới (ví dụ: 'temperature' input), chỉ cần:
> 1. Thêm 1 component Type mới trong `MyFormControlV2/Types/`
> 2. Server thêm field vào config
> 3. Không cần sửa screen nào cả"

---

### Device Tracking & QR

**Q: QR device tracking flow hoàn chỉnh như thế nào?**

> "1. Nhân viên scan QR code trên thiết bị (máy phun, bẫy chuột...) bằng camera
> 2. App decode QR → extract `DeviceQRCode` + metadata
> 3. Form hiện ra với fields config từ server cho device đó
> 4. GPS snapshot tự động (expo-location với retry 5 lần nếu signal yếu)
> 5. Nhân viên nhập dữ liệu + chụp ảnh
> 6. Submit → nếu offline thì queue vào SQLite, nếu online thì upload ngay
> 7. Server log `DateScan`, `DateSubmit` cho audit trail
>
> Toàn bộ flow chạy được offline — quan trọng vì nhà máy thường có dead zone mạng."

---

### Authentication

**Q: Biometric auth implement thế nào?**

> "Dùng `expo-local-authentication` để check FaceID/fingerprint availability. Token được split làm 2:
> - **Main token**: lưu `expo-secure-store` (native keychain/keystore) — dùng sau khi login bằng password
> - **Biometric token**: lưu riêng — dùng cho biometric login lần sau
>
> Flow biometric:
> 1. App check `isBiometricEnrolled` → nếu có, offer biometric login
> 2. User xác thực bằng FaceID/fingerprint
> 3. App lấy biometric token từ secure store → gọi API verify → nhận fresh access token
>
> Không bao giờ lưu password — chỉ lưu token. Nếu token expire, user phải login lại bằng password."

---

### OTA Update

**Q: OTA update trong Expo hoạt động thế nào? Có rủi ro gì không?**

> "Expo EAS Update cho phép push JavaScript bundle mới mà không cần submit qua App Store/Play Store — user nhận update ngay khi mở app.
>
> Cách implement: app check update khi start, nếu có version mới thì download background, apply khi restart.
>
> Rủi ro:
> - **Native code thay đổi** (thêm native module, config mới): KHÔNG dùng được OTA, phải submit store bình thường
> - **Bad update**: nếu JS crash ngay lúc start → Expo tự rollback về bundle trước
>
> VFC 3 dùng OTA cho bug fix nhỏ và content update — tránh dùng cho thay đổi architecture lớn. Có 4 channels (preview, adhoc, production, production_phase_two) để test từng bước trước khi push production."

---

### So sánh VFC 1/2 vs VFC 3

**Q: Bạn học được gì từ VFC 1/2 và apply vào VFC 3?**

> "Sau khi maintain VFC 1 và 2, tôi nhận ra một số pain point:
>
> 1. **Form hardcode**: mỗi màn hình VFC 1/2 tự build form riêng → duplicate code nhiều. VFC 3 tôi design `MyFormControlV2` centraliz toàn bộ — thêm field mới chỉ cần thêm 1 file.
>
> 2. **Không có offline support**: VFC 1/2 mất mạng là không dùng được. VFC 3 tôi design offline-first từ đầu với SQLite queue.
>
> 3. **Error handling rải rác**: VFC 1/2 mỗi component tự catch error theo cách riêng. VFC 3 dùng `ErrorBoundary` global + Crashlytics để có đủ context khi debug production issue.
>
> Về React Native vs Flutter: sau khi làm cả 2 stack, tôi thấy React Native với Expo phù hợp hơn cho team có background web (JavaScript/TypeScript). Flutter phù hợp hơn khi cần performance cao và background service phức tạp như GPS tracking liên tục trong Masu Driver."

---

## Project: COSHARE (Bán hàng nội bộ)

> React JS + Firebase + RESTful API. Web app dành cho nhân viên nhà máy.

*(Đang cập nhật — cần phân tích source code)*

---

**Câu hỏi dự kiến:**
- State management trong React JS? (Redux, Context, Zustand?)
- Firebase dùng cho phần nào? (Auth, Firestore, Realtime?)
- Authentication flow cho nhân viên nội bộ?

---

---

## Project: HV Quản Lý Tài Sản (Side Project · AI-assisted)

> Full-stack web app quản lý tài sản doanh nghiệp cho chuỗi nhà thuốc ~40 chi nhánh.
> Stack: React 18 + Node.js/Express + PostgreSQL + Socket.IO. Monorepo Turborepo.
> **Vai trò:** Thiết kế kiến trúc, viết spec, điều phối AI (Claude) để implement.

---

### AI-assisted Development

**Q: Project này bạn dùng AI để làm gì? Vai trò của bạn là gì?**

> "Tôi dùng Claude để accelerate implementation — nhưng tôi là người ra quyết định kỹ thuật.
>
> Cụ thể những gì tôi làm:
> - **Thiết kế kiến trúc**: chọn monorepo Turborepo, quyết định tách shared package, design Prisma schema cho 2 database (main + audit log)
> - **Viết spec chi tiết**: 12 module specs trong `docs/specs/` trước khi implement — mỗi spec định nghĩa data model, API endpoints, business rules, edge cases
> - **Review code**: mỗi output từ AI đều được review, hiểu, và debug khi cần
> - **Governance**: viết `CLAUDE.md` với naming conventions, module boundaries, code patterns cho cả project
>
> AI làm tốt phần boilerplate và pattern repetition — tôi tập trung vào phần đòi hỏi judgment: kiến trúc, trade-off, business logic phức tạp."

---

**Q: Bạn có thực sự hiểu code do AI viết không?**

> "Đây là câu hỏi quan trọng và tôi muốn trả lời thẳng: có, vì đây là điều kiện tôi đặt ra từ đầu.
>
> Những phần tôi có thể giải thích chi tiết:
> - Tại sao dùng 2 Prisma schema (main DB + log DB riêng biệt)
> - Socket.IO flow: JWT middleware → room per user → event-driven cache invalidation
> - Approval workflow state machine: draft → pending → approved/rejected
> - SLA violation detection trong TaskService
>
> Những phần tôi sẽ nói thật nếu không nhớ chi tiết implementation: 'Tôi biết nó làm gì và tại sao, nhưng cần xem lại code để trả lời câu hỏi cụ thể về implementation.'
>
> Điều này áp dụng cho mọi developer — kể cả code mình tự viết 6 tháng trước."

---

### Kiến trúc Monorepo

**Q: Tại sao chọn monorepo cho project này?**

> "3 lý do chính:
>
> 1. **Shared types**: Frontend và backend dùng chung TypeScript types/enums từ `@hvassets/shared` package — không bao giờ bị lệch interface giữa API response và frontend model
> 2. **Atomic changes**: Khi thêm field mới vào Prisma schema, cập nhật shared type, update API endpoint, và update UI component trong 1 commit — không có PR chờ nhau giữa 2 repo
> 3. **CI/CD đơn giản**: Turborepo detect thay đổi theo dependency graph — chỉ build lại package bị ảnh hưởng, không build toàn bộ
>
> Trade-off: setup phức tạp hơn single repo ban đầu, nhưng payoff rõ khi project scale."

---

### Real-time

**Q: Socket.IO dùng như thế nào trong project? Tại sao không dùng polling?**

> "Socket.IO cho real-time notifications và activity feed — khi tài sản thay đổi trạng thái hoặc có incident mới, tất cả user đang online thấy ngay không cần refresh.
>
> Architecture:
> - Backend: Socket.IO server có JWT middleware riêng — kết nối phải xác thực token trước khi nhận event
> - Activity subscribers: mỗi service (AssetService, IncidentService...) có subscriber emit event khi data thay đổi
> - Frontend: hook `useSocketNotifications` lắng nghe event → gọi `queryClient.invalidateQueries()` → TanStack Query tự re-fetch data mới
>
> Tại sao không polling? Với 40 chi nhánh và nhiều user concurrent, polling 30 giây = N users × requests/30s liên tục. Socket.IO chỉ tốn bandwidth khi thực sự có event."

---

### RBAC & Permission

**Q: Role-based access control implement thế nào? Có 6 role phức tạp không?**

> "Backend dùng middleware `require-role.middleware.ts` — route nào cần permission thì khai báo roles array:
> ```
> router.post('/assets', requireRole(['admin', 'ops_manager']), createAsset)
> ```
>
> Frontend có 2 tầng:
> - **Route guard**: check role trước khi render page
> - **Menu visibility**: Zustand store lưu `roleMenus` — menu items chỉ hiện với role có quyền
>
> Approval chains có thể config per-pharmacy — ví dụ pharmacy A cần manager duyệt chi phí >5tr, pharmacy B cần finance duyệt. Config này lưu trong DB, không hardcode.
>
> 6 role có vẻ nhiều nhưng về mặt implementation chỉ cần 1 middleware — không phức tạp hơn 2 role về code, chỉ phức tạp hơn về business logic mapping."

---

### SLA & Approval Workflow

**Q: SLA engine trong hệ thống này hoạt động như thế nào?**

> "Mỗi loại tài sản có `SlaConfig` gắn theo: `responseHours` (giờ phải phản hồi) và `completionHours` (giờ phải xong).
>
> Khi incident được tạo → timestamp lưu vào DB → TaskService khi query check:
> ```
> isOverdue = now > createdAt + completionHours
> isDueSoon = now > createdAt + completionHours * 0.8  // 80% SLA đã qua
> ```
>
> Frontend hiện badge màu: xanh (on-track), vàng (due-soon), đỏ (overdue).
>
> Không cần cron job để update badge — tính toán realtime mỗi lần query. Cron job chỉ dùng để gửi email reminder khi SLA gần hết."

---

### So sánh với Mobile Projects

**Q: Làm full-stack web sau khi làm mobile, bạn thấy khác gì?**

> "Khác biệt lớn nhất là mental model về state:
>
> - **Mobile (Flutter/React Native)**: UI state và server state thường tách biệt rõ — BLoC/Cubit là UI state, API call là separate concern
> - **Web với TanStack Query**: server state là first-class citizen — `useQuery` vừa fetch vừa cache vừa sync với UI, không cần tự manage loading/error state từng chỗ
>
> Điểm giống nhau: cả hai đều dùng Repository pattern, đều cần care về authentication, error handling, optimistic updates.
>
> Điểm tôi mang từ mobile sang web: tư duy về offline (web thường bỏ qua), performance profiling, và habit test edge case (mạng chậm, session expire giữa chừng)."

---

## Câu hỏi chung cho mọi project

**Q: Project nào bạn tự hào nhất và tại sao?**

> Gợi ý trả lời dựa trên Masu:
> "Masu là project tôi tự hào nhất vì độ phức tạp kỹ thuật cao — phải maintain 3 app cùng lúc (Ship/Driver/Merchant) với shared business logic nhưng UI và flow khác nhau hoàn toàn. Bài toán real-time tracking và đồng bộ state giữa 3 app là thử thách lớn nhất, giải quyết bằng Firebase Realtime Database làm source of truth duy nhất."

---

**Q: Khó khăn lớn nhất bạn gặp và giải quyết thế nào?**

> Gợi ý dựa trên Masu:
> "Deep link khi app bị kill là trường hợp khó nhất — phải handle khác hoàn toàn so với khi app đang chạy. Mất 2 ngày debug vì iOS và Android có behavior khác nhau với `getInitialAppLink`. Cuối cùng giải quyết bằng cách wrap cả 2 case trong `RouteUtils` và test kỹ trên cả 2 platform."

---

**Q: Nếu làm lại từ đầu, bạn sẽ thay đổi gì?**

> Gợi ý:
> "Tách DI ra khỏi GetX — dùng `get_it` + `injectable` thay vì GetX service locator. Lý do: khi routing thay đổi (ví dụ migrate sang go_router), DI không bị ảnh hưởng. Hiện tại coupling GetX cho cả DI + routing + state khiến khó migrate từng phần độc lập."

# React Native Interview Questions — Middle Level

---

## PHẦN 1: JAVASCRIPT / TYPESCRIPT FUNDAMENTALS

### 1.1. Event Loop & Async

**Q: Giải thích Event Loop trong JavaScript.**

```
Call Stack          Web APIs / Timer        Callback Queue / Microtask Queue
──────────          ────────────────        ────────────────────────────────
main()              setTimeout(cb, 0)  →    Macrotask Queue: [cb]
fetchData()         fetch(url)         →    Microtask Queue: [.then()]
                                            (Microtask ưu tiên hơn Macrotask)
```

```javascript
console.log('1');

setTimeout(() => console.log('2'), 0); // Macrotask

Promise.resolve().then(() => console.log('3')); // Microtask

console.log('4');

// Output: 1 → 4 → 3 → 2
// Microtask (Promise) luôn chạy TRƯỚC macrotask (setTimeout)
```

**Thứ tự ưu tiên:**
1. Call Stack (synchronous)
2. Microtask Queue (Promise.then, queueMicrotask, MutationObserver)
3. Macrotask Queue (setTimeout, setInterval, I/O)

---

### 1.2. Closure

**Q: Closure là gì? Cho ví dụ thực tế trong React Native.**

```javascript
// Closure = function "nhớ" scope của nơi nó được tạo ra
function makeCounter() {
  let count = 0; // biến trong outer scope

  return function() {
    count++; // vẫn truy cập được count dù makeCounter() đã return
    return count;
  };
}

const counter = makeCounter();
counter(); // 1
counter(); // 2

// Ví dụ thực tế: stale closure trong React hooks
function Timer() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      // BUG: count luôn là 0 vì closure "bắt" giá trị count ban đầu
      console.log(count); // luôn = 0
      setCount(count + 1); // luôn set = 1!
    }, 1000);
    return () => clearInterval(interval);
  }, []); // [] → closure cũ, không update

  // FIX: dùng functional update
  useEffect(() => {
    const interval = setInterval(() => {
      setCount(prev => prev + 1); // ĐÚNG — không cần đọc count
    }, 1000);
    return () => clearInterval(interval);
  }, []);
}
```

---

### 1.3. Prototype & this

```javascript
// this trong arrow function vs regular function
class Timer {
  seconds = 0;

  // Regular function — this thay đổi theo context
  startRegular() {
    setInterval(function() {
      this.seconds++; // LỖI: this = undefined (strict mode) hoặc global
    }, 1000);
  }

  // Arrow function — this kế thừa từ outer scope
  startArrow() {
    setInterval(() => {
      this.seconds++; // ĐÚNG: this = Timer instance
    }, 1000);
  }
}
```

---

### 1.4. TypeScript — Những gì hay bị hỏi

```typescript
// Generics thực tế
interface ApiResponse<T> {
  data: T;
  status: number;
  message: string;
}

async function fetchData<T>(url: string): Promise<ApiResponse<T>> {
  const response = await fetch(url);
  return response.json();
}

const user = await fetchData<User>('/user/1'); // user.data là type User

// Union & Intersection Types
type LoadingState = 'idle' | 'loading' | 'success' | 'error';

type Admin = User & { permissions: string[] }; // intersection

// Discriminated Union — rất hay dùng với state
type AuthState =
  | { status: 'unauthenticated' }
  | { status: 'authenticated'; user: User }
  | { status: 'loading' };

function handleState(state: AuthState) {
  switch (state.status) {
    case 'authenticated':
      return state.user.name; // TypeScript biết state.user tồn tại
    case 'loading':
      return 'Loading...';
  }
}

// Utility Types quan trọng
type PartialUser = Partial<User>;           // tất cả field optional
type RequiredUser = Required<User>;         // tất cả field required
type ReadonlyUser = Readonly<User>;         // không thể mutate
type UserName = Pick<User, 'id' | 'name'>; // chỉ lấy 1 số field
type WithoutEmail = Omit<User, 'email'>;    // bỏ 1 số field
type UserRecord = Record<string, User>;     // { [key: string]: User }
```

---

## PHẦN 2: REACT NATIVE CORE

### 2.1. Architecture — Old vs New

**Q: Giải thích kiến trúc RN cũ và mới (JSI/Fabric).**

#### Old Architecture (Bridge)

```
JavaScript Thread        Bridge (JSON serialization)     Native Thread
──────────────           ──────────────────────          ─────────────
JS Code          ──→    Serialize → Queue → Deserialize → Native Modules
                 ←──    Serialize → Queue → Deserialize ← Native Events

Vấn đề:
- Async: không giao tiếp được synchronous
- Serialization: tốn CPU khi data lớn
- Bridge là bottleneck
```

#### New Architecture (JSI + Fabric + TurboModules)

```
JavaScript Thread        JSI (JavaScript Interface)      Native Thread
──────────────           ─────────────────────           ─────────────
JS Code          ──→    Direct C++ reference             Native Modules (TurboModules)
                         Synchronous hoặc Async
                         Không cần serialize JSON

- JSI: JS có thể giữ reference C++ object trực tiếp
- Fabric: renderer mới, hỗ trợ concurrent features
- TurboModules: lazy load native modules
- Codegen: tự generate type-safe bridge code
```

---

### 2.2. Thread Model

**Q: React Native có bao nhiêu threads?**

| Thread | Nhiệm vụ |
|---|---|
| **JS Thread** | Chạy JS code, business logic, React reconciliation |
| **UI Thread (Main)** | Render native views, handle gestures |
| **Shadow Thread** | Tính toán layout (Yoga engine) |
| **Background Threads** | Network, file I/O, image processing |

```javascript
// Tại sao UI bị janky?
// → JS Thread bận quá (heavy computation, animation)
// → Giải pháp:
// 1. Move animation về UI thread (useNativeDriver: true)
// 2. Move heavy work về InteractionManager
// 3. Dùng Reanimated 2 (chạy trên UI thread)

InteractionManager.runAfterInteractions(() => {
  // Chạy sau khi animation/transition hoàn thành
  loadHeavyData();
});
```

---

### 2.3. Core Components

**Q: Kể tên và phân biệt các Core Components quan trọng.**

```javascript
// View — container cơ bản (như div)
<View style={styles.container} />

// Text — hiển thị text (KHÔNG thể đặt text thẳng vào View)
<Text numberOfLines={2} ellipsizeMode="tail">Long text...</Text>

// Image
<Image
  source={{ uri: 'https://...' }}
  resizeMode="cover"  // cover | contain | stretch | repeat | center
/>

// ScrollView vs FlatList vs SectionList
// ScrollView: render TẤT CẢ children → dùng khi ít items
// FlatList: lazy render → dùng khi list dài
// SectionList: FlatList nhưng có section header

// TextInput
<TextInput
  value={text}
  onChangeText={setText}
  keyboardType="email-address"
  returnKeyType="next"
  autoCapitalize="none"
  secureTextEntry={isPassword}
  onSubmitEditing={() => passwordRef.current?.focus()}
/>

// Pressable (thay thế TouchableOpacity, TouchableHighlight)
<Pressable
  onPress={handlePress}
  style={({ pressed }) => [
    styles.button,
    pressed && styles.buttonPressed
  ]}
>
  <Text>Click me</Text>
</Pressable>
```

---

### 2.4. StyleSheet

**Q: Tại sao dùng `StyleSheet.create()` thay vì inline styles?**

```javascript
// Inline style — tạo object mới mỗi lần render
<View style={{ flex: 1, backgroundColor: 'white' }} />

// StyleSheet.create — validate và optimize styles
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'white',
  },
});
<View style={styles.container} />

// Lợi ích StyleSheet.create:
// 1. Validate style props ở dev mode
// 2. Styles được register và send qua bridge 1 lần (ID thay vì object)
// 3. Không tạo object mới mỗi render → tiết kiệm memory

// Combine styles
<View style={[styles.base, isActive && styles.active, { marginTop: 10 }]} />
```

---

### 2.5. Flexbox trong React Native

**Q: Flexbox RN khác web như thế nào?**

| | React Native | Web (CSS) |
|---|---|---|
| `flexDirection` | `column` (mặc định) | `row` (mặc định) |
| `flex` | Chỉ nhận 1 số | `flex-grow flex-shrink flex-basis` |
| `position` | `relative` hoặc `absolute` | Thêm `fixed`, `sticky` |
| Unit | Không có px, rem | px, rem, %, vh... |
| Đơn vị số | Density-independent pixels (dp) | px |

```javascript
// RN không có %width... à có nhưng dùng khác
const { width } = Dimensions.get('window');

// Hoặc dùng flex
<View style={{ flex: 1 }}>           {/* fill available space */}
  <View style={{ flex: 2 }} />       {/* 2/3 height */}
  <View style={{ flex: 1 }} />       {/* 1/3 height */}
</View>

// useWindowDimensions — reactive (cập nhật khi xoay màn hình)
const { width, height } = useWindowDimensions();
```

---

## PHẦN 3: HOOKS (QUAN TRỌNG)

### 3.1. useState & useReducer

```javascript
// useState — simple state
const [count, setCount] = useState(0);

// useState với lazy initialization — tốn CPU khi compute initial value
const [data, setData] = useState(() => expensiveComputation());

// useReducer — khi state phức tạp, nhiều sub-values liên quan
const initialState = { count: 0, loading: false, error: null };

function reducer(state, action) {
  switch (action.type) {
    case 'increment':
      return { ...state, count: state.count + 1 };
    case 'setLoading':
      return { ...state, loading: action.payload };
    case 'setError':
      return { ...state, error: action.payload, loading: false };
    default:
      return state;
  }
}

const [state, dispatch] = useReducer(reducer, initialState);
dispatch({ type: 'increment' });
dispatch({ type: 'setLoading', payload: true });
```

**useState vs useReducer:**
| | useState | useReducer |
|---|---|---|
| Khi nào | State đơn giản | State phức tạp, có liên quan nhau |
| Testing | Khó test logic | Dễ test reducer (pure function) |
| Predictability | Thấp | Cao |

---

### 3.2. useEffect

```javascript
// Dependency array
useEffect(() => { ... });           // Mỗi render
useEffect(() => { ... }, []);       // Mount + Unmount
useEffect(() => { ... }, [userId]); // Khi userId thay đổi

// Cleanup function
useEffect(() => {
  const subscription = subscribe(userId);
  return () => subscription.unsubscribe(); // cleanup
}, [userId]);

// Common mistakes
// 1. Missing dependency
useEffect(() => {
  fetchUser(userId); // userId là dependency nhưng không khai báo!
}, []);  // ← BUG: stale closure

// ĐÚNG
useEffect(() => {
  fetchUser(userId);
}, [userId]);

// 2. Object/Array dependency — infinite loop!
useEffect(() => {
  doSomething(config);
}, [config]); // config = {} → mỗi render tạo object mới → infinite loop!

// FIX: useMemo hoặc destructure
const { url, timeout } = config;
useEffect(() => {
  doSomething({ url, timeout });
}, [url, timeout]);
```

---

### 3.3. useCallback & useMemo

**Q: Khi nào dùng useCallback và useMemo? Có phải lúc nào cũng dùng không?**

```javascript
// useMemo — cache kết quả tính toán
const sortedList = useMemo(
  () => [...items].sort((a, b) => a.name.localeCompare(b.name)),
  [items] // chỉ sort lại khi items thay đổi
);

// useCallback — cache function reference
const handlePress = useCallback((id) => {
  dispatch({ type: 'SELECT', payload: id });
}, [dispatch]); // stable reference nếu dispatch không đổi

// Tại sao quan trọng cho RN?
// React.memo — skip re-render nếu props không đổi
const ListItem = React.memo(({ item, onPress }) => {
  return <Pressable onPress={() => onPress(item.id)}><Text>{item.name}</Text></Pressable>;
});

// Nếu onPress là function thông thường → mỗi render tạo mới → ListItem vẫn re-render!
// Nếu onPress là useCallback → reference stable → ListItem không re-render nếu data không đổi

// ĐỪNG lạm dụng useCallback/useMemo — chỉ dùng khi:
// 1. Component con bọc React.memo
// 2. Function/value là dependency của useEffect
// 3. Tính toán thực sự nặng (sort, filter list lớn)
```

---

### 3.4. useRef

```javascript
// 2 mục đích chính:

// 1. Truy cập DOM/Native element
const inputRef = useRef(null);
const focusInput = () => inputRef.current?.focus();
<TextInput ref={inputRef} />

// 2. Lưu mutable value mà KHÔNG trigger re-render
const intervalRef = useRef(null);
const countRef = useRef(0);

useEffect(() => {
  intervalRef.current = setInterval(() => {
    countRef.current += 1; // update nhưng không re-render
  }, 1000);
  return () => clearInterval(intervalRef.current);
}, []);

// useRef vs useState:
// useRef — thay đổi không trigger re-render
// useState — thay đổi TRIGGER re-render
```

---

### 3.5. Custom Hooks

**Q: Tạo custom hook ví dụ thực tế.**

```javascript
// useFetch — fetch data với loading/error state
function useFetch(url) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true; // tránh setState khi component unmount

    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await fetch(url);
        const json = await response.json();
        if (isMounted) setData(json);
      } catch (err) {
        if (isMounted) setError(err.message);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchData();
    return () => { isMounted = false; };
  }, [url]);

  return { data, loading, error };
}

// useDebounce — delay search input
function useDebounce(value, delay = 500) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

// Sử dụng
function SearchScreen() {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 500);
  const { data, loading } = useFetch(`/search?q=${debouncedQuery}`);
}

// useAppState — lắng nghe app foreground/background
function useAppState() {
  const [appState, setAppState] = useState(AppState.currentState);

  useEffect(() => {
    const subscription = AppState.addEventListener('change', setAppState);
    return () => subscription.remove();
  }, []);

  return appState;
}

// useNetworkStatus
function useNetworkStatus() {
  const [isConnected, setIsConnected] = useState(true);

  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener(state => {
      setIsConnected(state.isConnected ?? true);
    });
    return unsubscribe;
  }, []);

  return isConnected;
}
```

---

## PHẦN 4: STATE MANAGEMENT

### 4.1. Redux Toolkit (RTK)

**Q: Giải thích Redux flow và RTK.**

```javascript
// Classic Redux flow:
// Action → Reducer → Store → Component

// Redux Toolkit — viết ít boilerplate hơn
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

// createAsyncThunk — handle async actions
export const fetchUser = createAsyncThunk(
  'user/fetchUser',
  async (userId, { rejectWithValue }) => {
    try {
      const response = await api.getUser(userId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

// createSlice — tự tạo actions, reducers
const userSlice = createSlice({
  name: 'user',
  initialState: {
    data: null,
    loading: false,
    error: null,
  },
  reducers: {
    // Synchronous actions
    logout: (state) => {
      state.data = null; // Immer cho phép "mutate" trực tiếp
    },
    updateName: (state, action) => {
      if (state.data) state.data.name = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchUser.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(fetchUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { logout, updateName } = userSlice.actions;

// RTK Query — data fetching tích hợp sẵn
const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({ baseUrl: '/api' }),
  endpoints: (builder) => ({
    getUser: builder.query({
      query: (id) => `/users/${id}`,
      providesTags: ['User'],
    }),
    updateUser: builder.mutation({
      query: (user) => ({ url: `/users/${user.id}`, method: 'PUT', body: user }),
      invalidatesTags: ['User'], // tự refetch getUser
    }),
  }),
});

export const { useGetUserQuery, useUpdateUserMutation } = apiSlice;

// Sử dụng
function UserProfile({ userId }) {
  const { data: user, isLoading, error } = useGetUserQuery(userId);
  const [updateUser] = useUpdateUserMutation();

  if (isLoading) return <ActivityIndicator />;
  if (error) return <Text>Error!</Text>;
  return <Text>{user.name}</Text>;
}
```

---

### 4.2. Zustand (nhẹ hơn Redux)

```javascript
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isLoggedIn: false,

      login: async (credentials) => {
        const { user, token } = await authApi.login(credentials);
        set({ user, token, isLoggedIn: true });
      },

      logout: () => set({ user: null, token: null, isLoggedIn: false }),

      updateUser: (updates) => set((state) => ({
        user: { ...state.user, ...updates }
      })),
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => AsyncStorage),
    }
  )
);

// Sử dụng
function LoginButton() {
  const { login, isLoggedIn } = useAuthStore();
  // Chỉ render lại khi login hoặc isLoggedIn thay đổi
  // Nếu user thay đổi → KHÔNG re-render (không subscribe user)
}
```

---

### 4.3. Context API — Khi nào dùng?

```javascript
// Context phù hợp cho:
// - Theme, Language, Auth (ít thay đổi)
// KHÔNG phù hợp cho: data thay đổi thường xuyên (gây re-render toàn bộ)

const ThemeContext = createContext('light');

// Tách context ra nhiều phần để tránh re-render thừa
const UserStateContext = createContext(null);
const UserDispatchContext = createContext(null);

function UserProvider({ children }) {
  const [user, dispatch] = useReducer(userReducer, null);

  return (
    <UserStateContext.Provider value={user}>
      <UserDispatchContext.Provider value={dispatch}>
        {children}
      </UserDispatchContext.Provider>
    </UserStateContext.Provider>
  );
}

// Component chỉ cần dispatch không bị re-render khi user thay đổi
function ActionButton() {
  const dispatch = useContext(UserDispatchContext);
  return <Button onPress={() => dispatch({ type: 'LOGOUT' })} />;
}
```

---

## PHẦN 5: NAVIGATION

### 5.1. React Navigation (v6+)

**Q: Các loại navigator và khi nào dùng?**

```javascript
// Stack Navigator — có animation push/pop
const Stack = createNativeStackNavigator();

// Bottom Tab Navigator
const Tab = createBottomTabNavigator();

// Drawer Navigator
const Drawer = createDrawerNavigator();

// Cấu trúc thực tế (nested navigators)
function AppNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator>
        {/* Auth screens */}
        <Stack.Screen name="Login" component={LoginScreen} />
        <Stack.Screen name="Register" component={RegisterScreen} />

        {/* Main app với Bottom Tabs */}
        <Stack.Screen
          name="Main"
          component={MainTabNavigator}
          options={{ headerShown: false }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

function MainTabNavigator() {
  return (
    <Tab.Navigator>
      <Tab.Screen name="Home" component={HomeStack} />
      <Tab.Screen name="Profile" component={ProfileStack} />
    </Tab.Navigator>
  );
}
```

---

### 5.2. Navigation Patterns

```javascript
// Truyền params
navigation.navigate('Detail', { itemId: 123 });

// Nhận params
const { itemId } = route.params;

// TypeScript — type-safe navigation
type RootStackParamList = {
  Home: undefined;
  Detail: { itemId: number };
  Profile: { userId: string; tab?: 'posts' | 'likes' };
};

// Navigate với replace (không có back button)
navigation.replace('Home');

// Reset stack
navigation.reset({
  index: 0,
  routes: [{ name: 'Home' }],
});

// Go back
navigation.goBack();
navigation.popToTop(); // về màn hình đầu tiên của stack

// Deep linking
const linking = {
  prefixes: ['myapp://', 'https://myapp.com'],
  config: {
    screens: {
      Home: 'home',
      Detail: 'product/:itemId',
      Profile: {
        path: 'user/:userId',
        parse: { userId: (id) => `user-${id}` },
      },
    },
  },
};
```

---

### 5.3. Navigation Events & Focus

```javascript
// Lắng nghe khi màn hình được focus
useEffect(() => {
  const unsubscribe = navigation.addListener('focus', () => {
    // Screen được focus → refetch data, start animation...
    fetchData();
  });
  return unsubscribe;
}, [navigation]);

// useFocusEffect — chạy mỗi khi screen focus
useFocusEffect(
  useCallback(() => {
    const subscription = startLocationTracking();
    return () => subscription.stop(); // cleanup khi blur
  }, [])
);

// useIsFocused — biết screen có đang focus không
const isFocused = useIsFocused();
```

---

## PHẦN 6: ANIMATION

### 6.1. Animated API

```javascript
// Basic animation
const fadeAnim = useRef(new Animated.Value(0)).current;

const fadeIn = () => {
  Animated.timing(fadeAnim, {
    toValue: 1,
    duration: 500,
    easing: Easing.ease,
    useNativeDriver: true, // chạy trên UI thread, không qua bridge
  }).start();
};

// useNativeDriver: true — chỉ hỗ trợ:
// transform (translateX, translateY, scale, rotate)
// opacity
// KHÔNG hỗ trợ: width, height, backgroundColor, flex...

// Sequence và Parallel
Animated.sequence([
  Animated.timing(opacity, { toValue: 1, duration: 300, useNativeDriver: true }),
  Animated.delay(1000),
  Animated.timing(opacity, { toValue: 0, duration: 300, useNativeDriver: true }),
]).start();

Animated.parallel([
  Animated.timing(translateX, { toValue: 100, useNativeDriver: true }),
  Animated.timing(opacity, { toValue: 0, useNativeDriver: true }),
]).start();

// Spring animation
Animated.spring(scale, {
  toValue: 1,
  friction: 7,
  tension: 40,
  useNativeDriver: true,
}).start();
```

---

### 6.2. Reanimated 2 (khuyên dùng)

**Q: Tại sao Reanimated 2 tốt hơn Animated API?**

```javascript
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withTiming,
  runOnJS,
} from 'react-native-reanimated';

// Shared Value — chạy trên UI thread
const offset = useSharedValue(0);

// Animated Style — tính toán trên UI thread
const animatedStyles = useAnimatedStyle(() => ({
  transform: [{ translateX: offset.value }],
}));

// Trigger animation
offset.value = withSpring(100); // không cần .start()
offset.value = withTiming(0, { duration: 500 });

// Tại sao tốt hơn:
// Animated API → animation logic chạy trên JS thread
//   → mỗi frame phải communicate qua bridge → có thể janky
// Reanimated 2 → animation logic chạy TRÊN UI THREAD
//   → không qua bridge → smooth 60fps ngay cả khi JS thread bận

// Gesture Handler + Reanimated — perfect combo
const { GestureDetector, Gesture } = require('react-native-gesture-handler');

const panGesture = Gesture.Pan()
  .onUpdate((event) => {
    offset.value = event.translationX;
  })
  .onEnd(() => {
    offset.value = withSpring(0);
  });

return (
  <GestureDetector gesture={panGesture}>
    <Animated.View style={[styles.box, animatedStyles]} />
  </GestureDetector>
);
```

---

## PHẦN 7: PERFORMANCE

### 7.1. FlatList Optimization

**Q: Cách optimize FlatList khi render list lớn?**

```javascript
<FlatList
  data={items}
  keyExtractor={(item) => item.id.toString()}
  renderItem={({ item }) => <ItemComponent item={item} />}

  // Performance props
  initialNumToRender={10}          // số items render ban đầu
  maxToRenderPerBatch={10}         // số items render mỗi batch
  windowSize={5}                   // số màn hình xung quanh giữ trong memory
  updateCellsBatchingPeriod={50}   // ms giữa các batch
  removeClippedSubviews={true}     // unmount items ngoài viewport (Android)

  // Tránh re-render không cần thiết
  getItemLayout={(data, index) => ({
    length: ITEM_HEIGHT,
    offset: ITEM_HEIGHT * index,
    index,
  })} // nếu item có fixed height → skip measurement, scroll nhanh hơn
/>

// Memoize renderItem — quan trọng!
const renderItem = useCallback(({ item }) => (
  <ItemComponent item={item} onPress={handlePress} />
), [handlePress]); // handlePress cần useCallback

// Hoặc memo component
const ItemComponent = React.memo(({ item, onPress }) => {
  // chỉ re-render khi item hoặc onPress thay đổi
});
```

---

### 7.2. Image Optimization

```javascript
// fast-image — thay thế built-in Image
import FastImage from 'react-native-fast-image';

<FastImage
  style={{ width: 100, height: 100 }}
  source={{
    uri: 'https://...',
    priority: FastImage.priority.normal,
    cache: FastImage.cacheControl.immutable,
  }}
  resizeMode={FastImage.resizeMode.cover}
/>

// Preload images
FastImage.preload([
  { uri: 'https://...' },
  { uri: 'https://...' },
]);

// Progressive loading pattern
function ProgressiveImage({ thumbnail, full }) {
  const [isLoaded, setIsLoaded] = useState(false);

  return (
    <View>
      <FastImage source={{ uri: thumbnail }} style={StyleSheet.absoluteFill} />
      <FastImage
        source={{ uri: full }}
        style={[StyleSheet.absoluteFill, !isLoaded && { opacity: 0 }]}
        onLoad={() => setIsLoaded(true)}
      />
    </View>
  );
}
```

---

### 7.3. JS Bundle & Hermes

**Q: Hermes engine là gì?**

- JavaScript engine được Facebook tối ưu cho React Native
- Compile JS → bytecode tại build time → startup nhanh hơn
- TTI (Time To Interactive) thấp hơn
- Memory footprint nhỏ hơn

```javascript
// Check xem app đang dùng Hermes không
const isHermes = () => !!global.HermesInternal;

// Enable Hermes (Android): android/app/build.gradle
// hermesEnabled = true

// iOS: Podfile
// :hermes_enabled => true
```

---

## PHẦN 8: NATIVE MODULES & PLATFORM

### 8.1. Expo vs React Native CLI

| | Expo Managed | Expo Bare | React Native CLI |
|---|---|---|---|
| Setup | Rất dễ | Dễ | Phức tạp hơn |
| Native code | Không được | Được | Được |
| Custom native module | Không | Được | Được |
| OTA update | Có (Expo Updates) | Có | Cần tự setup |
| App size | Lớn hơn | Trung bình | Nhỏ nhất |
| Khi nào dùng | MVP, học tập | Phổ biến nhất | Full control |

---

### 8.2. Native Modules

```javascript
// Gọi native code từ JS (tương tự Platform Channel của Flutter)
import { NativeModules, Platform } from 'react-native';

const { BiometricModule } = NativeModules;

async function authenticate() {
  if (Platform.OS === 'ios') {
    const result = await BiometricModule.authenticateWithFaceID();
    return result.success;
  } else {
    const result = await BiometricModule.authenticateWithFingerprint();
    return result.success;
  }
}

// Thường dùng thư viện có sẵn thay vì tự viết:
// react-native-biometrics
// react-native-camera
// react-native-maps
// react-native-push-notification
```

---

### 8.3. Permissions

```javascript
import { PermissionsAndroid, Platform } from 'react-native';
import { request, PERMISSIONS, RESULTS } from 'react-native-permissions';

async function requestCameraPermission() {
  const result = await request(
    Platform.OS === 'ios'
      ? PERMISSIONS.IOS.CAMERA
      : PERMISSIONS.ANDROID.CAMERA
  );

  switch (result) {
    case RESULTS.GRANTED:
      return true;
    case RESULTS.DENIED:
      // Hiện dialog giải thích tại sao cần permission
      return false;
    case RESULTS.BLOCKED:
      // User đã từ chối vĩnh viễn → redirect to settings
      Linking.openSettings();
      return false;
  }
}
```

---

## PHẦN 9: NETWORKING & DATA

### 9.1. API Layer

```javascript
// Axios với interceptors
const apiClient = axios.create({
  baseURL: Config.API_URL,
  timeout: 10000,
});

// Request interceptor — attach token
apiClient.interceptors.request.use(async (config) => {
  const token = await getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Response interceptor — handle refresh token
let isRefreshing = false;
let failedQueue = [];

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Queue request lại, chờ refresh xong
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return apiClient(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const newToken = await refreshToken();
        processQueue(null, newToken);
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      } catch (err) {
        processQueue(err, null);
        logout(); // refresh thất bại → logout
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);
```

---

### 9.2. Offline Support & AsyncStorage

```javascript
// AsyncStorage — key-value storage (như SharedPreferences)
import AsyncStorage from '@react-native-async-storage/async-storage';

// Lưu
await AsyncStorage.setItem('user', JSON.stringify(user));

// Đọc
const raw = await AsyncStorage.getItem('user');
const user = raw ? JSON.parse(raw) : null;

// Xóa
await AsyncStorage.removeItem('user');

// Batch operations
await AsyncStorage.multiSet([
  ['key1', 'value1'],
  ['key2', 'value2'],
]);

// Offline-first với React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 phút
      cacheTime: 24 * 60 * 60 * 1000, // 24 giờ
      networkMode: 'offlineFirst', // dùng cache khi offline
    },
  },
});
```

---

## PHẦN 10: TESTING

### 10.1. Jest + React Native Testing Library

```javascript
// Component test
import { render, fireEvent, waitFor } from '@testing-library/react-native';

describe('LoginScreen', () => {
  it('shows error when credentials invalid', async () => {
    const mockLogin = jest.fn().mockRejectedValue(new Error('Invalid'));

    const { getByPlaceholderText, getByText, queryByText } = render(
      <LoginScreen onLogin={mockLogin} />
    );

    // Tương tác
    fireEvent.changeText(getByPlaceholderText('Email'), 'test@mail.com');
    fireEvent.changeText(getByPlaceholderText('Password'), '123456');
    fireEvent.press(getByText('Login'));

    // Chờ async
    await waitFor(() => {
      expect(queryByText('Invalid')).toBeTruthy();
    });

    expect(mockLogin).toHaveBeenCalledWith({
      email: 'test@mail.com',
      password: '123456',
    });
  });

  it('navigates to Home on success', async () => {
    const mockNavigate = jest.fn();
    const mockLogin = jest.fn().mockResolvedValue({ user: { id: 1 } });

    // Mock navigation
    jest.mock('@react-navigation/native', () => ({
      ...jest.requireActual('@react-navigation/native'),
      useNavigation: () => ({ navigate: mockNavigate }),
    }));

    const { getByText } = render(<LoginScreen onLogin={mockLogin} />);
    fireEvent.press(getByText('Login'));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('Home');
    });
  });
});

// Hook test
import { renderHook, act } from '@testing-library/react-native';

test('useCounter increments', () => {
  const { result } = renderHook(() => useCounter());

  act(() => {
    result.current.increment();
  });

  expect(result.current.count).toBe(1);
});
```

---

### 10.2. Mock trong React Native

```javascript
// jest.config.js
module.exports = {
  preset: 'react-native',
  setupFilesAfterFramework: ['@testing-library/jest-native/extend-expect'],
};

// Mock native modules
jest.mock('react-native-permissions', () => ({
  request: jest.fn(() => Promise.resolve('granted')),
  PERMISSIONS: { IOS: { CAMERA: 'camera' } },
  RESULTS: { GRANTED: 'granted' },
}));

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () =>
  require('@react-native-async-storage/async-storage/jest/async-storage-mock')
);

// Mock navigation
const mockNavigate = jest.fn();
jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
    goBack: jest.fn(),
  }),
  useRoute: () => ({ params: { id: '123' } }),
}));
```

---

## PHẦN 11: ARCHITECTURE & CODE STRUCTURE

### 11.1. Feature-based Structure

```
src/
├── components/         # Shared/common components
│   ├── Button/
│   │   ├── Button.tsx
│   │   ├── Button.test.tsx
│   │   └── index.ts
│   └── ...
│
├── screens/            # Screen components
│   ├── Auth/
│   │   ├── LoginScreen.tsx
│   │   └── RegisterScreen.tsx
│   └── Home/
│
├── navigation/         # Navigation setup
│   ├── RootNavigator.tsx
│   ├── AuthNavigator.tsx
│   └── types.ts
│
├── store/              # Redux/Zustand
│   ├── index.ts
│   ├── hooks.ts
│   └── slices/
│       ├── authSlice.ts
│       └── userSlice.ts
│
├── services/           # API calls
│   ├── api.ts
│   ├── authService.ts
│   └── userService.ts
│
├── hooks/              # Custom hooks
│   ├── useAuth.ts
│   ├── useFetch.ts
│   └── useDebounce.ts
│
├── utils/              # Helper functions
├── constants/          # App constants, themes
└── types/              # TypeScript types
```

---

### 11.2. Error Boundaries

```javascript
class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // Log lên Sentry, Crashlytics...
    logError(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <ErrorScreen onRetry={() => this.setState({ hasError: false })} />;
    }
    return this.props.children;
  }
}

// Sử dụng
<ErrorBoundary>
  <App />
</ErrorBoundary>
```

---

## PHẦN 12: CÂU HỎI TÌNH HUỐNG THỰC TẾ

### Q1: App bị re-render nhiều lần không cần thiết. Bạn debug và fix thế nào?

**Trả lời mẫu:**
1. **Debug**: Dùng React DevTools Profiler để xem component nào re-render
2. **Nguyên nhân phổ biến**:
   - Props là object/array mới mỗi lần render
   - Function không được `useCallback`
   - State ở level quá cao, khi thay đổi render toàn bộ tree
3. **Fix**:
   - Wrap component với `React.memo`
   - Wrap functions với `useCallback`
   - Wrap computed values với `useMemo`
   - Tách state xuống component nhỏ hơn
   - Dùng state management library (Redux/Zustand) thay vì Context cho data thay đổi thường

---

### Q2: Cách implement infinite scroll?

```javascript
function InfiniteList() {
  const [page, setPage] = useState(1);
  const [items, setItems] = useState([]);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);

  const loadMore = useCallback(async () => {
    if (loading || !hasMore) return;

    setLoading(true);
    const newItems = await fetchItems(page);
    if (newItems.length === 0) {
      setHasMore(false);
    } else {
      setItems(prev => [...prev, ...newItems]);
      setPage(prev => prev + 1);
    }
    setLoading(false);
  }, [page, loading, hasMore]);

  return (
    <FlatList
      data={items}
      renderItem={({ item }) => <ItemCard item={item} />}
      keyExtractor={(item) => item.id}
      onEndReached={loadMore}
      onEndReachedThreshold={0.5} // load khi còn 50% cuối
      ListFooterComponent={loading ? <ActivityIndicator /> : null}
    />
  );
}
```

---

### Q3: Push Notification flow như thế nào?

**Trả lời mẫu:**
1. **Setup**: Firebase Cloud Messaging (FCM) cho Android, APNs cho iOS
2. **Request permission** → lấy device token
3. **Gửi token lên server** → server lưu map user ↔ token
4. **Server gửi notification** qua FCM/APNs
5. **Handle notification**:
   - App foreground: hiện in-app notification
   - App background/killed: notification tray, khi tap → navigate đến màn hình tương ứng
6. **Deep link từ notification**: parse data trong notification → navigate

```javascript
// Với notifee + firebase/messaging
messaging().onMessage(async remoteMessage => {
  // App ở foreground
  await notifee.displayNotification({
    title: remoteMessage.notification.title,
    body: remoteMessage.notification.body,
    android: { channelId: 'default' },
  });
});

// Khi tap notification (app background)
messaging().onNotificationOpenedApp(remoteMessage => {
  const { screen, params } = remoteMessage.data;
  navigation.navigate(screen, params);
});
```

---

### Q4: Cách handle keyboard trên iOS/Android?

```javascript
// KeyboardAvoidingView
<KeyboardAvoidingView
  behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
  style={{ flex: 1 }}
>
  <ScrollView>
    <TextInput ... />
  </ScrollView>
</KeyboardAvoidingView>

// Lắng nghe keyboard
useEffect(() => {
  const showSub = Keyboard.addListener('keyboardDidShow', (e) => {
    setKeyboardHeight(e.endCoordinates.height);
  });
  const hideSub = Keyboard.addListener('keyboardDidHide', () => {
    setKeyboardHeight(0);
  });
  return () => { showSub.remove(); hideSub.remove(); };
}, []);

// Dismiss keyboard
Keyboard.dismiss();
```

---

### Q5: Cách tổ chức theme (dark mode) trong RN?

```javascript
// ThemeContext
const ThemeContext = createContext(null);

const lightTheme = {
  colors: {
    primary: '#007AFF',
    background: '#FFFFFF',
    text: '#000000',
    border: '#E5E5E5',
  },
  spacing: { s: 8, m: 16, l: 24 },
  typography: { body: 16, title: 24 },
};

const darkTheme = {
  ...lightTheme,
  colors: {
    ...lightTheme.colors,
    background: '#1C1C1E',
    text: '#FFFFFF',
  },
};

function ThemeProvider({ children }) {
  const colorScheme = useColorScheme(); // 'light' | 'dark'
  const [theme, setTheme] = useState(
    colorScheme === 'dark' ? darkTheme : lightTheme
  );

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

const useTheme = () => useContext(ThemeContext);

// Sử dụng
function MyButton({ label }) {
  const { theme } = useTheme();
  return (
    <Pressable style={{ backgroundColor: theme.colors.primary }}>
      <Text style={{ color: theme.colors.text }}>{label}</Text>
    </Pressable>
  );
}
```

---

## PHẦN 13: CÂU HỎI "BẪY" THƯỜNG GẶP

### Bẫy 1: "React Native dùng WebView không?"
→ KHÔNG. RN render **native components** thực sự (UIView trên iOS, View trên Android). Đây là điểm khác biệt với Ionic/Cordova.

### Bẫy 2: "`useEffect` cleanup function chạy khi nào?"
→ 3 trường hợp:
1. Component unmount
2. Trước lần chạy tiếp theo của effect (khi dependency thay đổi)
3. **KHÔNG** phải chỉ khi unmount

### Bẫy 3: "Tại sao không nên gọi hooks trong điều kiện?"
```javascript
// SAI
if (condition) {
  const [state, setState] = useState(0); // LỖI!
}

// Hooks phải gọi theo thứ tự nhất định mỗi render
// React dùng call order để track hooks
// Nếu call order thay đổi (do if/loop) → bugs
```

### Bẫy 4: "Metro bundler là gì?"
→ JavaScript bundler của React Native. Tương tự Webpack nhưng tối ưu cho mobile. Hỗ trợ Hot Reload, tree shaking. Khi build production → bundle thành 1 file JS.

### Bẫy 5: "Sự khác biệt giữa `undefined` và `null` trong JS?"
```javascript
typeof undefined === 'undefined'
typeof null === 'object' // ← bug nổi tiếng của JS từ ngày đầu

undefined == null  // true (loose equality)
undefined === null // false (strict equality)

// null = có chủ ý gán giá trị "không có gì"
// undefined = chưa gán giá trị
```

### Bẫy 6: "`==` vs `===`?"
```javascript
0 == false   // true — type coercion
0 === false  // false — strict comparison

'' == false  // true
'' === false // false

null == undefined  // true
null === undefined // false

// LUÔN dùng === trong dự án thực tế
```

---

## TÓM TẮT: CHECKLIST TRƯỚC PHỎNG VẤN

- [ ] JavaScript: Event Loop, Closure, Prototype, this, Promise, async/await
- [ ] TypeScript: Generics, Utility Types, Discriminated Union
- [ ] RN Core: Architecture (Old vs New), Thread model, Core Components, FlexBox
- [ ] Hooks: useState, useEffect (cleanup, deps), useCallback, useMemo, useRef, custom hooks
- [ ] State Management: Redux Toolkit (createSlice, createAsyncThunk, RTK Query) hoặc Zustand
- [ ] Navigation: React Navigation v6, nested navigators, deep linking, params
- [ ] Animation: Animated API (useNativeDriver), Reanimated 2
- [ ] Performance: FlatList optimization, React.memo, getItemLayout, Hermes
- [ ] Networking: Axios interceptors, offline support, AsyncStorage
- [ ] Testing: React Native Testing Library, Jest mocks
- [ ] Platform: Permissions, Push Notification, Keyboard handling, Dark mode
- [ ] Architecture: Feature-based structure, Error Boundary

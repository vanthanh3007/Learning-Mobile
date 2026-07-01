# Thuật toán & Data Structures

## Mức độ cần thiết cho Senior Mobile

Công ty lớn (Google, Meta, Shopee, VNG) thường test **Easy → Medium LeetCode**. Mục tiêu: đánh giá tư duy logic, không cần nhớ thuộc lòng.

---

## Các chủ đề phổ biến nhất

### 1. Array & String

```dart
// Two Pointers — tìm cặp sum = target
List<int> twoSum(List<int> nums, int target) {
  final map = <int, int>{};
  for (int i = 0; i < nums.length; i++) {
    final complement = target - nums[i];
    if (map.containsKey(complement)) {
      return [map[complement]!, i];
    }
    map[nums[i]] = i;
  }
  return [];
}
// Time: O(n), Space: O(n)
```

```dart
// Sliding Window — max sum subarray độ dài k
int maxSumSubarray(List<int> nums, int k) {
  int windowSum = nums.take(k).reduce((a, b) => a + b);
  int maxSum = windowSum;

  for (int i = k; i < nums.length; i++) {
    windowSum += nums[i] - nums[i - k]; // trượt window
    maxSum = max(maxSum, windowSum);
  }
  return maxSum;
}
// Time: O(n), Space: O(1)
```

### 2. HashMap — O(1) lookup

```dart
// Group Anagrams
Map<String, List<String>> groupAnagrams(List<String> words) {
  final map = <String, List<String>>{};
  for (final word in words) {
    final key = (word.split('')..sort()).join(); // sorted chars làm key
    map.putIfAbsent(key, () => []).add(word);
  }
  return map;
}
// Time: O(n * k log k) — k là độ dài từ
```

### 3. Stack

```dart
// Valid Parentheses
bool isValid(String s) {
  final stack = <String>[];
  final pairs = {')': '(', ']': '[', '}': '{'};

  for (final c in s.split('')) {
    if ('([{'.contains(c)) {
      stack.add(c);
    } else {
      if (stack.isEmpty || stack.last != pairs[c]) return false;
      stack.removeLast();
    }
  }
  return stack.isEmpty;
}
// Time: O(n), Space: O(n)
```

### 4. Binary Search

```dart
// Tìm vị trí trong sorted array
int binarySearch(List<int> nums, int target) {
  int left = 0, right = nums.length - 1;

  while (left <= right) {
    int mid = left + (right - left) ~/ 2; // tránh overflow
    if (nums[mid] == target) return mid;
    if (nums[mid] < target) left = mid + 1;
    else right = mid - 1;
  }
  return -1;
}
// Time: O(log n), Space: O(1)
```

### 5. Tree (BFS & DFS)

```dart
class TreeNode {
  int val;
  TreeNode? left, right;
  TreeNode(this.val);
}

// BFS — Level order traversal
List<List<int>> levelOrder(TreeNode? root) {
  if (root == null) return [];
  final result = <List<int>>[];
  final queue = Queue<TreeNode>()..add(root);

  while (queue.isNotEmpty) {
    final levelSize = queue.length;
    final level = <int>[];
    for (int i = 0; i < levelSize; i++) {
      final node = queue.removeFirst();
      level.add(node.val);
      if (node.left != null) queue.add(node.left!);
      if (node.right != null) queue.add(node.right!);
    }
    result.add(level);
  }
  return result;
}

// DFS — Max depth
int maxDepth(TreeNode? node) {
  if (node == null) return 0;
  return 1 + max(maxDepth(node.left), maxDepth(node.right));
}
```

### 6. Dynamic Programming (cơ bản)

```dart
// Fibonacci — Bottom-up DP
int fib(int n) {
  if (n <= 1) return n;
  int prev = 0, curr = 1;
  for (int i = 2; i <= n; i++) {
    final next = prev + curr;
    prev = curr;
    curr = next;
  }
  return curr;
}
// Time: O(n), Space: O(1)

// Climbing Stairs (giống Fibonacci)
int climbStairs(int n) {
  if (n <= 2) return n;
  int a = 1, b = 2;
  for (int i = 3; i <= n; i++) {
    final c = a + b;
    a = b;
    b = c;
  }
  return b;
}
```

---

## Big O Complexity nên biết

| Operation | Array | HashMap | Binary Search Tree |
|---|---|---|---|
| Access | O(1) | O(1) | O(log n) |
| Search | O(n) | O(1) | O(log n) |
| Insert | O(n) | O(1) | O(log n) |
| Delete | O(n) | O(1) | O(log n) |

---

## Chiến lược làm bài

1. **Clarify** — hỏi edge cases: empty array? null? duplicate?
2. **Brute force** — nói ra giải pháp O(n²) trước
3. **Optimize** — "Tôi có thể dùng HashMap để giảm xuống O(n)"
4. **Code** — viết clean, đặt tên biến rõ ràng
5. **Test** — chạy tay với ví dụ, edge case

---

## Bài tập gợi ý

| Bài | Topic | Difficulty |
|---|---|---|
| Two Sum | Array, HashMap | Easy |
| Valid Parentheses | Stack | Easy |
| Merge Intervals | Array, Sort | Medium |
| LRU Cache | HashMap + LinkedList | Medium |
| Binary Tree Level Order | Tree, BFS | Medium |
| Coin Change | DP | Medium |
| Word Search | DFS, Backtracking | Medium |

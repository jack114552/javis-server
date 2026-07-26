import 'dart:convert';
import 'package:http/http.dart' as http;
import 'server_config.dart';

class ApiService {
  static final ApiService _instance = ApiService._();
  factory ApiService() => _instance;
  ApiService._();

  final _client = http.Client();

  // ============================================================
  // 健康检查
  // ============================================================

  Future<Map<String, dynamic>> healthCheck() async {
    final config = ServerConfig();
    final res = await _client.get(
      Uri.parse('${config.baseUrl}/api/system/health'),
    ).timeout(const Duration(seconds: 5));
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  // ============================================================
  // 通知
  // ============================================================

  Future<Map<String, dynamic>> sendNotification({
    required String appName,
    required String title,
    required String body,
  }) async {
    final config = ServerConfig();
    final res = await _client.post(
      Uri.parse('${config.baseUrl}/api/notifications'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'session_id': config.sessionId,
        'app_name': appName,
        'title': title,
        'body': body,
      }),
    ).timeout(const Duration(seconds: 30));
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  // ============================================================
  // 待办
  // ============================================================

  Future<List<Map<String, dynamic>>> getTodos({String? status}) async {
    final config = ServerConfig();
    final url = status != null
        ? '${config.baseUrl}/api/todos?status=$status'
        : '${config.baseUrl}/api/todos';
    final res = await _client.get(Uri.parse(url))
        .timeout(const Duration(seconds: 10));
    final data = jsonDecode(res.body) as Map<String, dynamic>;
    return (data['todos'] as List).cast<Map<String, dynamic>>();
  }

  Future<void> completeTodo(int id) async {
    final config = ServerConfig();
    await _client.patch(
      Uri.parse('${config.baseUrl}/api/todos/$id'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'status': 'done'}),
    ).timeout(const Duration(seconds: 10));
  }

  Future<void> deleteTodo(int id) async {
    final config = ServerConfig();
    await _client.delete(
      Uri.parse('${config.baseUrl}/api/todos/$id'),
    ).timeout(const Duration(seconds: 10));
  }

  Future<Map<String, dynamic>> createTodo({
    required String title,
    String description = '',
    String? deadlineUtc,
    String deadlineText = '',
    String priority = 'medium',
  }) async {
    final config = ServerConfig();
    final res = await _client.post(
      Uri.parse('${config.baseUrl}/api/todos'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'title': title,
        'description': description,
        'deadline_utc': deadlineUtc,
        'deadline_text': deadlineText,
        'source': '手动',
        'priority': priority,
      }),
    ).timeout(const Duration(seconds: 10));
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<void> updateTodo(int id, Map<String, dynamic> fields) async {
    final config = ServerConfig();
    await _client.patch(
      Uri.parse('${config.baseUrl}/api/todos/$id'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(fields),
    ).timeout(const Duration(seconds: 10));
  }

  // ============================================================
  // 提醒
  // ============================================================

  Future<List<Map<String, dynamic>>> getReminders({int triggered = 0}) async {
    final config = ServerConfig();
    final res = await _client.get(
      Uri.parse('${config.baseUrl}/api/reminders?triggered=$triggered'),
    ).timeout(const Duration(seconds: 10));
    final data = jsonDecode(res.body) as Map<String, dynamic>;
    return (data['reminders'] as List).cast<Map<String, dynamic>>();
  }

  // ============================================================
  // 记忆
  // ============================================================

  Future<List<Map<String, dynamic>>> getMemories({String? q}) async {
    final config = ServerConfig();
    var url = '${config.baseUrl}/api/memories';
    if (q != null && q.isNotEmpty) {
      url += '?q=$q';
    }
    final res = await _client.get(Uri.parse(url))
        .timeout(const Duration(seconds: 10));
    final data = jsonDecode(res.body) as Map<String, dynamic>;
    return (data['memories'] as List).cast<Map<String, dynamic>>();
  }

  Future<List<String>> getMemoryCategories() async {
    final config = ServerConfig();
    final res = await _client.get(
      Uri.parse('${config.baseUrl}/api/memories/categories'),
    ).timeout(const Duration(seconds: 10));
    final data = jsonDecode(res.body) as Map<String, dynamic>;
    return (data['categories'] as List).cast<String>();
  }

  Future<void> deleteMemory(int id) async {
    final config = ServerConfig();
    await _client.delete(
      Uri.parse('${config.baseUrl}/api/memories/$id'),
    ).timeout(const Duration(seconds: 10));
  }
}

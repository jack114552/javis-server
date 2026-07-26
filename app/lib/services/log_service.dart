import 'dart:collection';
import 'package:flutter/foundation.dart';

/// 单条事件日志
class LogEntry {
  final DateTime time;
  final String type;   // 'notification' | 'ai' | 'tool' | 'system' | 'error'
  final String message;
  final Map<String, dynamic>? detail;

  LogEntry({
    required this.type,
    required this.message,
    this.detail,
    DateTime? time,
  }) : time = time ?? DateTime.now();
}

/// 应用内事件日志服务（循环队列，保留最近 200 条）
class LogService {
  static final LogService _instance = LogService._();
  factory LogService() => _instance;
  LogService._();

  final Queue<LogEntry> _logs = Queue();
  static const int maxLogs = 200;

  // 通知监听者
  final List<VoidCallback> _listeners = [];

  void addListener(VoidCallback cb) => _listeners.add(cb);
  void removeListener(VoidCallback cb) => _listeners.remove(cb);

  UnmodifiableListView<LogEntry> get logs => UnmodifiableListView(_logs.toList());

  void add(LogEntry entry) {
    _logs.add(entry);
    if (_logs.length > maxLogs) {
      _logs.removeFirst();
    }
    for (final cb in _listeners) {
      cb();
    }
  }

  void info(String message, {Map<String, dynamic>? detail}) {
    add(LogEntry(type: 'system', message: message, detail: detail));
    debugPrint('[Javis] $message');
  }

  void notification(String app, String title) {
    add(LogEntry(type: 'notification', message: '来自 [$app] $title'));
  }

  void aiResponse(String content) {
    add(LogEntry(type: 'ai', message: content.length > 60 ? '${content.substring(0, 60)}...' : content));
  }

  void toolCall(String name, Map<String, dynamic> args) {
    add(LogEntry(type: 'tool', message: '调用 $name', detail: args));
  }

  void error(String message) {
    add(LogEntry(type: 'error', message: message));
  }

  void clear() {
    _logs.clear();
    for (final cb in _listeners) {
      cb();
    }
  }
}

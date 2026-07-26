import 'dart:async';
import 'package:flutter/services.dart';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';
import 'server_config.dart';
import 'log_service.dart';

class _DedupStore {
  static const _key = 'processed_notifications';
  Set<String> _processed = {};

  Future<void> load() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getStringList(_key) ?? [];
      _processed = raw.toSet();
    } catch (_) {}
  }

  bool isProcessed(String fingerprint) => _processed.contains(fingerprint);

  Future<void> markProcessed(String fingerprint) async {
    _processed.add(fingerprint);
    if (_processed.length > 500) {
      _processed = _processed.skip(_processed.length - 500).toSet();
    }
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setStringList(_key, _processed.toList());
    } catch (_) {}
  }

  void reset() { _processed.clear(); }
}

class NotificationService extends ChangeNotifier {
  static const _channel = MethodChannel('javis/notifications');
  static const _eventChannel = EventChannel('javis/notification_events');

  bool _listening = false;
  Timer? _pollTimer;
  StreamSubscription? _eventSub;
  final _dedup = _DedupStore();

  bool get listening => _listening;

  Future<void> startPolling() async {
    if (_listening) return;
    _listening = true;

    await _dedup.load();
    await _reportTestNotification();

    // 1. 实时通道：NotificationListenerService 推送过来的通知
    _eventSub = _eventChannel.receiveBroadcastStream().listen(
      (data) {
        if (data is Map) {
          _handleNotification(data.cast<String, dynamic>());
        }
      },
      onError: (e) => debugPrint('实时通知通道错误: $e'),
    );
    LogService().info('实时通知通道已开启');

    // 2. 先轮询一次（兜底）
    await _pollNotifications();

    // 3. 定时轮询（备用）
    _pollTimer = Timer.periodic(
      const Duration(minutes: 1),
      (_) => _pollNotifications(),
    );

    notifyListeners();
  }

  void stopPolling() {
    _listening = false;
    _pollTimer?.cancel();
    _eventSub?.cancel();
    _pollTimer = null;
    _eventSub = null;
    notifyListeners();
  }

  /// 处理单条通知（实时通道或轮询共用）
  Future<void> _handleNotification(Map<String, dynamic> notif) async {
    final appName = notif['app_name'] as String? ?? '';
    final title = notif['title'] as String? ?? '';
    final body = notif['body'] as String? ?? '';

    if (title.isEmpty && body.isEmpty) return;

    final fingerprint = '$appName:$title:$body';
    if (_dedup.isProcessed(fingerprint)) return;
    await _dedup.markProcessed(fingerprint);

    LogService().notification(appName, title);

    try {
      await ApiService().sendNotification(
        appName: appName,
        title: title,
        body: body,
      );
      LogService().info('已推送至服务器: [$appName] $title');
    } catch (e) {
      LogService().error('推送失败: $e');
    }
  }

  Future<void> _reportTestNotification() async {
    try {
      await ApiService().sendNotification(
        appName: 'Javis', title: '助手已启动',
        body: '通知监听服务已开始运行',
      );
    } catch (e) {
      debugPrint('通知测试失败: $e');
    }
  }

  Future<void> _pollNotifications() async {
    try {
      final result = await _channel.invokeListMethod<Map>('getNewNotifications');
      if (result == null) return;
      for (final notif in result) {
        await _handleNotification(notif.cast<String, dynamic>());
      }
    } catch (e) {
      debugPrint('通知轮询错误: $e');
    }
  }

  @override
  void dispose() {
    stopPolling();
    super.dispose();
  }
}

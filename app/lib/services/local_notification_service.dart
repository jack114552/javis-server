import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class LocalNotificationService {
  static final LocalNotificationService _instance = LocalNotificationService._();
  factory LocalNotificationService() => _instance;
  LocalNotificationService._();

  final _plugin = FlutterLocalNotificationsPlugin();
  bool _initialized = false;

  Future<void> init() async {
    if (_initialized) return;

    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings(
      requestAlertPermission: false,
      requestBadgePermission: false,
      requestSoundPermission: false,
    );

    await _plugin.initialize(
      const InitializationSettings(android: androidSettings, iOS: iosSettings),
    );

    _initialized = true;
  }

  Future<void> showNotification({
    required String title,
    required String body,
    String? payload,
  }) async {
    await init();

    const androidDetails = AndroidNotificationDetails(
      'javis_reminder',
      'Javis 提醒',
      channelDescription: 'Javis 的待办与提醒通知',
      importance: Importance.high,
      priority: Priority.high,
      showWhen: true,
      enableVibration: true,
      playSound: true,
    );

    const details = NotificationDetails(
      android: androidDetails,
      iOS: DarwinNotificationDetails(),
    );

    await _plugin.show(
      DateTime.now().millisecondsSinceEpoch ~/ 1000,
      title,
      body,
      details,
      payload: payload,
    );
  }
}

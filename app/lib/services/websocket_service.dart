import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:provider/provider.dart';
import 'server_config.dart';

class WebSocketService extends ChangeNotifier {
  WebSocketChannel? _channel;
  bool _connected = false;
  bool _streaming = false;
  final List<ChatMessage> _messages = [];
  String _streamBuffer = "";
  Timer? _reconnectTimer;

  bool get connected => _connected;
  bool get streaming => _streaming;
  List<ChatMessage> get messages => List.unmodifiable(_messages);
  String get streamBuffer => _streamBuffer;

  void connect() {
    final cfg = ServerConfig();
    _connect(cfg.wsUrl);
  }

  void _connect(String url) {
    try {
      _channel = WebSocketChannel.connect(Uri.parse(url));
      _connected = true;
      _reconnectTimer?.cancel();
      notifyListeners();

      _channel!.stream.listen(
        (data) {
          final json = jsonDecode(data as String) as Map<String, dynamic>;
          final type = json["type"] as String?;
          if (type == "notification" || type == "message") {
            final title = json["title"] as String? ?? "";
            final body = json["body"] as String? ?? "";
            _messages.add(ChatMessage(role: "assistant", content: "$title\n$body"));
            notifyListeners();
          }
        },
        onDone: () {
          _connected = false;
          notifyListeners();
          _scheduleReconnect(url);
        },
        onError: (_) {
          _connected = false;
          notifyListeners();
          _scheduleReconnect(url);
        },
      );
    } catch (_) {
      _scheduleReconnect(url);
    }
  }

  void _scheduleReconnect(String url) {
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(const Duration(seconds: 5), () => _connect(url));
  }

  void sendMessage(String text) {
    if (_channel == null || !_connected) return;
    _messages.add(ChatMessage(role: "user", content: text));
    _streamBuffer = "";
    _streaming = true;
    notifyListeners();

    _channel!.sink.add(jsonEncode({
      "type": "message",
      "content": text,
      "session_id": "default",
    }));
  }

  void updateStreamBuffer(String delta) {
    _streamBuffer += delta;
    notifyListeners();
  }

  void endStream() {
    if (_streamBuffer.isNotEmpty) {
      _messages.add(ChatMessage(role: "assistant", content: _streamBuffer));
      _streamBuffer = "";
    }
    _streaming = false;
    notifyListeners();
  }

  @override
  void dispose() {
    _channel?.sink.close();
    _reconnectTimer?.cancel();
    super.dispose();
  }
}

class ChatMessage {
  final String role;
  final String content;
  final DateTime time;

  ChatMessage({required this.role, required this.content}) : time = DateTime.now();
}

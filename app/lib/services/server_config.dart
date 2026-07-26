import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ServerConfig extends ChangeNotifier {
  String _host = "120.26.192.124";
  int _port = 8080;
  bool _connected = false;

  String get host => _host;
  int get port => _port;
  bool get connected => _connected;
  String get wsUrl => "ws://$_host:$port/ws";
  String get apiUrl => "http://$_host:$port";

  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    _host = prefs.getString("server_host") ?? "120.26.192.124";
    _port = prefs.getInt("server_port") ?? 8080;
    notifyListeners();
  }

  Future<void> save(String host, int port) async {
    _host = host;
    _port = port;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString("server_host", host);
    await prefs.setInt("server_port", port);
    notifyListeners();
  }

  void setConnected(bool v) {
    _connected = v;
    notifyListeners();
  }
}

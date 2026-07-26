import 'package:flutter/material.dart';
import '../main.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});
  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _group("SERVER", [
          _tile(Icons.dns_rounded, "Server", "120.26.192.124:8080"),
        ]),
        const SizedBox(height: 16),
        _group("CONNECTION", [
          _tile(Icons.wifi_rounded, "WebSocket", "Connected", color: AppColors.success),
          _tile(Icons.desktop_windows_rounded, "BaiLongma", "Offline", color: AppColors.warning),
        ]),
        const SizedBox(height: 16),
        _group("ABOUT", [
          _tile(Icons.info_rounded, "Version", "v2.0"),
          _tile(Icons.cloud_rounded, "API Key", "Configured"),
        ]),
      ],
    );
  }

  Widget _group(String title, List<Widget> children) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(left: 16, bottom: 8),
          child: Text(title, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.textSecondary, letterSpacing: 1)),
        ),
        Card(
          margin: EdgeInsets.zero,
          child: Column(children: children),
        ),
      ],
    );
  }

  Widget _tile(IconData icon, String title, String subtitle, {Color? color}) {
    return ListTile(
      leading: Container(
        width: 40, height: 40,
        decoration: BoxDecoration(
          color: (color ?? AppColors.textTertiary).withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Icon(icon, color: color ?? AppColors.textTertiary, size: 20),
      ),
      title: Text(title, style: const TextStyle(fontSize: 15, color: AppColors.textPrimary)),
      subtitle: Text(subtitle, style: const TextStyle(fontSize: 12, color: AppColors.textTertiary)),
      trailing: const Icon(Icons.chevron_right_rounded, color: AppColors.textTertiary, size: 20),
    );
  }
}

import 'package:flutter/material.dart';
import '../main.dart';

class LogViewerScreen extends StatelessWidget {
  const LogViewerScreen({super.key});
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 80, height: 80,
            decoration: BoxDecoration(
              color: AppColors.primaryLight,
              borderRadius: BorderRadius.circular(24),
            ),
            child: const Icon(Icons.terminal_rounded, size: 36, color: AppColors.primary),
          ),
          const SizedBox(height: 20),
          const Text("运行时日志", style: AppStyles.h3),
          const SizedBox(height: 6),
          const Text("连接服务器后将实时显示", style: AppStyles.bodySmall),
        ],
      ),
    );
  }
}

import 'package:flutter/material.dart';
import '../main.dart';

class MemoryScreen extends StatelessWidget {
  const MemoryScreen({super.key});
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
            child: const Icon(Icons.memory_rounded, size: 36, color: AppColors.primary),
          ),
          const SizedBox(height: 20),
          const Text("No Memories", style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: AppColors.textPrimary)),
          const SizedBox(height: 6),
          const Text("Javis saves important info automatically", style: TextStyle(fontSize: 13, color: AppColors.textSecondary)),
        ],
      ),
    );
  }
}

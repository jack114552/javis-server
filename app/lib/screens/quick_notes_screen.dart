import 'package:flutter/material.dart';
import '../main.dart';

class QuickNotesScreen extends StatelessWidget {
  const QuickNotesScreen({super.key});
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.lightbulb_rounded, size: 64, color: AppColors.textTertiary.withValues(alpha: 0.3)),
          const SizedBox(height: 16),
          const Text("说\"记个想法\"即可记录灵感", style: TextStyle(color: AppColors.textTertiary, fontSize: 16)),
        ],
      ),
    );
  }
}

import 'package:flutter/material.dart';
import '../main.dart';

class ExpensesScreen extends StatelessWidget {
  const ExpensesScreen({super.key});
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.account_balance_wallet_rounded, size: 64, color: AppColors.textTertiary.withValues(alpha: 0.3)),
          const SizedBox(height: 16),
          const Text("说\"记一笔账\"即可记录", style: TextStyle(color: AppColors.textTertiary, fontSize: 16)),
          const SizedBox(height: 4),
          const Icon(Icons.add_circle_rounded, color: AppColors.primary, size: 40),
        ],
      ),
    );
  }
}

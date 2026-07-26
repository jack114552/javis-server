import 'package:flutter/material.dart';
import '../main.dart';

class NewsScreen extends StatelessWidget {
  const NewsScreen({super.key});
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
            child: const Icon(Icons.article_rounded, size: 36, color: AppColors.primary),
          ),
          const SizedBox(height: 20),
          const Text("新闻每日早八点推送", style: AppStyles.h3),
        ],
      ),
    );
  }
}

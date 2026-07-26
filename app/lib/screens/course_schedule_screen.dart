import 'package:flutter/material.dart';
import '../main.dart';

class CourseScheduleScreen extends StatelessWidget {
  const CourseScheduleScreen({super.key});
  @override
  Widget build(BuildContext context) {
    final days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];
    return ListView(
      padding: const EdgeInsets.all(16),
      children: days.map((day) => Card(
        margin: const EdgeInsets.only(bottom: 8),
        child: ExpansionTile(
          leading: Container(
            width: 40, height: 40,
            decoration: BoxDecoration(
              color: AppColors.primaryLight,
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(Icons.school_rounded, color: AppColors.primary, size: 20),
          ),
          title: Text(day, style: const TextStyle(fontWeight: FontWeight.w600)),
          children: [
            const Padding(
              padding: EdgeInsets.all(16),
              child: Text("暂无课程安排", style: TextStyle(color: AppColors.textTertiary)),
            ),
          ],
        ),
      )).toList(),
    );
  }
}

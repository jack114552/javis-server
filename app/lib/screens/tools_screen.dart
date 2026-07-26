import 'package:flutter/material.dart';
import '../main.dart';

class ToolsScreen extends StatelessWidget {
  const ToolsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final tools = [
      _T("add_todo", "创建待办", Icons.checklist_rounded, const Color(0xFF2563EB)),
      _T("query_todos", "查询待办", Icons.search_rounded, const Color(0xFF7C3AED)),
      _T("complete_todo", "完成待办", Icons.check_circle_rounded, const Color(0xFF10B981)),
      _T("set_reminder", "设置提醒", Icons.notifications_rounded, const Color(0xFFF59E0B)),
      _T("web_search", "联网搜索", Icons.language_rounded, const Color(0xFF06B6D4)),
      _T("get_weather", "查天气", Icons.cloud_rounded, const Color(0xFF6366F1)),
      _T("translate", "翻译", Icons.translate_rounded, const Color(0xFF8B5CF6)),
      _T("add_expense", "记账", Icons.account_balance_wallet_rounded, const Color(0xFF14B8A6)),
      _T("query_schedule", "查课程", Icons.calendar_month_rounded, const Color(0xFFF97316)),
      _T("call_bailongma", "白龙马", Icons.desktop_windows_rounded, const Color(0xFF6B7280)),
    ];

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Padding(
          padding: EdgeInsets.only(bottom: 16, left: 4),
          child: Text("Javis 工具集 (22个)", style: AppStyles.label),
        ),
        Wrap(
          spacing: 8, runSpacing: 8,
          children: tools.map((t) => _ToolCard(t)).toList(),
        ),
      ],
    );
  }
}

class _T {
  final String name, desc;
  final IconData icon;
  final Color color;
  const _T(this.name, this.desc, this.icon, this.color);
}

class _ToolCard extends StatelessWidget {
  final _T t;
  const _ToolCard(this.t);
  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: (MediaQuery.of(context).size.width - 56) / 2,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 36, height: 36,
                decoration: BoxDecoration(
                  color: t.color.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(t.icon, color: t.color, size: 18),
              ),
              const SizedBox(height: 10),
              Text(t.name, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13, color: AppColors.textPrimary)),
              const SizedBox(height: 2),
              Text(t.desc, style: const TextStyle(fontSize: 11, color: AppColors.textTertiary)),
            ],
          ),
        ),
      ),
    );
  }
}

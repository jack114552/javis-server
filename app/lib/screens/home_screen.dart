import 'package:flutter/material.dart';
import '../main.dart';
import 'chat_screen.dart';
import 'todo_screen.dart';
import 'memory_screen.dart';
import 'settings_screen.dart';
import 'news_screen.dart';
import 'course_schedule_screen.dart';
import 'expenses_screen.dart';
import 'quick_notes_screen.dart';
import 'log_viewer_screen.dart';
import 'tools_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;

  final _pages = <Widget>[
    const ChatScreen(),
    const TodoScreen(),
    const MemoryScreen(),
    const CourseScheduleScreen(),
    const NewsScreen(),
    const ExpensesScreen(),
    const QuickNotesScreen(),
    const ToolsScreen(),
    const SettingsScreen(),
    const LogViewerScreen(),
  ];

  // Unicode escapes to avoid Windows encoding issues
  final _titles = [
    "\u5BF9\u8BDD", "\u5F85\u529E", "\u8BB0\u5FC6", "\u8BFE\u7A0B\u8868", "\u65B0\u95FB",
    "\u8BB0\u8D26", "\u7075\u611F", "\u5DE5\u5177", "\u8BBE\u7F6E", "\u65E5\u5FD7",
  ];

  final _icons = <IconData>[
    Icons.chat_rounded,
    Icons.checklist_rounded,
    Icons.memory_rounded,
    Icons.calendar_month_rounded,
    Icons.article_rounded,
    Icons.account_balance_wallet_rounded,
    Icons.lightbulb_rounded,
    Icons.build_rounded,
    Icons.settings_rounded,
    Icons.terminal_rounded,
  ];

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return PopScope(
      canPop: _currentIndex == 0,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop && _currentIndex != 0) setState(() => _currentIndex = 0);
      },
      child: Scaffold(
        backgroundColor: AppColors.background,
        appBar: AppBar(
          leading: Builder(
            builder: (ctx) => IconButton(
              icon: const Icon(Icons.menu_rounded),
              onPressed: () => Scaffold.of(ctx).openDrawer(),
            ),
          ),
          title: Text(_titles[_currentIndex]),
          actions: [
            if (_currentIndex != 1)
              IconButton(
                icon: const Icon(Icons.checklist_rounded),
                onPressed: () => setState(() => _currentIndex = 1),
                tooltip: "Todo",
              ),
          ],
        ),
        drawer: Drawer(
          child: Container(
            color: Colors.white,
            child: Column(
              children: [
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.fromLTRB(20, 60, 20, 24),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFF2563EB), Color(0xFF1D4ED8)],
                      begin: Alignment.topLeft, end: Alignment.bottomRight,
                    ),
                    borderRadius: const BorderRadius.only(
                      bottomLeft: Radius.circular(24), bottomRight: Radius.circular(24),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        width: 48, height: 48,
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.2),
                          borderRadius: BorderRadius.circular(14),
                        ),
                        child: const Icon(Icons.auto_awesome, color: Colors.white, size: 24),
                      ),
                      const SizedBox(height: 12),
                      const Text("Javis", style: TextStyle(
                        color: Colors.white, fontSize: 22, fontWeight: FontWeight.w800, letterSpacing: -0.5,
                      )),
                      Text(
                        "\u751F\u6D3B\u52A9\u7406",
                        style: const TextStyle(
                          color: Colors.white70, fontSize: 13, fontWeight: FontWeight.w400,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 8),
                Expanded(
                  child: ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: 8),
                    itemCount: _titles.length,
                    itemBuilder: (_, i) {
                      final active = _currentIndex == i;
                      return Container(
                        margin: const EdgeInsets.symmetric(vertical: 1),
                        decoration: BoxDecoration(
                          color: active ? cs.primary.withValues(alpha: 0.08) : null,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: ListTile(
                          dense: true,
                          leading: Container(
                            width: 36, height: 36,
                            decoration: BoxDecoration(
                              color: active ? cs.primary.withValues(alpha: 0.12) : AppColors.divider,
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Icon(_icons[i], color: active ? cs.primary : AppColors.textTertiary, size: 18),
                          ),
                          title: Text(_titles[i], style: TextStyle(
                            fontSize: 15,
                            fontWeight: active ? FontWeight.w600 : FontWeight.normal,
                            color: active ? cs.primary : AppColors.textSecondary,
                          )),
                          trailing: active
                              ? Container(width: 4, height: 24,
                                  decoration: BoxDecoration(
                                    color: cs.primary, borderRadius: BorderRadius.circular(3),
                                  ))
                              : null,
                          onTap: () {
                            setState(() => _currentIndex = i);
                            Navigator.pop(context);
                          },
                        ),
                      );
                    },
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  child: Text(
                    "Javis v2.0",
                    style: TextStyle(
                      fontSize: 12, color: AppColors.textTertiary.withValues(alpha: 0.5),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
        body: IndexedStack(index: _currentIndex, children: _pages),
      ),
    );
  }
}

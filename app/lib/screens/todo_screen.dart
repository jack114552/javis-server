import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../main.dart';

class TodoScreen extends StatefulWidget {
  const TodoScreen({super.key});
  @override
  State<TodoScreen> createState() => _TodoScreenState();
}

class _TodoScreenState extends State<TodoScreen> {
  List<TodoItem> _todos = [];
  int _tab = 0;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  Future<void> _fetch() async {
    setState(() => _loading = true);
    try {
      final r = await http.get(Uri.parse("http://120.26.192.124:8080/api/todos?limit=50"));
      if (r.statusCode == 200) {
        final data = jsonDecode(r.body) as Map;
        final list = (data["todos"] as List).map((e) => TodoItem.fromJson(e)).toList();
        setState(() { _todos = list; _loading = false; });
      }
    } catch (_) {}
    setState(() => _loading = false);
  }

  List<TodoItem> get _filtered {
    if (_tab == 0) return _todos.where((t) => t.status == "pending").toList();
    if (_tab == 1) return _todos.where((t) => t.status == "done").toList();
    return _todos;
  }

  Future<void> _delete(int id) async {
    await http.delete(Uri.parse("http://120.26.192.124:8080/api/todos/$id"));
    _fetch();
  }

  Future<void> _toggleDone(int id) async {
    await http.patch(
      Uri.parse("http://120.26.192.124:8080/api/todos/$id"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({"status": "done"}),
    );
    _fetch();
  }

  Future<void> _setReminder(int id) async {
    final date = await showDatePicker(
      context: context,
      initialDate: DateTime.now().add(const Duration(days: 1)),
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (date == null) return;
    if (!mounted) return;
    final time = await showTimePicker(context: context, initialTime: const TimeOfDay(hour: 9, minute: 0));
    if (time == null) return;
    final dt = DateTime(date.year, date.month, date.day, time.hour, time.minute);
    await http.patch(
      Uri.parse("http://120.26.192.124:8080/api/todos/$id"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({"remind_at_utc": dt.toUtc().toIso8601String()}),
    );
    _fetch();
  }

  @override
  Widget build(BuildContext context) {
    final filtered = _filtered;
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Row(
            children: ["Pending", "Done", "All"].asMap().entries.map((e) {
              final active = _tab == e.key;
              return Padding(
                padding: const EdgeInsets.only(right: 8),
                child: GestureDetector(
                  onTap: () => setState(() => _tab = e.key),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 9),
                    decoration: BoxDecoration(
                      gradient: active ? const LinearGradient(colors: [Color(0xFF2563EB), Color(0xFF1D4ED8)]) : null,
                      color: active ? null : Colors.white,
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: active ? Colors.transparent : AppColors.border),
                    ),
                    child: Text(e.value, style: TextStyle(
                      fontSize: 13, fontWeight: FontWeight.w600,
                      color: active ? Colors.white : AppColors.textSecondary,
                    )),
                  ),
                ),
              );
            }).toList(),
          ),
        ),
        Expanded(
          child: _loading
              ? const Center(child: CircularProgressIndicator())
              : filtered.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Container(
                            width: 80, height: 80,
                            decoration: BoxDecoration(color: AppColors.primaryLight, borderRadius: BorderRadius.circular(24)),
                            child: const Icon(Icons.checklist_rounded, size: 36, color: AppColors.primary),
                          ),
                          const SizedBox(height: 20),
                          const Text("No tasks", style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: AppColors.textPrimary)),
                        ],
                      ),
                    )
                  : RefreshIndicator(
                      onRefresh: _fetch,
                      child: ListView.builder(
                        padding: const EdgeInsets.symmetric(horizontal: 16),
                        itemCount: filtered.length,
                        itemBuilder: (_, i) {
                          final t = filtered[i];
                          return Card(
                            margin: const EdgeInsets.only(bottom: 8),
                            child: Padding(
                              padding: const EdgeInsets.all(12),
                              child: Row(
                                children: [
                                  GestureDetector(
                                    onTap: () => _toggleDone(t.id),
                                    child: Container(
                                      width: 24, height: 24,
                                      decoration: BoxDecoration(
                                        color: t.status == "done" ? AppColors.success : Colors.transparent,
                                        borderRadius: BorderRadius.circular(6),
                                        border: Border.all(color: t.status == "done" ? AppColors.success : AppColors.border),
                                      ),
                                      child: t.status == "done"
                                          ? const Icon(Icons.check, color: Colors.white, size: 16)
                                          : null,
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Text(t.title, style: TextStyle(
                                      fontSize: 14,
                                      fontWeight: FontWeight.w500,
                                      color: AppColors.textPrimary,
                                      decoration: t.status == "done" ? TextDecoration.lineThrough : null,
                                    )),
                                  ),
                                  IconButton(
                                    icon: const Icon(Icons.notifications_none_rounded, size: 20, color: AppColors.primary),
                                    onPressed: () => _setReminder(t.id),
                                    tooltip: "Remind",
                                  ),
                                  IconButton(
                                    icon: const Icon(Icons.delete_outline_rounded, size: 20, color: AppColors.error),
                                    onPressed: () => _delete(t.id),
                                    tooltip: "Delete",
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
                    ),
        ),
      ],
    );
  }
}

class TodoItem {
  final int id;
  final String title;
  final String status;

  TodoItem({required this.id, required this.title, required this.status});

  factory TodoItem.fromJson(Map<String, dynamic> json) {
    return TodoItem(
      id: json["id"] as int,
      title: json["title"] as String? ?? "",
      status: json["status"] as String? ?? "pending",
    );
  }
}

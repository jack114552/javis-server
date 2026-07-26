import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../main.dart';
import '../services/websocket_service.dart';

class ChatScreen extends StatelessWidget {
  const ChatScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<WebSocketService>(
      builder: (context, ws, _) {
        return Column(
          children: [
            if (!ws.connected)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 16),
                color: AppColors.warning.withValues(alpha: 0.1),
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    SizedBox(width: 8, height: 8, child: CircularProgressIndicator(strokeWidth: 1.5)),
                    SizedBox(width: 8),
                    Text("Connecting...", style: TextStyle(fontSize: 12, color: AppColors.warning)),
                  ],
                ),
              ),
            Expanded(
              child: ws.messages.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.chat_rounded, size: 64, color: AppColors.textTertiary.withValues(alpha: 0.3)),
                          const SizedBox(height: 16),
                          const Text("Say something", style: TextStyle(color: AppColors.textTertiary, fontSize: 16)),
                        ],
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: ws.messages.length + (ws.streaming ? 1 : 0),
                      itemBuilder: (_, i) {
                        if (i == ws.messages.length && ws.streaming) {
                          return _bubble(ws.streamBuffer, true);
                        }
                        final m = ws.messages[i];
                        return _bubble(m.content, m.role == "assistant");
                      },
                    ),
            ),
            Container(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
              decoration: const BoxDecoration(
                color: Colors.white,
                border: Border(top: BorderSide(color: Color(0xFFE2E8F0))),
              ),
              child: SafeArea(
                top: false,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF1F5F9),
                    borderRadius: BorderRadius.circular(24),
                    border: Border.all(color: const Color(0xFFE2E8F0)),
                  ),
                  child: Row(
                    children: [
                      const Expanded(
                        child: TextField(
                          decoration: InputDecoration(
                            hintText: "Type a message...",
                            border: InputBorder.none,
                            hintStyle: TextStyle(color: Color(0xFF94A3B8), fontSize: 15),
                          ),
                          style: TextStyle(fontSize: 15, color: Color(0xFF0F172A)),
                        ),
                      ),
                      Container(
                        margin: const EdgeInsets.only(left: 4),
                        child: IconButton(
                          icon: const Icon(Icons.send_rounded, size: 20),
                          color: const Color(0xFF2563EB),
                          onPressed: () {},
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _bubble(String content, bool isAi) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        mainAxisAlignment: isAi ? MainAxisAlignment.start : MainAxisAlignment.end,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (isAi) ...[
            Container(
              width: 30, height: 30, margin: const EdgeInsets.only(right: 6),
              decoration: BoxDecoration(
                color: AppColors.primary.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(Icons.auto_awesome, size: 15, color: AppColors.primary),
            ),
          ],
          Flexible(
            child: Container(
              constraints: const BoxConstraints(maxWidth: 300),
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: isAi ? Colors.white : AppColors.primary,
                borderRadius: BorderRadius.circular(18),
                border: isAi ? Border.all(color: const Color(0xFFE2E8F0)) : null,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.04),
                    blurRadius: 8, offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: SelectableText(
                content,
                style: TextStyle(
                  color: isAi ? AppColors.textPrimary : Colors.white,
                  fontSize: 15, height: 1.4,
                ),
              ),
            ),
          ),
          if (!isAi) const SizedBox(width: 6),
        ],
      ),
    );
  }
}

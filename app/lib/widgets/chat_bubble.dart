import 'package:flutter/material.dart';
import '../services/websocket_service.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../main.dart';

class ChatBubble extends StatelessWidget {
  final ChatMessage message;
  const ChatBubble({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        mainAxisAlignment: message.isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (!message.isUser) _avatar(Icons.bolt, AppColors.primary),
          const SizedBox(width: 8),
          ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 280),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: message.isUser ? AppColors.primary : AppColors.surface,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(16), topRight: const Radius.circular(16),
                  bottomLeft: Radius.circular(message.isUser ? 16 : 4),
                  bottomRight: Radius.circular(message.isUser ? 4 : 16),
                ),
                border: message.isUser ? null : Border.all(color: AppColors.border),
                boxShadow: message.isUser ? null : [
                  BoxShadow(color: Colors.black.withAlpha(8), blurRadius: 8, offset: const Offset(0, 2)),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  message.streaming
                      ? _StreamingText(content: message.content)
                      : SelectableText(message.content, style: TextStyle(
                          fontSize: 15, height: 1.5,
                          color: message.isUser ? Colors.white : AppColors.text)),
                  if (message.hasTools) ...[
                    const SizedBox(height: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: message.isUser ? Colors.white.withAlpha(25) : AppColors.primaryLight,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text('已处理', style: TextStyle(
                        fontSize: 11, color: message.isUser ? Colors.white70 : AppColors.primary)),
                    ),
                  ],
                  Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text(
                      '${message.time.hour.toString().padLeft(2, '0')}:${message.time.minute.toString().padLeft(2, '0')}',
                      style: TextStyle(fontSize: 11, color: message.isUser ? Colors.white60 : AppColors.textTertiary)),
                  ),
                ],
              ),
            ),
          ),
          if (message.isUser) const SizedBox(width: 8),
          if (message.isUser) _avatar(Icons.person, AppColors.surfaceHover),
        ],
      ),
    );
  }

  Widget _avatar(IconData icon, Color bg) {
    return Container(
      width: 30, height: 30,
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(8)),
      child: Icon(icon, size: 16, color: icon == Icons.bolt ? Colors.white : AppColors.textSecondary),
    );
  }
}

class _StreamingText extends StatefulWidget {
  final String content;
  const _StreamingText({required this.content});
  @override
  State<_StreamingText> createState() => _StreamingTextState();
}

class _StreamingTextState extends State<_StreamingText> with SingleTickerProviderStateMixin {
  late AnimationController _c;
  @override void initState() { super.initState(); _c = AnimationController(vsync: this, duration: 600.ms)..repeat(reverse: true); }
  @override void dispose() { _c.dispose(); super.dispose(); }
  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Flexible(child: Text(widget.content, style: const TextStyle(fontSize: 15, height: 1.5, color: AppColors.text))),
        FadeTransition(opacity: _c, child: Container(
          width: 2, height: 16, margin: const EdgeInsets.only(top: 3, left: 2),
          decoration: BoxDecoration(color: AppColors.primary, borderRadius: BorderRadius.circular(1)),
        )),
      ],
    );
  }
}

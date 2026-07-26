import 'package:flutter/material.dart';

/// 骨架屏组件（加载占位动画）
class SkeletonBox extends StatefulWidget {
  final double width;
  final double height;
  final double radius;

  const SkeletonBox({
    super.key,
    this.width = double.infinity,
    this.height = 16,
    this.radius = 8,
  });

  @override
  State<SkeletonBox> createState() => _SkeletonBoxState();
}

class _SkeletonBoxState extends State<SkeletonBox> with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (_, child) {
        final opacity = 0.3 + (_controller.value * 0.4);
        return Opacity(
          opacity: opacity,
          child: Container(
            width: widget.width,
            height: widget.height,
            decoration: BoxDecoration(
              color: const Color(0xFF1E1E3A),
              borderRadius: BorderRadius.circular(widget.radius),
            ),
          ),
        );
      },
    );
  }
}

/// 聊天骨架屏
class ChatSkeleton extends StatelessWidget {
  const ChatSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _row(false, [200, 140, 180]),
          const SizedBox(height: 8),
          _row(true, [160, 100]),
          const SizedBox(height: 8),
          _row(false, [240, 120, 80]),
          const SizedBox(height: 8),
          _row(true, [180]),
        ],
      ),
    );
  }

  Widget _row(bool isUser, List<double> widths) {
    return Row(
      mainAxisAlignment: isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
      children: [
        if (!isUser) const SkeletonBox(width: 32, height: 32, radius: 10),
        if (!isUser) const SizedBox(width: 8),
        Column(
          crossAxisAlignment: isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
          children: widths.map((w) => Padding(
            padding: const EdgeInsets.only(bottom: 6),
            child: SkeletonBox(width: w, height: 14),
          )).toList(),
        ),
        if (isUser) const SizedBox(width: 8),
        if (isUser) const SkeletonBox(width: 32, height: 32, radius: 10),
      ],
    );
  }
}

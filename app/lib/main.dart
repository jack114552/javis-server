import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'services/server_config.dart';
import 'services/websocket_service.dart';
import 'screens/home_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => ServerConfig()..load()),
        ChangeNotifierProvider(create: (_) => WebSocketService()..connect()),
      ],
      child: const JavisApp(),
    ),
  );
}

class JavisApp extends StatelessWidget {
  const JavisApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: "Javis",
      debugShowCheckedModeBanner: false,
      theme: _buildTheme(),
      home: const HomeScreen(),
    );
  }

  ThemeData _buildTheme() {
    const primary = Color(0xFF2563EB);
    const secondary = Color(0xFF7C3AED);
    return ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.light(
        primary: primary,
        secondary: secondary,
        surface: Colors.white,
        surfaceContainerHighest: const Color(0xFFF1F5F9),
        onSurface: const Color(0xFF0F172A),
        outline: const Color(0xFFE2E8F0),
      ),
      scaffoldBackgroundColor: const Color(0xFFF8FAFC),
      fontFamily: null,
      appBarTheme: const AppBarTheme(
        centerTitle: true,
        backgroundColor: Colors.white,
        foregroundColor: Color(0xFF0F172A),
        elevation: 0,
        scrolledUnderElevation: 0.5,
        titleTextStyle: TextStyle(
          fontSize: 18, fontWeight: FontWeight.w700, color: Color(0xFF0F172A), letterSpacing: -0.3,
        ),
      ),
      cardTheme: CardTheme(
        color: Colors.white,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: const BorderSide(color: Color(0xFFF1F5F9), width: 1),
        ),
        clipBehavior: Clip.antiAlias,
      ),
      navigationBarTheme: NavigationBarThemeData(
        elevation: 0,
        backgroundColor: Colors.white,
        indicatorColor: primary.withValues(alpha: 0.1),
        labelTextStyle: WidgetStatePropertyAll(
          TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: primary),
        ),
      ),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        backgroundColor: const Color(0xFF0F172A),
      ),
      dividerTheme: const DividerThemeData(
        color: Color(0xFFF1F5F9),
        thickness: 1,
        space: 1,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0xFFF8FAFC),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: Color(0xFFE2E8F0)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: Color(0xFFE2E8F0)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: const BorderSide(color: primary, width: 1.5),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),
    );
  }
}

class AppColors {
  static const primary = Color(0xFF2563EB);
  static const primaryDark = Color(0xFF1D4ED8);
  static const primaryLight = Color(0xFFDBEAFE);
  static const secondary = Color(0xFF7C3AED);
  static const accent = Color(0xFF06B6D4);
  static const success = Color(0xFF10B981);
  static const warning = Color(0xFFF59E0B);
  static const error = Color(0xFFEF4444);
  static const background = Color(0xFFF8FAFC);
  static const surface = Colors.white;
  static const textPrimary = Color(0xFF0F172A);
  static const textSecondary = Color(0xFF64748B);
  static const textTertiary = Color(0xFF94A3B8);
  static const border = Color(0xFFE2E8F0);
  static const divider = Color(0xFFF1F5F9);
  static const cardShadow = Color(0x0D000000);
  static const shimmer = Color(0xFFF1F5F9);
}

class AppStyles {
  static const h1 = TextStyle(fontSize: 28, fontWeight: FontWeight.w800, color: AppColors.textPrimary, letterSpacing: -0.5);
  static const h2 = TextStyle(fontSize: 22, fontWeight: FontWeight.w700, color: AppColors.textPrimary, letterSpacing: -0.3);
  static const h3 = TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: AppColors.textPrimary);
  static const body = TextStyle(fontSize: 15, fontWeight: FontWeight.w400, color: AppColors.textPrimary, height: 1.5);
  static const bodySmall = TextStyle(fontSize: 13, fontWeight: FontWeight.w400, color: AppColors.textSecondary);
  static const caption = TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: AppColors.textTertiary);
  static const label = TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.textSecondary, letterSpacing: 0.5);
}

class Deco {
  static BoxDecoration glassCard = BoxDecoration(
    color: Colors.white.withValues(alpha: 0.8),
    borderRadius: BorderRadius.circular(20),
    border: Border.all(color: Colors.white.withValues(alpha: 0.3)),
    boxShadow: [
      BoxShadow(
        color: Colors.black.withValues(alpha: 0.04),
        blurRadius: 20, offset: const Offset(0, 4),
      ),
      BoxShadow(
        color: AppColors.primary.withValues(alpha: 0.02),
        blurRadius: 40, offset: const Offset(0, 8),
      ),
    ],
  );

  static BoxDecoration primaryGradient = BoxDecoration(
    gradient: const LinearGradient(
      colors: [AppColors.primary, AppColors.primaryDark],
      begin: Alignment.topLeft, end: Alignment.bottomRight,
    ),
    borderRadius: BorderRadius.circular(20),
  );

  static BoxDecoration iconBg = BoxDecoration(
    color: AppColors.primaryLight,
    borderRadius: BorderRadius.circular(14),
  );
}

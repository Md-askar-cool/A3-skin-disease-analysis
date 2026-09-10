import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/screening_result.dart';
import '../services/api_service.dart';

/// FutureProvider that fetches screening history list from the API.
final historyProvider =
    FutureProvider.autoDispose<List<ScreeningHistoryItem>>((ref) async {
  return apiService.getScreeningHistory();
});

/// Provider for a single screening detail by ID
final screeningDetailProvider =
    FutureProvider.autoDispose.family<ScreeningResult, String>((ref, id) async {
  return apiService.getScreening(id);
});

/// StateNotifier for managing history operations (delete, refresh)
class HistoryNotifier extends StateNotifier<AsyncValue<List<ScreeningHistoryItem>>> {
  HistoryNotifier() : super(const AsyncValue.loading()) {
    load();
  }

  Future<void> load() async {
    state = const AsyncValue.loading();
    try {
      final items = await apiService.getScreeningHistory();
      state = AsyncValue.data(items);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  Future<void> delete(String id) async {
    await apiService.deleteScreening(id);
    // Optimistically remove from local state
    state.whenData((items) {
      state = AsyncValue.data(items.where((i) => i.id != id).toList());
    });
  }

  Future<void> deleteAll() async {
    await apiService.deleteAllScreenings();
    state = const AsyncValue.data([]);
  }
}

final historyNotifierProvider =
    StateNotifierProvider.autoDispose<HistoryNotifier, AsyncValue<List<ScreeningHistoryItem>>>(
  (ref) => HistoryNotifier(),
);

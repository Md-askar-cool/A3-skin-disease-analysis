import 'dart:io';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/screening_result.dart';
import '../services/api_service.dart';

/// State for the progress tracker
class ProgressState {
  final List<ProgressImage> images;
  final bool isLoading;
  final String? errorMessage;
  final String? selectedId1;
  final String? selectedId2;

  const ProgressState({
    this.images = const [],
    this.isLoading = false,
    this.errorMessage,
    this.selectedId1,
    this.selectedId2,
  });

  ProgressState copyWith({
    List<ProgressImage>? images,
    bool? isLoading,
    String? errorMessage,
    String? selectedId1,
    String? selectedId2,
  }) {
    return ProgressState(
      images: images ?? this.images,
      isLoading: isLoading ?? this.isLoading,
      errorMessage: errorMessage,
      selectedId1: selectedId1 ?? this.selectedId1,
      selectedId2: selectedId2 ?? this.selectedId2,
    );
  }

  /// Whether two images are selected for comparison
  bool get canCompare => selectedId1 != null && selectedId2 != null;
}

class ProgressNotifier extends StateNotifier<ProgressState> {
  final ApiService _api;

  ProgressNotifier(this._api) : super(const ProgressState()) {
    load();
  }

  Future<void> load() async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final images = await _api.getProgress();
      state = state.copyWith(images: images, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, errorMessage: e.toString());
    }
  }

  Future<void> addImage(File image, {String? notes, String? bodyPart}) async {
    state = state.copyWith(isLoading: true, errorMessage: null);
    try {
      final newImage = await _api.addProgressImage(image, notes: notes, bodyPart: bodyPart);
      final updated = [newImage, ...state.images];
      state = state.copyWith(images: updated, isLoading: false);
    } catch (e) {
      state = state.copyWith(isLoading: false, errorMessage: e.toString());
    }
  }

  Future<void> delete(String id) async {
    try {
      await _api.deleteProgressEntry(id);
      final updated = state.images.where((img) => img.id != id).toList();
      state = state.copyWith(
        images: updated,
        selectedId1: state.selectedId1 == id ? null : state.selectedId1,
        selectedId2: state.selectedId2 == id ? null : state.selectedId2,
      );
    } catch (e) {
      state = state.copyWith(errorMessage: e.toString());
    }
  }

  Future<void> deleteAll() async {
    try {
      await _api.deleteAllProgress();
      state = const ProgressState();
    } catch (e) {
      state = state.copyWith(errorMessage: e.toString());
    }
  }

  void toggleSelection(String id) {
    if (state.selectedId1 == id) {
      state = state.copyWith(selectedId1: null);
    } else if (state.selectedId2 == id) {
      state = state.copyWith(selectedId2: null);
    } else if (state.selectedId1 == null) {
      state = state.copyWith(selectedId1: id);
    } else if (state.selectedId2 == null) {
      state = state.copyWith(selectedId2: id);
    }
    // If both slots filled, replace the older selection
  }

  void clearSelection() {
    state = ProgressState(images: state.images);
  }
}

final progressProvider =
    StateNotifierProvider.autoDispose<ProgressNotifier, ProgressState>(
  (ref) => ProgressNotifier(apiService),
);

import { create } from 'zustand';

interface UiState {
  isSidebarCollapsed: boolean;
  setSidebarCollapsed: (isCollapsed: boolean) => void;
}

export const useUiStore = create<UiState>((set) => ({
  isSidebarCollapsed: false,
  setSidebarCollapsed: (isSidebarCollapsed: boolean): void =>
    set({ isSidebarCollapsed }),
}));

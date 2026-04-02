// src/store/authStore.js
import { create } from "zustand";

export const useAuthStore = create((set) => ({
  user: JSON.parse(localStorage.getItem("user")) || null,

  // Login function
  login: (userData) => {
    localStorage.setItem("user", JSON.stringify(userData));
    set({ user: userData });
  },

  // Logout function
  logout: () => {
    localStorage.removeItem("user");
    set({ user: null });
  },
}));
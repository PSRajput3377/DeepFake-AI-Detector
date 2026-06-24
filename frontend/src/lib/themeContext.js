import { createContext, useContext } from "react";

export const ThemeContext = createContext({
  theme: "dark",
  setTheme: () => {},
  toggle: () => {},
});

export function useTheme() {
  return useContext(ThemeContext);
}

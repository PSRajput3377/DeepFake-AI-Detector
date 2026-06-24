import { createContext, useContext } from "react";

export const ToastContext = createContext({
  toast: () => {},
});

export function useToast() {
  return useContext(ToastContext);
}

import { useEffect, useRef, useCallback } from "react";
import {
  isPermissionGranted,
  requestPermission,
  sendNotification,
} from "@tauri-apps/plugin-notification";

export function useNotifications() {
  const permitted = useRef(false);

  useEffect(() => {
    (async () => {
      let ok = await isPermissionGranted();
      if (!ok) {
        const result = await requestPermission();
        ok = result === "granted";
      }
      permitted.current = ok;
    })();
  }, []);

  const notify = useCallback((title: string, body?: string) => {
    if (!permitted.current) return;
    sendNotification({ title, body });
  }, []);

  return { notify };
}

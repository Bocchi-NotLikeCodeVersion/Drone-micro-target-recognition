// utils/log.js
import store from '@/store';

export function logUserAction(action, description) {
  const logEntry = {
    action,
    description,
    timestamp: new Date().toISOString()
  };
  store.dispatch('logAction', logEntry);
}
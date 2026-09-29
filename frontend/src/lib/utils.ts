export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}

export function formatDateTime(dateInput: string | number | Date | null | undefined): string {
  if (!dateInput) return '—';
  const date = new Date(dateInput);
  if (isNaN(date.getTime())) return 'Invalid date';
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  }).format(date);
}

export function formatRelativeTime(dateInput: string | number | Date | null | undefined): string {
  if (!dateInput) return '—';
  const date = new Date(dateInput);
  if (isNaN(date.getTime())) return '—';
  
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) {
    return 'Just now';
  }
  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) {
    return `${diffInMinutes}m ago`;
  }
  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) {
    return `${diffInHours}h ago`;
  }
  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays === 1) {
    return 'Yesterday';
  }
  if (diffInDays < 7) {
    return `${diffInDays}d ago`;
  }
  return formatDateTime(date);
}

export function formatDuration(durationMs?: number): string {
  if (!durationMs && durationMs !== 0) return '—';
  if (durationMs < 1000) return `${durationMs}ms`;
  const seconds = Math.floor(durationMs / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}m ${remainingSeconds}s`;
}

/**
 * Converts common cron syntax or schedule presets into plain English descriptions
 */
export function describeCronExpression(cron: string): string {
  const trimmed = cron.trim();
  if (!trimmed) return 'No schedule specified';

  // Common preset keywords
  switch (trimmed.toLowerCase()) {
    case 'hourly':
    case '0 * * * *':
      return 'Runs at minute 0 of every hour';
    case 'daily':
    case '0 8 * * *':
      return 'Runs every day at 08:00 AM UTC';
    case '0 9 * * 1':
    case 'weekly':
      return 'Runs every Monday at 09:00 AM UTC';
    case '0 0 * * *':
      return 'Runs every day at midnight (00:00 UTC)';
    case '*/5 * * * *':
      return 'Runs every 5 minutes';
    case '*/15 * * * *':
      return 'Runs every 15 minutes';
    case '*/30 * * * *':
      return 'Runs every 30 minutes';
    case '0 0 1 * *':
      return 'Runs on the 1st of every month at midnight';
    case '0 18 * * 1-5':
      return 'Runs weekdays (Mon-Fri) at 06:00 PM UTC';
  }

  // Parse standard 5-part cron
  const parts = trimmed.split(/\s+/);
  if (parts.length === 5) {
    const [min, hour, dom, mon, dow] = parts;
    
    // Every X minutes
    if (min.startsWith('*/') && hour === '*' && dom === '*' && mon === '*' && dow === '*') {
      const step = min.replace('*/', '');
      return `Runs every ${step} minutes`;
    }

    // Daily at HH:MM
    if (!min.includes('*') && !min.includes('/') && !hour.includes('*') && !hour.includes('/') && dom === '*' && mon === '*' && dow === '*') {
      const h = parseInt(hour, 10);
      const m = min.padStart(2, '0');
      const ampm = h >= 12 ? 'PM' : 'AM';
      const formattedHour = h % 12 || 12;
      return `Runs every day at ${formattedHour}:${m} ${ampm} UTC`;
    }

    // Weekly on day of week
    if (!min.includes('*') && !hour.includes('*') && dom === '*' && mon === '*' && dow !== '*') {
      const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
      const dayName = days[parseInt(dow, 10)] || `day ${dow}`;
      const h = parseInt(hour, 10);
      const m = min.padStart(2, '0');
      const ampm = h >= 12 ? 'PM' : 'AM';
      const formattedHour = h % 12 || 12;
      return `Runs every ${dayName} at ${formattedHour}:${m} ${ampm} UTC`;
    }

    return `Custom cron schedule (${trimmed})`;
  }

  return `Schedule: ${trimmed}`;
}

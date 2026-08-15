export function formatDate(value: unknown) {
  if (!value) return "—";
  const date = new Date(String(value));
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit", timeZone: "America/Sao_Paulo",
  }).format(date).replace(",", " às");
}

export function duration(value: unknown) {
  const seconds = Math.round(Number(value || 0));
  if (!seconds) return "—";
  if (seconds < 60) return `${seconds} s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)} min${seconds % 60 ? ` ${seconds % 60} s` : ""}`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} h${Math.floor((seconds % 3600) / 60) ? ` ${Math.floor((seconds % 3600) / 60)} min` : ""}`;
  return `${Math.floor(seconds / 86400)} d${Math.floor((seconds % 86400) / 3600) ? ` ${Math.floor((seconds % 86400) / 3600)} h` : ""}`;
}

export function relativeDuration(value: unknown) {
  const formatted = duration(value);
  return formatted === "—" ? "Sem dados" : `há ${formatted}`;
}

export function number(value: unknown) {
  return new Intl.NumberFormat("pt-BR").format(Number(value || 0));
}

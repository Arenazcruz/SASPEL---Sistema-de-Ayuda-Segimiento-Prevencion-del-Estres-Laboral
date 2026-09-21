import { ValidatorFn } from '@angular/forms';

export const normalizeName = (value: string) => value.normalize('NFC').trim().replace(/ +/g, ' ');

export const personName: ValidatorFn = ({ value }) => {
  if (!value) return null;
  return /^\p{L}[\p{L}\p{M}]*(?: +\p{L}[\p{L}\p{M}]*)*$/u.test(normalizeName(value))
    ? null
    : { personName: true };
};
export const employeeCode: ValidatorFn = ({ value }) =>
  !value || /^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$/.test(value.trim()) ? null : { employeeCode: true };
export const phoneNumber: ValidatorFn = ({ value }) =>
  !value || /^[0-9]{8,15}$/.test(value.trim()) ? null : { phoneNumber: true };

/** Usa la fecha institucional, incluso si el navegador está en otra zona horaria. */
export function institutionalToday(): string {
  const parts = new Intl.DateTimeFormat('en', {
    timeZone: 'America/La_Paz',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(new Date());
  const part = (type: string) => parts.find((entry) => entry.type === type)!.value;
  return `${part('year')}-${part('month')}-${part('day')}`;
}

export function birthDateBounds(today = institutionalToday()) {
  const [year, month, day] = today.split('-').map(Number);
  const yearsAgo = (years: number) =>
    new Date(
      Date.UTC(
        year - years,
        month - 1,
        Math.min(day, new Date(Date.UTC(year - years, month, 0)).getUTCDate()),
      ),
    );
  const minimum = yearsAgo(78);
  minimum.setUTCDate(minimum.getUTCDate() + 1);
  return { min: minimum.toISOString().slice(0, 10), max: yearsAgo(19).toISOString().slice(0, 10) };
}

export const birthDate: ValidatorFn = ({ value }) => {
  if (!value) return null;
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return { birthDate: true };
  const parsed = new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(parsed.getTime()) || parsed.toISOString().slice(0, 10) !== value) {
    return { birthDate: true };
  }
  const bounds = birthDateBounds();
  return value >= bounds.min && value <= bounds.max ? null : { ageRange: true };
};

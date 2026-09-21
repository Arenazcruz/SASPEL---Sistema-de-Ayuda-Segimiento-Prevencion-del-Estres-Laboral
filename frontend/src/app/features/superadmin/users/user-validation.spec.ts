import { FormControl } from '@angular/forms';
import {
  birthDate,
  birthDateBounds,
  employeeCode,
  institutionalToday,
  personName,
  phoneNumber,
} from './user-validation';

describe('Validación de datos personales', () => {
  it('admite nombres con tildes y ñ, y rechaza números y símbolos', () => {
    for (const name of ['Jesús Gabriel', 'Muñoz', 'Jesu\u0301s', '  Ana   María ']) {
      expect(personName(new FormControl(name))).toBeNull();
    }
    for (const name of ['Ana123', 'Pérez!', 'Ana-María', "O'Neill", 'Ana\nMaría', '😀', '   ']) {
      expect(personName(new FormControl(name))).not.toBeNull();
    }
  });
  it('valida códigos alfanuméricos y teléfonos de longitud limitada', () => {
    for (const code of ['123', 'AB123', 'AB-123'])
      expect(employeeCode(new FormControl(code))).toBeNull();
    for (const code of ['AB_12', '-AB', 'AB--12', 'AB 12', '!!!'])
      expect(employeeCode(new FormControl(code))).not.toBeNull();
    for (const phone of ['', '00123456', '1'.repeat(15)])
      expect(phoneNumber(new FormControl(phone))).toBeNull();
    for (const phone of [
      '1234567',
      '1'.repeat(16),
      '+59170000000',
      '7000 0000',
      '7000000a',
      '１２３４５６７８',
    ]) {
      expect(phoneNumber(new FormControl(phone))).not.toBeNull();
    }
  });
});

describe('Edad institucional', () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ['Date'] });
    vi.setSystemTime(new Date('2026-09-21T12:00:00Z'));
  });
  afterEach(() => vi.useRealTimers());
  it('acepta 19 a 77 años cumplidos y rechaza fechas inválidas o futuras', () => {
    for (const value of ['2007-09-21', '1948-09-22', '1949-09-21']) {
      expect(birthDate(new FormControl(value))).toBeNull();
    }
    for (const value of [
      '2008-09-21',
      '2007-09-22',
      '1948-09-21',
      '2099-01-01',
      '2000-02-30',
      '1990-1-1',
    ]) {
      expect(birthDate(new FormControl(value))).not.toBeNull();
    }
    expect(birthDateBounds()).toEqual({ min: '1948-09-22', max: '2007-09-21' });
  });
  it('maneja los límites de febrero y cumpleaños de años bisiestos', () => {
    expect(birthDateBounds('2024-02-29')).toEqual({ min: '1946-03-01', max: '2005-02-28' });
    vi.setSystemTime(new Date('2027-02-28T12:00:00Z'));
    expect(birthDate(new FormControl('2008-02-29'))).not.toBeNull();
    vi.setSystemTime(new Date('2027-03-01T12:00:00Z'));
    expect(birthDate(new FormControl('2008-02-29'))).toBeNull();
  });
  it('utiliza la fecha de La Paz y no el día UTC del navegador', () => {
    vi.setSystemTime(new Date('2026-09-22T02:00:00Z'));
    expect(institutionalToday()).toBe('2026-09-21');
    expect(birthDate(new FormControl('2007-09-22'))).not.toBeNull();
  });
});

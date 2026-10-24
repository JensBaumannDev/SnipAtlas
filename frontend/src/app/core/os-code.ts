import { OsCode } from './entry';
import { OperatingSystem } from './preferences';

export interface ResolvedCode {
  code: string;
  os?: OperatingSystem;
}

export function resolveOsCode(code: string | OsCode, os: OperatingSystem): ResolvedCode {
  return typeof code === 'string' ? { code } : { code: code[os], os };
}

import { Service } from '@angular/core';
import { ActivatedRouteSnapshot, BaseRouteReuseStrategy } from '@angular/router';

@Service()
export class ComponentReuseStrategy extends BaseRouteReuseStrategy {
  override shouldReuseRoute(
    future: ActivatedRouteSnapshot,
    current: ActivatedRouteSnapshot,
  ): boolean {
    if (future.routeConfig === current.routeConfig) return true;
    const component = future.routeConfig?.component;
    return !!component && component === current.routeConfig?.component;
  }
}

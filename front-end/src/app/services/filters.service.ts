import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class FilterService {
  private selectedSubcategoriesSource = new BehaviorSubject<Set<number>>(
    new Set()
  );
  selectedSubcategories$ = this.selectedSubcategoriesSource.asObservable();

  private subcategoriesSource = new BehaviorSubject<Set<number>>(new Set());
  subcategories$ = this.subcategoriesSource.asObservable();

  updateSubcategories(subcategories: Set<number>): void {
    this.subcategoriesSource.next(subcategories);
  }
}

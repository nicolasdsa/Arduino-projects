import { Component, Output, EventEmitter } from '@angular/core';

@Component({
  selector: 'app-filters',
  templateUrl: './filters.component.html',
})
export class FiltersComponent {
  @Output() filterChange = new EventEmitter<string[]>();
  private activeFilters: string[] = [];

  toggleFilter(filter: string): void {
    if (this.activeFilters.includes(filter)) {
      this.activeFilters = this.activeFilters.filter((f) => f !== filter);
    } else {
      this.activeFilters.push(filter);
    }
    this.filterChange.emit(this.activeFilters);
  }
}

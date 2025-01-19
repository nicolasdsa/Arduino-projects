import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { FilterService } from 'src/app/services/filters.service';

@Component({
  selector: 'app-filters',
  templateUrl: './filters.component.html',
  styleUrls: ['./filters.component.css'],
})
export class FilterComponent implements OnInit {
  categories: any[] = [];
  selectedSubcategories: Set<number> = new Set();

  constructor(private filterService: FilterService, private http: HttpClient) {}

  ngOnInit(): void {
    this.fetchCategories();
  }

  fetchCategories(): void {
    this.http.get<any[]>('http://localhost:8000/categories').subscribe(
      (response) => {
        this.categories = response;
        this.categories.forEach((category) => {
          category.checked = true;
          category.subcategories.forEach((subcategory: any) => {
            subcategory.checked = true;
            this.selectedSubcategories.add(subcategory.id);
          });
        });
        this.filterService.updateSubcategories(this.selectedSubcategories);
      },
      (error) => console.error('Erro ao buscar categorias:', error)
    );
  }

  toggleCategory(category: any): void {
    category.checked = !category.checked;
    category.subcategories.forEach((subcategory: any) => {
      subcategory.checked = category.checked;

      if (category.checked) {
        this.selectedSubcategories.add(subcategory.id);
      } else {
        this.selectedSubcategories.delete(subcategory.id);
      }
    });
    this.filterService.updateSubcategories(this.selectedSubcategories);
  }

  toggleSubcategory(category: any, subcategory: any): void {
    subcategory.checked = !subcategory.checked;

    if (subcategory.checked) {
      this.selectedSubcategories.add(subcategory.id);
    } else {
      this.selectedSubcategories.delete(subcategory.id);
    }

    category.checked = category.subcategories.every((sub: any) => sub.checked);
    this.filterService.updateSubcategories(this.selectedSubcategories);
  }
}

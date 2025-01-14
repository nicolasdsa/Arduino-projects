import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
})
export class AppComponent {
  onFilterChange(filters: string[]): void {
    console.log('Filters changed:', filters);
    // Lógica para atualizar o mapa e gráficos com base nos filtros.
  }
}

import { Component, AfterViewInit } from '@angular/core';
import { Chart } from 'chart.js';

@Component({
  selector: 'app-charts',
  templateUrl: './charts.component.html',
})
export class ChartsComponent implements AfterViewInit {
  ngAfterViewInit(): void {
    this.createChart('chart1', 'Gráfico 1');
    this.createChart('chart2', 'Gráfico 2');
  }

  createChart(canvasId: string, label: string): void {
    new Chart(canvasId, {
      type: 'bar',
      data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr'],
        datasets: [
          {
            label: label,
            data: [10, 20, 30, 40],
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
      },
    });
  }
}

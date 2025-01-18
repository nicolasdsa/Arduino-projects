import { Component, Input, AfterViewInit } from '@angular/core';
import { Chart, ChartType, ChartOptions } from 'chart.js';

@Component({
  selector: 'app-charts',
  templateUrl: './charts.component.html',
})
export class ChartsComponent implements AfterViewInit {
  @Input() chartType: ChartType = 'bar';
  @Input() chartData: any;
  @Input() chartLabels: string[] = [];
  @Input() chartOptions: ChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
  };

  ngAfterViewInit(): void {
    if (this.chartData && this.chartLabels) {
      this.createChart('dynamicChart');
    }
  }

  createChart(canvasId: string): void {
    new Chart(canvasId, {
      type: this.chartType,
      data: {
        labels: this.chartLabels,
        datasets: this.chartData,
      },
      options: this.chartOptions,
    });
  }
}

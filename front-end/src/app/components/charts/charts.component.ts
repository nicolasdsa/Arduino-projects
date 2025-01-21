import { Component, Input, AfterViewInit } from '@angular/core';
import { Chart, ChartType, ChartOptions, registerables } from 'chart.js';
import { CrimeDataService } from 'src/app/services/crime-data.service';

@Component({
  selector: 'app-charts',
  templateUrl: './charts.component.html',
})
export class ChartsComponent implements AfterViewInit {
  loadedCrimes: any[] = [];
  private charts: { [key: string]: Chart } = {};

  constructor(private crimeDataService: CrimeDataService) {
    Chart.register(...registerables);
  }

  @Input() chartType: ChartType = 'bar';
  @Input() chartData: any;
  @Input() chartLabels: string[] = [];
  @Input() chartOptions: ChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
  };

  ngOnInit(): void {
    // Inscreva-se para reagir a mudanças nos crimes
    this.crimeDataService.crimes$.subscribe((crimes) => {
      this.loadedCrimes = crimes;
      this.updateCharts();
    });
  }

  updateCharts(): void {
    if (this.loadedCrimes && this.loadedCrimes.length > 0) {
      this.generateCategoryChart();
      this.generateTimePeriodChart();
      this.generateDailyTrendChart();
      this.generateWeekdayChart();
    } else {
      console.warn('Nenhum dado carregado para os gráficos.');
    }
  }

  ngAfterViewInit(): void {
    /*setTimeout(() => {
      this.createTestChart();
    }, 5000); // Ajuste o tempo se necessário
    */
    if (this.loadedCrimes) {
      this.generateCategoryChart();
      this.generateTimePeriodChart();
      this.generateDailyTrendChart();
      this.generateWeekdayChart();
    }
  }

  generateCategoryChart(): void {
    const categoryCounts = this.loadedCrimes.reduce((acc, crime) => {
      acc[crime.category_name] = (acc[crime.category_name] || 0) + 1;
      return acc;
    }, {});

    const labels = Object.keys(categoryCounts);
    const data = Object.values(categoryCounts);

    this.createChart(
      'categoryChart',
      labels,
      [
        {
          label: 'Número de Crimes',
          data,
          backgroundColor: 'rgba(75, 192, 192, 0.6)',
        },
      ],
      'bar'
    );
  }

  generateTimePeriodChart(): void {
    const timePeriods = { manhã: 0, tarde: 0, noite: 0, madrugada: 0 };

    this.loadedCrimes.forEach((crime) => {
      if (crime.crime_time && typeof crime.crime_time === 'string') {
        const hour = new Date(crime.crime_time).getUTCHours(); // Extrai a hora

        if (hour >= 6 && hour < 12) timePeriods.manhã++;
        else if (hour >= 12 && hour < 18) timePeriods.tarde++;
        else if (hour >= 18 && hour < 24) timePeriods.noite++;
        else timePeriods.madrugada++;
      } else {
        console.warn('Crime com crime_time inválido:', crime);
      }
    });

    const labels = Object.keys(timePeriods);
    const data = Object.values(timePeriods);

    this.createChart(
      'timePeriodChart',
      labels,
      [
        {
          label: 'Crimes por Período',
          data,
          backgroundColor: 'rgba(153, 102, 255, 0.6)',
        },
      ],
      'bar'
    );
  }

  generateDailyTrendChart(): void {
    const dailyCounts = this.loadedCrimes.reduce((acc, crime) => {
      // Verifique e limpe o campo crime_date
      if (crime.crime_date && typeof crime.crime_date === 'string') {
        const date = crime.crime_date.trim(); // Remove espaços no início e no final
        acc[date] = (acc[date] || 0) + 1;
      } else {
        console.warn('Crime com crime_date inválido:', crime);
      }
      return acc;
    }, {});

    const labels = Object.keys(dailyCounts).sort(); // Ordena as datas
    const data = labels.map((date) => dailyCounts[date]);

    this.createChart(
      'dailyTrendChart',
      labels,
      [
        {
          label: 'Crimes por Dia',
          data,
          borderColor: 'rgba(54, 162, 235, 0.8)',
          fill: false,
        },
      ],
      'line'
    );
  }

  generateWeekdayChart(): void {
    const weekdayCounts = Array(7).fill(0);
    this.loadedCrimes.forEach((crime) => {
      const weekday = new Date(crime.crime_date).getDay();
      weekdayCounts[weekday]++;
    });

    const labels = [
      'Domingo',
      'Segunda',
      'Terça',
      'Quarta',
      'Quinta',
      'Sexta',
      'Sábado',
    ];
    const data = weekdayCounts;

    this.createChart(
      'weekdayChart',
      labels,
      [
        {
          label: 'Crimes por Dia da Semana',
          data,
          backgroundColor: 'rgba(255, 159, 64, 0.6)',
        },
      ],
      'bar'
    );
  }

  createChart(
    canvasId: string,
    labels: string[],
    datasets: any[],
    chartType: string
  ): void {
    const canvas = document.getElementById(canvasId) as HTMLCanvasElement;
    if (!canvas) {
      console.error(`Canvas com id ${canvasId} não encontrado`);
      return;
    }

    // Verifique se um gráfico já existe no canvas e o destrua
    if (this.charts[canvasId]) {
      this.charts[canvasId].destroy();
    }

    // Crie um novo gráfico e registre-o
    this.charts[canvasId] = new Chart(canvas, {
      type: chartType as any,
      data: {
        labels,
        datasets,
      },
      options: {
        responsive: true,
        maintainAspectRatio: true, // Mantém a proporção
      },
    });
  }
}

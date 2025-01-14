import { Component, AfterViewInit } from '@angular/core';
import * as L from 'leaflet';

@Component({
  selector: 'app-map',
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.css'],
})
export class MapComponent implements AfterViewInit {
  private map: L.Map | undefined;

  ngAfterViewInit(): void {
    // Inicializa o mapa
    this.map = L.map('map').setView([51.505, -0.09], 13);

    // Adiciona as tiles (camada base)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(this.map);

    // Garantir que o tamanho do mapa seja ajustado
    setTimeout(() => {
      this.map?.invalidateSize();
    }, 0);

    window.addEventListener('resize', () => {
      this.map?.invalidateSize();
    });

    // Adiciona evento para capturar a movimentação
    this.map.on('moveend', this.onMapMoveEnd.bind(this));
  }

  // Função chamada quando o movimento termina
  private onMapMoveEnd(): void {
    if (!this.map) return;

    // Obtém os limites visíveis no mapa
    const bounds = this.map.getBounds();

    // Coordenadas dos cantos do mapa
    const topLeft = bounds.getNorthWest(); // Canto superior esquerdo
    const bottomRight = bounds.getSouthEast(); // Canto inferior direito

    console.log('Bounds:', {
      northWest: topLeft,
      southEast: bottomRight,
    });

    // Chama a função para carregar dados com base nos limites
    this.fetchCoordinates(bounds);
  }

  // Simula uma requisição para buscar dados
  private fetchCoordinates(bounds: L.LatLngBounds): void {
    // Extrai os limites
    const { lat: north, lng: west } = bounds.getNorthWest();
    const { lat: south, lng: east } = bounds.getSouthEast();

    // Simula uma requisição com as coordenadas visíveis
    console.log('Fazendo requisição com os limites:', {
      north,
      west,
      south,
      east,
    });

    // Aqui você faria sua requisição HTTP real
    // Por exemplo: this.http.get('api/coordinates', { params: { north, west, south, east } }).subscribe(...)
  }
}

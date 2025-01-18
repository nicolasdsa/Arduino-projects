import { Component, AfterViewInit } from '@angular/core';
import * as L from 'leaflet';
import 'leaflet.markercluster';
import { HttpClient } from '@angular/common/http';

// Corrigir os caminhos dos ícones do Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;

L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'assets/leaflet/marker-icon-2x.png',
  iconUrl: 'assets/leaflet/marker-icon.png',
  shadowUrl: 'assets/leaflet/marker-shadow.png',
});

@Component({
  selector: 'app-map',
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.css'],
})
export class MapComponent implements AfterViewInit {
  private map: L.Map | undefined;
  private markerClusterGroup = L.markerClusterGroup();

  constructor(private http: HttpClient) {}

  startDate: string = '2024-01-01';
  endDate: string = '2024-01-02';

  ngAfterViewInit(): void {
    // Inicializa o mapa
    this.map = L.map('map').setView([51.505, -0.09], 13);

    // Adiciona as tiles (camada base)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(this.map);

    // Configura o MarkerClusterGroup
    this.markerClusterGroup = L.markerClusterGroup({
      iconCreateFunction: (cluster) => {
        const count = cluster.getChildCount();

        let clusterClass = ' marker-cluster-small';
        if (count > 10 && count <= 50) {
          clusterClass = ' marker-cluster-medium';
        } else if (count > 50) {
          clusterClass = ' marker-cluster-large';
        }

        return new L.DivIcon({
          html: `<div><span>${count}</span></div>`,
          className: 'marker-cluster' + clusterClass,
          iconSize: L.point(40, 40),
        });
      },
    });

    this.map.addLayer(this.markerClusterGroup);

    // Adiciona eventos
    this.map.on('moveend', this.onMapMoveEnd.bind(this));
  }

  private onMapMoveEnd(): void {
    if (!this.map) return;

    const bounds = this.map.getBounds();
    this.fetchCoordinates(bounds);
  }

  private fetchCoordinates(bounds: L.LatLngBounds): void {
    const { lat: north, lng: west } = bounds.getNorthWest();
    const { lat: south, lng: east } = bounds.getSouthEast();

    const requestBody = {
      north,
      west,
      south,
      east,
      startDate: this.startDate,
      endDate: this.endDate,
    };

    // Faz a requisição HTTP
    this.http
      .post<any[]>('http://localhost:8000/getAll', requestBody)
      .subscribe(
        (response) => {
          this.updateMap(response);
        },
        (error) => {
          console.error('Erro ao buscar coordenadas:', error);
        }
      );
  }

  private updateMap(data: any[]): void {
    this.markerClusterGroup.clearLayers();

    data.forEach((point) => {
      const marker = L.marker([point.latitude, point.longitude]);
      this.markerClusterGroup.addLayer(marker);
    });
  }
}

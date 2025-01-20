import { Component, AfterViewInit } from '@angular/core';
import * as L from 'leaflet';
import 'leaflet.markercluster';
import { HttpClient } from '@angular/common/http';
import { debounceTime, Subject, Subscription } from 'rxjs';
import { FilterService } from 'src/app/services/filters.service';

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
  selectedSubcategories: Set<number> = new Set();
  private movementSubject = new Subject<void>(); // Controle de debounce

  constructor(private filterService: FilterService, private http: HttpClient) {
    this.movementSubject.pipe(debounceTime(300)).subscribe(() => {
      if (this.map) {
        const bounds = this.map.getBounds();
        this.fetchCoordinates(bounds);
      }
    });
    this.filterService.subcategories$.subscribe((subcategories) => {
      this.selectedSubcategories = subcategories;
      this.updateMapFilter(this.startDate, this.endDate);
    });
  }

  private map: L.Map | undefined;
  private markerClusterGroup = L.markerClusterGroup();
  private loadedCrimes = new Map<number, any>(); // Cache local de crimes

  startDate: string = '2024-01-01';
  endDate: string = '2024-01-02';

  ngAfterViewInit(): void {
    // Inicializa o mapa
    this.map = L.map('map').setView([51.505, -0.09], 13);

    // Adiciona as tiles (camada base)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(this.map);

    this.map.on('moveend', () => {
      this.movementSubject.next();
    });
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

    // Obtém os IDs das subcategorias selecionadas
    const selectedSubcategories = Array.from(this.selectedSubcategories);

    const requestBody = {
      north,
      west,
      south,
      east,
      startDate: this.startDate,
      endDate: this.endDate,
      excludedIds: Array.from(this.loadedCrimes.keys()), // Cache local
      subcategories: selectedSubcategories, // Subcategorias selecionadas
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

  public updateMap(data: any[]): void {
    if (!data) {
      this.updateMapFilter(this.startDate, this.endDate);
      return;
    }
    // 2. Processar novos pontos em lote
    const newPoints = data.filter((point) => !this.loadedCrimes.has(point.id));

    // 3. Atualizar cache em uma única operação
    newPoints.forEach((point) => {
      this.loadedCrimes.set(point.id, point);
    });

    this.updateMapFilter(this.startDate, this.endDate);
  }

  public updateMapFilter(startDate: string, endDate: string): void {
    // 1. Pré-processar as datas uma única vez
    const start = new Date(startDate).getTime();
    const end = new Date(endDate).getTime();
    const selectedSubcategoriesSet = new Set(this.selectedSubcategories);

    // 2. Criar índices temporários para otimizar buscas
    const visibleLayers = new Set();
    const layersToRemove: any[] = [];

    // 3. Processar camadas existentes com menos conversões de data
    this.markerClusterGroup.eachLayer((layer: any) => {
      const crimeTime = new Date(layer.options.crimeDate).getTime();

      if (
        !selectedSubcategoriesSet.has(layer.options.subcategory_id) ||
        crimeTime < start ||
        crimeTime > end
      ) {
        layersToRemove.push(layer);
      } else {
        visibleLayers.add(layer.options.id);
      }
    });

    // 4. Remover camadas em lote
    if (layersToRemove.length > 0) {
      this.markerClusterGroup.removeLayers(layersToRemove);
    }

    // 5. Preparar novos marcadores com menos conversões de data
    const newMarkers: L.Layer[] = [];

    this.loadedCrimes.forEach((point, id) => {
      if (!visibleLayers.has(point.id)) {
        const crimeTime = new Date(point.crime_date).getTime();

        if (
          selectedSubcategoriesSet.has(point.subcategory_id) &&
          crimeTime >= start &&
          crimeTime <= end
        ) {
          newMarkers.push(
            L.marker([point.latitude, point.longitude], {
              id: point.id,
              subcategoryId: point.subcategory_id,
              crimeDate: point.crime_date,
            } as any)
          );
        }
      }
    });

    // 6. Adicionar novos marcadores em lote
    if (newMarkers.length > 0) {
      this.markerClusterGroup.addLayers(newMarkers);
    }
  }

  onDateChange(): void {
    if (this.map) {
      const bounds = this.map.getBounds();
      this.fetchCoordinates(bounds);
    }
  }
}

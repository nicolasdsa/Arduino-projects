import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class CrimeDataService {
  private crimesSubject = new BehaviorSubject<any[]>([]);
  crimes$ = this.crimesSubject.asObservable();

  setCrimes(crimes: any[]): void {
    this.crimesSubject.next(crimes);
  }

  getCrimes(): any[] {
    return this.crimesSubject.getValue();
  }
}

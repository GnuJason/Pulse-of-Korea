"""
Population State Manager for Pulse of Korea
Maintains authoritative population data anchored to official statistics
"""

import asyncio
import json
import time
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class PopulationEvent:
    """Represents a single birth or death event"""
    country: str  # 'south_korea' or 'north_korea'
    event_type: str  # 'birth' or 'death'
    timestamp: float
    
@dataclass
class CountryData:
    """Official demographic data for a country"""
    name: str
    base_population: int
    base_year: int
    base_date: str  # ISO format when data was last updated
    annual_births: int
    annual_deaths: int
    annual_growth_rate: float  # percentage
    fertility_rate: float
    life_expectancy: float
    birth_rate: float  # per 1000
    death_rate: float  # per 1000
    data_source: str
    
    def calculate_daily_increment(self) -> float:
        """Calculate precise daily population increment based on growth rate"""
        annual_increment = self.base_population * (self.annual_growth_rate / 100)
        return annual_increment / 365.25  # Account for leap years
    
    def calculate_birth_death_rates_per_second(self):
        """Calculate births and deaths per second for real-time display"""
        births_per_second = self.annual_births / (365.25 * 24 * 60 * 60)
        deaths_per_second = self.annual_deaths / (365.25 * 24 * 60 * 60)
        return births_per_second, deaths_per_second
    
    def verify_calculations(self):
        """Verify that birth/death calculations are consistent with growth rate"""
        net_annual_change = self.annual_births - self.annual_deaths
        calculated_growth_rate = (net_annual_change / self.base_population) * 100
        return {
            "annual_births": self.annual_births,
            "annual_deaths": self.annual_deaths,
            "net_change": net_annual_change,
            "stated_growth_rate": self.annual_growth_rate,
            "calculated_growth_rate": calculated_growth_rate,
            "discrepancy": abs(self.annual_growth_rate - calculated_growth_rate)
        }

@dataclass
class PopulationState:
    """Current state of the population with all metrics"""
    timestamp: float
    south_korea_population: int
    north_korea_population: int
    total_population: int
    sk_births_today: int
    sk_deaths_today: int
    nk_births_today: int
    nk_deaths_today: int
    seconds_since_midnight_kst: int
    recent_events: List[PopulationEvent]  # Track recent birth/death events

class PopulationManager:
    """Hybrid population manager - deterministic server truth with client-side visual events"""
    
    def __init__(self):
        self.connected_clients: List = []
        self.last_update_time = time.time()
        self.broadcast_interval = 1.0  # Update every second
        self.resync_interval = 30.0  # Resync every 30 seconds (less frequent)
        self.last_resync_time = time.time()
        
        # Deterministic populations - calculated from base data
        self.sk_population = 0  # Will be calculated deterministically
        self.nk_population = 0  # Will be calculated deterministically
        
        # No server-side event tracking - events are client-side only
        self.recent_events: List[PopulationEvent] = []  # Keep for compatibility
        self.max_recent_events = 0  # Not used in hybrid mode
        
        # Daily counters (calculated deterministically)
        self.sk_births_today = 0
        self.sk_deaths_today = 0
        self.nk_births_today = 0
        self.nk_deaths_today = 0
        
        # Track when day started for daily counter reset
        self.current_day = self.get_korea_timezone_now().date()
        
        # Official demographic data (for rate calculations)
        self.south_korea_data = CountryData(
            name="South Korea",
            base_population=51628117,  # 2024 official KOSIS data
            base_year=2024,
            base_date="2024-01-01T00:00:00Z",
            annual_births=216215,  # 2024 KOSIS
            annual_deaths=325162,  # 2024 KOSIS
            annual_growth_rate=-0.21,  # 2024 KOSIS
            fertility_rate=0.748,
            life_expectancy=75.5,
            birth_rate=4.2,
            death_rate=6.3,
            data_source="KOSIS (Korean Statistical Information Service)"
        )
        
        self.north_korea_data = CountryData(
            name="North Korea",
            base_population=25971909,  # 2024 CIA World Factbook
            base_year=2024,
            base_date="2024-01-01T00:00:00Z",
            annual_births=int(25971909 * 13.2 / 1000),  # CIA estimate
            annual_deaths=int(25971909 * 9.2 / 1000),   # CIA estimate
            annual_growth_rate=0.4,  # CIA World Factbook 2024
            fertility_rate=1.9,
            life_expectancy=72.3,
            birth_rate=13.2,
            death_rate=9.2,
            data_source="CIA World Factbook 2024"
        )
        
        # Calculate event rates per second
        self.sk_births_per_sec, self.sk_deaths_per_sec = self.south_korea_data.calculate_birth_death_rates_per_second()
        self.nk_births_per_sec, self.nk_deaths_per_sec = self.north_korea_data.calculate_birth_death_rates_per_second()
        
        # Verify calculations for debugging
        self.verify_population_calculations()
        
        print(f"Hybrid Population Manager initialized:")
        print(f"Base SK population (2024-01-01): {self.south_korea_data.base_population:,}")
        print(f"Base NK population (2024-01-01): {self.north_korea_data.base_population:,}")
        print(f"Total base population: {self.south_korea_data.base_population + self.north_korea_data.base_population:,}")
        print(f"SK annual growth rate: {self.south_korea_data.annual_growth_rate:.3f}%")
        print(f"NK annual growth rate: {self.north_korea_data.annual_growth_rate:.3f}%")
        print(f"Server: Deterministic calculation | Client: Visual event simulation")
        print(f"Resync interval: {self.resync_interval}s")
    
    def get_korea_timezone_now(self) -> datetime:
        """Get current time in Korea timezone (KST/UTC+9)"""
        kst = timezone(timedelta(hours=9))
        return datetime.now(kst)
    
    def get_seconds_since_midnight_kst(self) -> int:
        """Get seconds elapsed since midnight KST today"""
        now_kst = self.get_korea_timezone_now()
        midnight_kst = now_kst.replace(hour=0, minute=0, second=0, microsecond=0)
        delta = now_kst - midnight_kst
        return int(delta.total_seconds())
    
    def get_days_since_base_date(self) -> float:
        """Calculate days elapsed since base data date"""
        now_kst = self.get_korea_timezone_now()
        base_date = datetime.fromisoformat(self.south_korea_data.base_date.replace('Z', '+00:00'))
        delta = now_kst - base_date
        return delta.total_seconds() / (24 * 60 * 60)
    
    def verify_population_calculations(self):
        """Verify all population calculations are consistent"""
        print("\n=== POPULATION CALCULATION VERIFICATION ===")
        
        # Verify South Korea
        sk_verification = self.south_korea_data.verify_calculations()
        print(f"\nSouth Korea Verification:")
        print(f"  Annual births: {sk_verification['annual_births']:,}")
        print(f"  Annual deaths: {sk_verification['annual_deaths']:,}")
        print(f"  Net change: {sk_verification['net_change']:,}")
        print(f"  Stated growth rate: {sk_verification['stated_growth_rate']:.3f}%")
        print(f"  Calculated growth rate: {sk_verification['calculated_growth_rate']:.3f}%")
        print(f"  Discrepancy: {sk_verification['discrepancy']:.3f}%")
        
        # Verify North Korea
        nk_verification = self.north_korea_data.verify_calculations()
        print(f"\nNorth Korea Verification:")
        print(f"  Annual births: {nk_verification['annual_births']:,}")
        print(f"  Annual deaths: {nk_verification['annual_deaths']:,}")
        print(f"  Net change: {nk_verification['net_change']:,}")
        print(f"  Stated growth rate: {nk_verification['stated_growth_rate']:.3f}%")
        print(f"  Calculated growth rate: {nk_verification['calculated_growth_rate']:.3f}%")
        print(f"  Discrepancy: {nk_verification['discrepancy']:.3f}%")
        
        # Verify per-second rates
        print(f"\nPer-Second Rates:")
        print(f"  SK births/sec: {self.sk_births_per_sec:.8f} ({self.sk_births_per_sec * 86400:.2f}/day)")
        print(f"  SK deaths/sec: {self.sk_deaths_per_sec:.8f} ({self.sk_deaths_per_sec * 86400:.2f}/day)")
        print(f"  NK births/sec: {self.nk_births_per_sec:.8f} ({self.nk_births_per_sec * 86400:.2f}/day)")
        print(f"  NK deaths/sec: {self.nk_deaths_per_sec:.8f} ({self.nk_deaths_per_sec * 86400:.2f}/day)")
        
        # Check if daily totals match annual rates
        sk_daily_births = self.sk_births_per_sec * 86400
        sk_annual_births_calculated = sk_daily_births * 365.25
        print(f"\nAnnual Rate Verification:")
        print(f"  SK: {self.south_korea_data.annual_births:,} stated vs {sk_annual_births_calculated:.0f} calculated")
        
        nk_daily_births = self.nk_births_per_sec * 86400
        nk_annual_births_calculated = nk_daily_births * 365.25
        print(f"  NK: {self.north_korea_data.annual_births:,} stated vs {nk_annual_births_calculated:.0f} calculated")
        
        print("=== END VERIFICATION ===\n")
    
    def calculate_current_population(self) -> PopulationState:
        """Calculate authoritative population using deterministic growth rates"""
        current_time = time.time()
        
        # Check if we need to reset daily counters (new day)
        current_date = self.get_korea_timezone_now().date()
        if current_date != self.current_day:
            print(f"New day detected! Resetting daily counters.")
            self.current_day = current_date
        
        # Calculate time elapsed since base date (2024-01-01)
        base_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        base_timestamp = base_date.timestamp()
        time_elapsed_seconds = current_time - base_timestamp
        time_elapsed_days = time_elapsed_seconds / (24 * 60 * 60)
        
        # Calculate deterministic populations using smooth growth rates
        # Formula: current_population = base_population + (annual_growth_rate * base_population * days_elapsed / 365.25)
        sk_growth_increment = (self.south_korea_data.annual_growth_rate / 100) * self.south_korea_data.base_population * (time_elapsed_days / 365.25)
        nk_growth_increment = (self.north_korea_data.annual_growth_rate / 100) * self.north_korea_data.base_population * (time_elapsed_days / 365.25)
        
        self.sk_population = int(self.south_korea_data.base_population + sk_growth_increment)
        self.nk_population = int(self.north_korea_data.base_population + nk_growth_increment)
        
        # Calculate births and deaths today based on deterministic rates
        seconds_today = self.get_seconds_since_midnight_kst()
        
        # Daily births/deaths = annual rate * fraction of day elapsed
        day_fraction = seconds_today / (24 * 60 * 60)
        self.sk_births_today = int(self.south_korea_data.annual_births * day_fraction / 365.25)
        self.sk_deaths_today = int(self.south_korea_data.annual_deaths * day_fraction / 365.25)
        self.nk_births_today = int(self.north_korea_data.annual_births * day_fraction / 365.25)
        self.nk_deaths_today = int(self.north_korea_data.annual_deaths * day_fraction / 365.25)
        
        # Update last update time
        self.last_update_time = current_time
        
        return PopulationState(
            timestamp=current_time,
            south_korea_population=self.sk_population,
            north_korea_population=self.nk_population,
            total_population=self.sk_population + self.nk_population,
            sk_births_today=self.sk_births_today,
            sk_deaths_today=self.sk_deaths_today,
            nk_births_today=self.nk_births_today,
            nk_deaths_today=self.nk_deaths_today,
            seconds_since_midnight_kst=seconds_today,
            recent_events=self.recent_events.copy()
        )
    
    def add_client(self, websocket):
        """Add a WebSocket client to receive updates"""
        self.connected_clients.append(websocket)
        print(f"Client connected. Total clients: {len(self.connected_clients)}")
    
    def remove_client(self, websocket):
        """Remove a WebSocket client"""
        if websocket in self.connected_clients:
            self.connected_clients.remove(websocket)
            print(f"Client disconnected. Total clients: {len(self.connected_clients)}")
    
    async def broadcast_update(self, state: PopulationState):
        """Broadcast authoritative population and client-side simulation parameters"""
        if not self.connected_clients:
            return
        
        current_time = state.timestamp
        is_resync_time = (current_time - self.last_resync_time) >= self.resync_interval
        
        if is_resync_time:
            self.last_resync_time = current_time
        
        # Send authoritative data with client simulation parameters
        message = {
            "timestamp": state.timestamp,
            "south_korea_population": state.south_korea_population,
            "north_korea_population": state.north_korea_population,
            "total_population": state.total_population,
            "sk_births_today": state.sk_births_today,
            "sk_deaths_today": state.sk_deaths_today,
            "nk_births_today": state.nk_births_today,
            "nk_deaths_today": state.nk_deaths_today,
            "korea_time": self.get_korea_timezone_now().strftime("%H:%M:%S"),
            "seconds_since_midnight": state.seconds_since_midnight_kst,
            "is_resync": is_resync_time,  # Signal client to resync to authoritative value
            "simulation_rates": {
                "sk_births_per_sec": self.sk_births_per_sec,
                "sk_deaths_per_sec": self.sk_deaths_per_sec,
                "nk_births_per_sec": self.nk_births_per_sec,
                "nk_deaths_per_sec": self.nk_deaths_per_sec
            },
            "event_indicators": {
                "any_birth": False,  # No server events - client will generate
                "any_death": False
            }
        }
        
        # Debug: Log broadcast data periodically
        if is_resync_time:
            print(f"Broadcasting resync data - Clients: {len(self.connected_clients)}")
            print(f"  SK Pop: {state.south_korea_population:,}, NK Pop: {state.north_korea_population:,}")
            print(f"  Simulation rates - SK births/sec: {self.sk_births_per_sec:.6f}, SK deaths/sec: {self.sk_deaths_per_sec:.6f}")
            print(f"  NK births/sec: {self.nk_births_per_sec:.6f}, NK deaths/sec: {self.nk_deaths_per_sec:.6f}")
        
        # Send to all connected clients
        disconnected_clients = []
        for client in self.connected_clients:
            try:
                await client.send_text(json.dumps(message))
            except Exception as e:
                print(f"Error sending to client: {e}")
                disconnected_clients.append(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            self.remove_client(client)
    
    async def start_broadcasting(self):
        """Start the continuous population update broadcast"""
        print("Starting population broadcast...")
        while True:
            current_state = self.calculate_current_population()
            await self.broadcast_update(current_state)
            await asyncio.sleep(self.broadcast_interval)
    
    def update_base_data(self, country: str, new_data: Dict):
        """Update base population data when new official statistics are released"""
        if country.lower() == "south_korea":
            # Update South Korea data
            self.south_korea_data.base_population = new_data.get("population", self.south_korea_data.base_population)
            self.south_korea_data.base_year = new_data.get("year", self.south_korea_data.base_year)
            self.south_korea_data.base_date = new_data.get("date", self.south_korea_data.base_date)
            self.south_korea_data.annual_births = new_data.get("births", self.south_korea_data.annual_births)
            self.south_korea_data.annual_deaths = new_data.get("deaths", self.south_korea_data.annual_deaths)
            self.south_korea_data.annual_growth_rate = new_data.get("growth_rate", self.south_korea_data.annual_growth_rate)
            
            # Recalculate increments
            self.sk_daily_increment = self.south_korea_data.calculate_daily_increment()
            self.sk_births_per_sec, self.sk_deaths_per_sec = self.south_korea_data.calculate_birth_death_rates_per_second()
            
        elif country.lower() == "north_korea":
            # Update North Korea data
            self.north_korea_data.base_population = new_data.get("population", self.north_korea_data.base_population)
            self.north_korea_data.base_year = new_data.get("year", self.north_korea_data.base_year)
            self.north_korea_data.base_date = new_data.get("date", self.north_korea_data.base_date)
            self.north_korea_data.annual_births = new_data.get("births", self.north_korea_data.annual_births)
            self.north_korea_data.annual_deaths = new_data.get("deaths", self.north_korea_data.annual_deaths)
            self.north_korea_data.annual_growth_rate = new_data.get("growth_rate", self.north_korea_data.annual_growth_rate)
            
            # Recalculate increments
            self.nk_daily_increment = self.north_korea_data.calculate_daily_increment()
            self.nk_births_per_sec, self.nk_deaths_per_sec = self.north_korea_data.calculate_birth_death_rates_per_second()
        
        print(f"Updated {country} base data. New increments calculated.")
    
    def get_static_data(self) -> Dict:
        """Get static demographic data for initial page load"""
        return {
            "south_korea": asdict(self.south_korea_data),
            "north_korea": asdict(self.north_korea_data),
            "last_updated": self.get_korea_timezone_now().isoformat()
        }

# Global population manager instance
population_manager = PopulationManager()
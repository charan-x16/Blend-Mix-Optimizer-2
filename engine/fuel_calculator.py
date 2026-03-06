"""
Fuel Slag Calculator — Computes slag contribution from coke, nut coke, and PCI.

Formula per fuel:
    ash_qty_MT   = fuel_qty_MT × (ash_pct / 100)
    slag_MT      = ash_qty_MT  × (SiO2 + Al2O3 + CaO + MgO)_ash / 100

Total fuel slag = coke_slag + nut_coke_slag + pci_slag
This is added to ore blend slag to get total BF slag burden.
"""

from dataclasses import dataclass
from config.config import cfg


@dataclass
class FuelInput:
    coke_qty_mt:     float
    coke_ash_pct:    float
    nut_coke_qty_mt: float
    nut_coke_ash_pct: float
    pci_qty_mt:      float
    pci_ash_pct:     float


@dataclass
class FuelSlagResult:
    # Coke
    coke_ash_qty_mt:     float
    coke_slag_mt:        float
    # Nut Coke
    nut_coke_ash_qty_mt: float
    nut_coke_slag_mt:    float
    # PCI
    pci_ash_qty_mt:      float
    pci_slag_mt:         float
    # Total
    total_fuel_slag_mt:  float


def _slag_factor(ash_analysis: dict) -> float:
    """Sum of slag-forming oxides in ash (SiO2 + Al2O3 + CaO + MgO) as fraction."""
    return (
        ash_analysis.get("SiO2",  0.0) +
        ash_analysis.get("Al2O3", 0.0) +
        ash_analysis.get("CaO",   0.0) +
        ash_analysis.get("MgO",   0.0) +
        ash_analysis.get("MnO",   0.0)    # Include MnO as slag-former based on config
    ) / 100.0


def calculate_fuel_slag(fuel: FuelInput) -> FuelSlagResult:
    """Calculate slag contribution from all three fuels."""

    # Coke
    coke_ash_qty      = fuel.coke_qty_mt * (fuel.coke_ash_pct / 100.0)
    coke_slag         = coke_ash_qty * _slag_factor(cfg.coke_ash_analysis)

    # Nut Coke
    nut_coke_ash_qty  = fuel.nut_coke_qty_mt * (fuel.nut_coke_ash_pct / 100.0)
    nut_coke_slag     = nut_coke_ash_qty * _slag_factor(cfg.nut_coke_ash_analysis)

    # PCI
    pci_ash_qty       = fuel.pci_qty_mt * (fuel.pci_ash_pct / 100.0)
    pci_slag          = pci_ash_qty * _slag_factor(cfg.pci_ash_analysis)

    total = coke_slag + nut_coke_slag + pci_slag

    return FuelSlagResult(
        coke_ash_qty_mt     = round(coke_ash_qty,     2),
        coke_slag_mt        = round(coke_slag,        2),
        nut_coke_ash_qty_mt = round(nut_coke_ash_qty, 2),
        nut_coke_slag_mt    = round(nut_coke_slag,    2),
        pci_ash_qty_mt      = round(pci_ash_qty,      2),
        pci_slag_mt         = round(pci_slag,         2),
        total_fuel_slag_mt  = round(total,            2),
    )
# **DirSpec**
## NDBC 2D-spectral density data viewer using first two harmonics of truncated Fourier series.

## Features
1. **Interactive selection** of buoy, timestamp, and frequency band
2. **Frequency Spectrum Plot** allows interactive selection of frequency bands
3. **Polar plot** of directional wave energy distribution

## Data Pipeline
1. Ingests NOAA buoy data from the NDBC api (energy density, r₁, r₂, α₁, α₂, general buoy data)
2. Cleans and organizes data
3. Computes mo, Hm0, m_1, and Te - stores to buoy in database for future use
4. Computes Fourier-based direction distributions for each frequency bin
5. Stores outputs in a relation database schema:
   - spectra_parameters: per frequency wave characteristics (Ef, α₁, α₂, r₁, r₂)
   - spectra_directional: directional spreading distributions
  
## Future Goals
- Increase the number of available buoys
- Enhance UI/UX of the dashboard to give user more freedom in analysis
- Train a ML model to generate idealized directional distributions for comparison to Fourier-based plots
- Deploy dashboard online

## Preview of work in progess

![image](https://github.com/user-attachments/assets/dbbc5778-b7cd-47e4-a930-44d3f8bddcee)

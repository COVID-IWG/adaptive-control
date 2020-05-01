from typing import Dict, Iterator, Optional, Sequence, Union

import numpy as np

class ModelUnit():
    def __init__(self, 
        name:              str,             # name of unit
        population:        int,             # unit population
        I0:       Optional[int]  = None,    # initial infected, None -> Poisson random intro 
        R0:                int   = 0,       # initial recovered
        D0:                int   = 0,       # initial dead
        infectious_period: int   = 5,       # how long disease is communicable in days 
        introduction_rate: float = 5.0,     # parameter for new community transmissions (lambda) 
        mortality:         float = 0.02,    # I -> D transition probability 
        mobility:          float = 0.0001, # percentage of total population migrating out at each timestep 
        RR0:               float = 1.9):    # initial reproductive rate 
        
        # save params 
        self.name  = name 
        self.pop0  = population
        self.gamma = 1.0/infectious_period
        self.ll    = introduction_rate
        self.m     = mortality
        self.mu    = mobility
        self.RR0   = RR0
        
        # state and delta vectors 
        if I0 is None:
            I0 = np.random.poisson(self.ll) # initial number of cases 
        self.RR = [RR0]
        self.b  = [np.exp(self.gamma * (RR0 - 1.0))]
        self.S  = [population]
        self.I  = [I0] 
        self.R  = [R0]
        self.D  = [D0]
        self.P  = [population - I0 - R0 - D0] # total population = S + I + R 
        self.beta = [RR0/self.gamma] # initial contact rate 
        self.delta_T     = [I0] # case change rate, initialized with the first introduction, if any
        self.total_cases = [I0] # total cases 
        # self.delta_D = [0]
        # self.delta_R = [0]

    # period 1: inter-state migratory transmission
    def migration_step(self) -> int:
        # note: update state *in place* since we consider it the same time period 
        outflux = np.random.poisson(self.mu * self.I[-1])
        new_I = self.I[-1] - outflux
        if new_I < 0: new_i = 0
        self.I[-1]  = new_I
        self.P[-1] -= outflux
        return outflux

    # period 2: intra-state community transmission
    def forward_epi_step(self, delta_B: int): 
        # get previous state 
        S, I, R, D, P = (vector[-1] for vector in (self.S, self.I, self.R, self.D, self.P))

        # update state 
        RR = self.RR0 * float(S)/float(P)
        b  = np.exp(self.gamma * (RR - 1))

        rate_T    = (delta_B + b * (self.delta_T[-1] - delta_B) + self.gamma * RR * delta_B)
        num_cases = np.random.poisson(max(0, rate_T))

        I += num_cases
        S -= num_cases

        rate_D    = self.m * self.gamma * I
        num_dead  = np.random.poisson(rate_D)
        D        += num_dead

        rate_R    = (1 - self.m) * self.gamma * I 
        num_recov = np.random.poisson(rate_R)
        R        += num_recov

        I -= (num_dead + num_recov)
        
        if S < 0: S = 0
        if I < 0: I = 0
        if D < 0: D = 0

        P = S + I + R
        beta = (num_cases * P)/(b * S * I)

        # update state vectors 
        self.RR.append(RR)
        self.b.append(b)
        self.S.append(S)
        self.I.append(I)
        self.R.append(R)
        self.D.append(D)
        self.P.append(P)
        self.beta.append(beta)
        self.delta_T.append(num_cases)
        self.total_cases.append(I + R + D)

    def __repr__(self) -> str:
        return f"ModelUnit[{self.name}]"

class Model():
    def __init__(self, units: Sequence[ModelUnit], default_migrations: Optional[np.matrix] = None, random_seed : Optional[int] = None):
        self.units      = units
        self.migrations = default_migrations
        self.names      = {unit.name: unit for unit in units}
        if random_seed:
            np.random.seed(random_seed)

    def tick(self, migrations: np.matrix):
        # run migration step 
        outflux       = [unit.migration_step() for unit in self.units]
        transmissions = [flux * self.migrations[i, :].sum() for (i, flux) in enumerate(outflux)]
        
        # now run forward epidemiological model 
        for (unit, tmx) in zip(self.units, transmissions):
            unit.forward_epi_step(tmx)

    def run(self, days: int, migrations: Optional[np.matrix] = None):
        if not migrations:
            migrations = self.migrations
        for _ in range(days):
            self.tick(migrations)
        return self 

    def __iter__(self) -> Iterator[ModelUnit]:
        return iter(self.units)

    # index units
    def __getitem__(self, idx: Union[str, int]) -> ModelUnit:
        if isinstance(idx, int):
            return self.units[idx]
        return self.names[idx]

    def set_parameters(self, **kwargs):
        for (attr, val) in kwargs.items():
            if callable(val):
                if val.__code__.co_argcount == 1:
                    for unit in self.units:
                        unit.__setattr__(attr, val(unit))
                else: 
                    for (i, unit) in enumerate(self.units):
                        unit.__setattr__(attr, val(i, unit))
            elif isinstance(val, dict):
                for unit in self.units:
                    unit.__setattr__(attr, val[unit.name])
            else: 
                for unit in self.units:
                    unit.__setattr__(attr, val)
        return self 

    def aggregate(self, curves: Union[Sequence[str], str] = ["RR", "b", "S", "I", "R", "D", "P", "beta"]) -> Union[Dict[str, Sequence[float]], Sequence[float]]:
        if isinstance(curves, str):
            single_curve = curves
            curves = [curves]
        else: 
            single_curve = False
        aggs = { 
            curve: list(map(sum, zip(*(unit.__getattribute__(curve) for unit in self.units))))
            for curve in curves
        }

        if single_curve:
            return aggs[single_curve]
        return aggs